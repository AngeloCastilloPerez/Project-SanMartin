# Fabric Notebook: nb_landing_sap_equipos
# Description: SAP SOAP ingestion (ZWS_GET_EQUIPOS) → landing layer
# Architecture: Landing (raw JSON) → OneLake / ADLS Gen2

# ---------------------------------------------------------------------------
# Parameters (injected via mssparkutils.notebook.run or Fabric widget)
# ---------------------------------------------------------------------------
storage_account = ""   # e.g. "onelake" or ADLS account name
environment = ""       # "dev" | "qa" | "prod"
execution_id = ""      # unique run id (GUID or timestamp string)

try:
    storage_account = getArgument("storage_account")
    environment = getArgument("environment")
    execution_id = getArgument("execution_id")
except Exception:
    # Default values for interactive / local runs
    storage_account = storage_account or "onelakesanmartin"
    environment = environment or "dev"
    execution_id = execution_id or "manual"

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import json
import traceback
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit

# SAP integration helper (bundled as a Fabric attached library or notebook util)
import sys
sys.path.insert(0, "/lakehouse/default/Files/libs")
from sap_client import SapSoapClient  # noqa: E402

spark = SparkSession.builder.getOrCreate()

# ---------------------------------------------------------------------------
# Path config — Medallion architecture
# ---------------------------------------------------------------------------
CONTAINER_LANDING = f"abfss://landing@{storage_account}.dfs.fabric.microsoft.com"
CONTAINER_LOGS    = f"abfss://logs@{storage_account}.dfs.fabric.microsoft.com"

LANDING_PATH = f"{CONTAINER_LANDING}/{environment}/sap/equipos/"
LOG_PATH     = f"{CONTAINER_LOGS}/{environment}/nb_landing_sap_equipos/"

# ---------------------------------------------------------------------------
# SAP SOAP call
# ---------------------------------------------------------------------------
start_ts = datetime.now(timezone.utc)
status = "SUCCESS"
error_msg = ""
rows_written = 0

try:
    client = SapSoapClient()
    raw_data = client.get_equipos()          # returns list[dict]

    df_raw = spark.createDataFrame(raw_data)
    rows_written = df_raw.count()

    # Write raw JSON-style Parquet to landing
    (
        df_raw
        .write
        .mode("overwrite")
        .parquet(f"{LANDING_PATH}execution_id={execution_id}/")
    )

except Exception as exc:
    status = "ERROR"
    error_msg = traceback.format_exc()
    raise

finally:
    # -----------------------------------------------------------------------
    # Execution log
    # -----------------------------------------------------------------------
    end_ts = datetime.now(timezone.utc)
    duration_s = (end_ts - start_ts).total_seconds()

    log_record = [{
        "notebook":      "nb_landing_sap_equipos",
        "execution_id":  execution_id,
        "environment":   environment,
        "start_ts":      start_ts.isoformat(),
        "end_ts":        end_ts.isoformat(),
        "duration_s":    duration_s,
        "rows_written":  rows_written,
        "status":        status,
        "error_msg":     error_msg,
    }]

    df_log = spark.createDataFrame(log_record)
    (
        df_log
        .write
        .mode("append")
        .parquet(f"{LOG_PATH}date={start_ts.strftime('%Y-%m-%d')}/")
    )

print(f"[nb_landing_sap_equipos] status={status} rows={rows_written} duration={duration_s:.1f}s")
