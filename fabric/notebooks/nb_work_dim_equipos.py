# Fabric Notebook: nb_work_dim_equipos
# Description: Clean + normalize dim_equipos (hybrid: SAP + master tables)
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
from pyspark.sql.types import StringType

spark = SparkSession.builder.getOrCreate()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SA = storage_account
ENV = environment

LANDING_EQUIPOS     = f"abfss://landing@{SA}.dfs.fabric.microsoft.com/{ENV}/sap/equipos/"
MASTER_BASE         = f"abfss://landing@{SA}.dfs.fabric.microsoft.com/master_tables/"
WORK_DIM_EQUIPOS    = f"abfss://work@{SA}.dfs.fabric.microsoft.com/{ENV}/dim_equipos/"
CONTAINER_LOGS      = f"abfss://logs@{SA}.dfs.fabric.microsoft.com"
LOG_PATH            = f"{CONTAINER_LOGS}/{ENV}/nb_work_dim_equipos/"

# ---------------------------------------------------------------------------
# Helper: normalize text (remove accents, uppercase, trim)
# ---------------------------------------------------------------------------
def _normalize_str(s: str) -> str:
    if s is None:
        return None
    nfkd = unicodedata.normalize("NFKD", s)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    return ascii_str.strip().upper()

normalize_udf = F.udf(_normalize_str, StringType())

# ---------------------------------------------------------------------------
# ETL
# ---------------------------------------------------------------------------
start_ts = datetime.now(timezone.utc)
status = "SUCCESS"
error_msg = ""
rows_written = 0

try:
    # 1. Read latest landing snapshot
    df_sap = (
        spark.read.parquet(LANDING_EQUIPOS)
        .orderBy(F.col("execution_id").desc())
        .limit(1000000)   # safety cap; remove if needed
    )

    # Normalize key fields from SAP
    str_cols = [c for c, t in df_sap.dtypes if t == "string"]
    for col in str_cols:
        df_sap = df_sap.withColumn(col, normalize_udf(F.col(col)))

    # 2. Read master tables (CSV seed files)
    df_contratista = spark.read.option("header", True).csv(
        f"{MASTER_BASE}map_equipo_contratista.csv"
    )
    df_tipo_flota = spark.read.option("header", True).csv(
        f"{MASTER_BASE}map_codigo_tipo_flota.csv"
    )
    df_niveles = spark.read.option("header", True).csv(
        f"{MASTER_BASE}map_equipo_niveles.csv"
    )

    # 3. Enrich: EMPRESA_CONTRATISTA
    df_work = df_sap.join(
        df_contratista.select("EQUIPO_ID", "EMPRESA_CONTRATISTA"),
        on="EQUIPO_ID",
        how="left",
    )

    # 4. Enrich: TIPO_DE_FLOTA (prefix-based rules applied via master table)
    #    map_codigo_tipo_flota.csv should contain columns: PREFIX, TIPO_DE_FLOTA
    #    Example: C- → CARGUIO, V- → ACARREO, RE- → CARGUIO, P- → PERFORACION
    df_work = df_work.join(
        df_tipo_flota.select("EQUIPO_ID", "TIPO_DE_FLOTA"),
        on="EQUIPO_ID",
        how="left",
    )

    # 5. Enrich: NIVEL_I / NIVEL_II / NIVEL_III
    df_work = df_work.join(
        df_niveles.select("EQUIPO_ID", "NIVEL_I", "NIVEL_II", "NIVEL_III"),
        on="EQUIPO_ID",
        how="left",
    )

    # 6. Normalize enriched string columns
    for col in ["EMPRESA_CONTRATISTA", "TIPO_DE_FLOTA", "NIVEL_I", "NIVEL_II", "NIVEL_III"]:
        if col in df_work.columns:
            df_work = df_work.withColumn(col, normalize_udf(F.col(col)))

    # 7. Add metadata columns
    df_work = df_work.withColumn("execution_id", F.lit(execution_id))
    df_work = df_work.withColumn("load_ts", F.current_timestamp())

    rows_written = df_work.count()

    # 8. ACID-safe write — truncate/insert pattern
    (
        df_work
        .write
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .parquet(WORK_DIM_EQUIPOS)
    )

except Exception as exc:
    status = "ERROR"
    error_msg = traceback.format_exc()
    raise

finally:
    end_ts = datetime.now(timezone.utc)
    duration_s = (end_ts - start_ts).total_seconds()

    log_record = [{
        "notebook":      "nb_work_dim_equipos",
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

print(f"[nb_work_dim_equipos] status={status} rows={rows_written} duration={duration_s:.1f}s")
