# Fabric Notebook: nb_work_fact_rdp
# Description: Transform fact_rdp with KPI columns
#              KPIs: V/HR (Viajes/Hora), MTS/HRS, TN*DIST, TN/VJ
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
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType

spark = SparkSession.builder.getOrCreate()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SA  = storage_account
ENV = environment

LANDING_RDP     = f"abfss://landing@{SA}.dfs.fabric.microsoft.com/{ENV}/sharepoint/"
WORK_FACT_RDP   = f"abfss://work@{SA}.dfs.fabric.microsoft.com/{ENV}/fact_rdp/"
CONTAINER_LOGS  = f"abfss://logs@{SA}.dfs.fabric.microsoft.com"
LOG_PATH        = f"{CONTAINER_LOGS}/{ENV}/nb_work_fact_rdp/"

# ---------------------------------------------------------------------------
# ETL
# ---------------------------------------------------------------------------
start_ts = datetime.now(timezone.utc)
status = "SUCCESS"
error_msg = ""
rows_written = 0

try:
    # 1. Read raw RDP data from landing
    df_raw = spark.read.parquet(f"{LANDING_RDP}RDP*/")

    # 2. Cast numeric columns (landing stores everything as string)
    numeric_cols = ["HM", "VIAJES", "METROS", "TONELAJE", "DISTANCIA", "HORAS"]
    for col in numeric_cols:
        if col in df_raw.columns:
            df_raw = df_raw.withColumn(col, F.col(col).cast(DoubleType()))

    # 3. Compute KPI columns
    # V/HR: Viajes por Hora de Movimiento
    df_work = df_raw.withColumn(
        "V_HR",
        F.when(F.col("HM") > 0, F.col("VIAJES") / F.col("HM")).otherwise(None)
    )

    # MTS/HRS: Metros perforados por Hora
    df_work = df_work.withColumn(
        "MTS_HRS",
        F.when(F.col("HORAS") > 0, F.col("METROS") / F.col("HORAS")).otherwise(None)
    )

    # TN*DIST: Tonelaje × Distancia (tkm indicator)
    df_work = df_work.withColumn(
        "TN_DIST",
        F.col("TONELAJE") * F.col("DISTANCIA")
    )

    # TN/VJ: Tonelaje por Viaje
    df_work = df_work.withColumn(
        "TN_VJ",
        F.when(F.col("VIAJES") > 0, F.col("TONELAJE") / F.col("VIAJES")).otherwise(None)
    )

    # 4. Add metadata
    df_work = df_work.withColumn("execution_id", F.lit(execution_id))
    df_work = df_work.withColumn("load_ts", F.current_timestamp())

    rows_written = df_work.count()

    # 5. ACID-safe write — truncate/insert
    (
        df_work
        .write
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .parquet(WORK_FACT_RDP)
    )

except Exception as exc:
    status = "ERROR"
    error_msg = traceback.format_exc()
    raise

finally:
    end_ts = datetime.now(timezone.utc)
    duration_s = (end_ts - start_ts).total_seconds()

    log_record = [{
        "notebook":      "nb_work_fact_rdp",
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

print(f"[nb_work_fact_rdp] status={status} rows={rows_written} duration={duration_s:.1f}s")
