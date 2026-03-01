# Fabric Notebook: nb_landing_sap_costos
# Description: SAP SOAP ingestion (ZWS_GET_KOB1 — Costos Equipos) → landing layer
# Architecture: Landing (raw Parquet) → OneLake / ADLS Gen2

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
storage_account = ""
environment = ""
execution_id = ""
fecha_inicio = ""   # "YYYYMMDD" — filter for SAP query
fecha_fin = ""      # "YYYYMMDD" — filter for SAP query

try:
    storage_account = getArgument("storage_account")
    environment     = getArgument("environment")
    execution_id    = getArgument("execution_id")
    fecha_inicio    = getArgument("fecha_inicio")
    fecha_fin       = getArgument("fecha_fin")
except Exception:
    storage_account = storage_account or "onelakesanmartin"
    environment     = environment or "dev"
    execution_id    = execution_id or "manual"
    fecha_inicio    = fecha_inicio or "20240101"
    fecha_fin       = fecha_fin or "20241231"

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import traceback
from datetime import datetime, timezone

from pyspark.sql import SparkSession

import sys
sys.path.insert(0, "/lakehouse/default/Files/libs")
from sap_client import SapSoapClient  # noqa: E402

spark = SparkSession.builder.getOrCreate()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CONTAINER_LANDING = f"abfss://landing@{storage_account}.dfs.fabric.microsoft.com"
CONTAINER_LOGS    = f"abfss://logs@{storage_account}.dfs.fabric.microsoft.com"

LANDING_PATH = f"{CONTAINER_LANDING}/{environment}/sap/costos/"
LOG_PATH     = f"{CONTAINER_LOGS}/{environment}/nb_landing_sap_costos/"

# ---------------------------------------------------------------------------
# SAP SOAP call — ZWS_GET_KOB1
# ---------------------------------------------------------------------------
start_ts = datetime.now(timezone.utc)
status = "SUCCESS"
error_msg = ""
rows_written = 0

try:
    client = SapSoapClient()
    raw_data = client.get_costos_equipos(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

    df_raw = spark.createDataFrame(raw_data)
    rows_written = df_raw.count()

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
    end_ts = datetime.now(timezone.utc)
    duration_s = (end_ts - start_ts).total_seconds()

    log_record = [{
        "notebook":      "nb_landing_sap_costos",
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

print(f"[nb_landing_sap_costos] status={status} rows={rows_written} duration={duration_s:.1f}s")
