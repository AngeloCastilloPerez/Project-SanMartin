# Fabric Notebook: nb_work_costos_totales
# Description: Clean Costos_Totales and link to dim_equipos
# Architecture: Landing → Work (Parquet, truncate/insert)

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
import unicodedata
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, DateType, StringType

spark = SparkSession.builder.getOrCreate()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SA  = storage_account
ENV = environment

LANDING_COSTOS       = f"abfss://landing@{SA}.dfs.fabric.microsoft.com/{ENV}/sap/costos/"
WORK_DIM_EQUIPOS     = f"abfss://work@{SA}.dfs.fabric.microsoft.com/{ENV}/dim_equipos/"
WORK_COSTOS_TOTALES  = f"abfss://work@{SA}.dfs.fabric.microsoft.com/{ENV}/costos_totales/"
CONTAINER_LOGS       = f"abfss://logs@{SA}.dfs.fabric.microsoft.com"
LOG_PATH             = f"{CONTAINER_LOGS}/{ENV}/nb_work_costos_totales/"

# ---------------------------------------------------------------------------
# Normalization helper
# ---------------------------------------------------------------------------
def _normalize_str(s):
    if s is None:
        return None
    nfkd = unicodedata.normalize("NFKD", s)
    return nfkd.encode("ascii", "ignore").decode("ascii").strip().upper()

normalize_udf = F.udf(_normalize_str, StringType())

# ---------------------------------------------------------------------------
# ETL
# ---------------------------------------------------------------------------
start_ts = datetime.now(timezone.utc)
status = "SUCCESS"
error_msg = ""
rows_written = 0

try:
    # 1. Read raw costos from landing
    df_raw = spark.read.parquet(LANDING_COSTOS)

    # 2. Cast types
    df_costos = (
        df_raw
        .withColumn("MONTO",    F.col("MONTO").cast(DoubleType()))
        .withColumn("CANTIDAD", F.col("CANTIDAD").cast(DoubleType()))
        .withColumn("FECHA",    F.to_date(F.col("FECHA"), "yyyyMMdd"))
    )

    # 3. Normalize text fields
    for col in ["TIPO_COSTO", "CENTRO_COSTO", "DESCRIPCION", "EQUIPO_ID"]:
        if col in df_costos.columns:
            df_costos = df_costos.withColumn(col, normalize_udf(F.col(col)))

    # 4. Deduplicate (keep latest by execution_id)
    df_costos = df_costos.dropDuplicates(["EQUIPO_ID", "FECHA", "TIPO_COSTO", "CENTRO_COSTO"])

    # 5. Join dim_equipos for enrichment
    df_dim = spark.read.parquet(WORK_DIM_EQUIPOS).select(
        "EQUIPO_ID", "EMPRESA_CONTRATISTA", "TIPO_DE_FLOTA", "NIVEL_I", "NIVEL_II"
    )

    df_work = df_costos.join(df_dim, on="EQUIPO_ID", how="left")

    # 6. Add metadata
    df_work = df_work.withColumn("execution_id", F.lit(execution_id))
    df_work = df_work.withColumn("load_ts", F.current_timestamp())

    rows_written = df_work.count()

    # 7. ACID-safe write
    (
        df_work
        .write
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .parquet(WORK_COSTOS_TOTALES)
    )

except Exception as exc:
    status = "ERROR"
    error_msg = traceback.format_exc()
    raise

finally:
    end_ts = datetime.now(timezone.utc)
    duration_s = (end_ts - start_ts).total_seconds()

    log_record = [{
        "notebook":      "nb_work_costos_totales",
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

print(f"[nb_work_costos_totales] status={status} rows={rows_written} duration={duration_s:.1f}s")
