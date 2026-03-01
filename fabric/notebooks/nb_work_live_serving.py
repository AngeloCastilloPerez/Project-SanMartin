# Fabric Notebook: nb_work_live_serving
# Description: Final serving layer — merge Work tables into Work Live (Delta / Parquet)
# Architecture: Work → Work Live (merge / upsert pattern)

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
storage_account = ""
environment = ""
execution_id = ""

try:
    storage_account = getArgument("storage_account")
    environment     = getArgument("environment")
    execution_id    = getArgument("execution_id")
except Exception:
    storage_account = storage_account or "onelakesanmartin"
    environment     = environment or "dev"
    execution_id    = execution_id or "manual"

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import traceback
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from delta.tables import DeltaTable  # available in Fabric runtime

spark = SparkSession.builder \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SA  = storage_account
ENV = environment

WORK_BASE         = f"abfss://work@{SA}.dfs.fabric.microsoft.com/{ENV}"
WORK_LIVE_BASE    = f"abfss://work_live@{SA}.dfs.fabric.microsoft.com/{ENV}"
CONTAINER_LOGS    = f"abfss://logs@{SA}.dfs.fabric.microsoft.com"
LOG_PATH          = f"{CONTAINER_LOGS}/{ENV}/nb_work_live_serving/"

TABLES = [
    {
        "name":       "dim_equipos",
        "source":     f"{WORK_BASE}/dim_equipos/",
        "target":     f"{WORK_LIVE_BASE}/dim_equipos/",
        "merge_key":  "EQUIPO_ID",
    },
    {
        "name":       "fact_rdp",
        "source":     f"{WORK_BASE}/fact_rdp/",
        "target":     f"{WORK_LIVE_BASE}/fact_rdp/",
        "merge_key":  "RDP_ID",
    },
    {
        "name":       "costos_totales",
        "source":     f"{WORK_BASE}/costos_totales/",
        "target":     f"{WORK_LIVE_BASE}/costos_totales/",
        "merge_key":  None,   # use full overwrite for cost table
    },
]

# ---------------------------------------------------------------------------
# Serving merge
# ---------------------------------------------------------------------------
start_ts = datetime.now(timezone.utc)
status = "SUCCESS"
error_msg = ""
rows_written = 0

def upsert_delta(source_path: str, target_path: str, merge_key: str):
    """Merge source Parquet into Delta target table."""
    df_source = spark.read.parquet(source_path)

    if DeltaTable.isDeltaTable(spark, target_path):
        dt = DeltaTable.forPath(spark, target_path)
        (
            dt.alias("target")
            .merge(
                df_source.alias("source"),
                f"target.{merge_key} = source.{merge_key}"
            )
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute()
        )
    else:
        # First load — write as Delta
        (
            df_source
            .write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .save(target_path)
        )
    return df_source.count()

def overwrite_delta(source_path: str, target_path: str):
    """Full overwrite for tables with no natural merge key."""
    df_source = spark.read.parquet(source_path)
    (
        df_source
        .write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .save(target_path)
    )
    return df_source.count()

try:
    for tbl in TABLES:
        if tbl["merge_key"]:
            cnt = upsert_delta(tbl["source"], tbl["target"], tbl["merge_key"])
        else:
            cnt = overwrite_delta(tbl["source"], tbl["target"])
        rows_written += cnt
        print(f"  [{tbl['name']}] rows={cnt}")

except Exception as exc:
    status = "ERROR"
    error_msg = traceback.format_exc()
    raise

finally:
    end_ts = datetime.now(timezone.utc)
    duration_s = (end_ts - start_ts).total_seconds()

    log_record = [{
        "notebook":      "nb_work_live_serving",
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

print(f"[nb_work_live_serving] status={status} total_rows={rows_written} duration={duration_s:.1f}s")
