# Fabric Notebook: nb_landing_sharepoint
# Description: Excel / CSV ingestion from SharePoint Online → landing layer
# Architecture: Landing (raw Parquet) → OneLake / ADLS Gen2

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
storage_account   = ""
environment       = ""
execution_id      = ""
sharepoint_site   = ""   # e.g. "https://contoso.sharepoint.com/sites/sanmartin"
sharepoint_folder = ""   # relative folder path inside the document library
file_pattern      = ""   # glob, e.g. "RDP*.xlsx"

try:
    storage_account   = getArgument("storage_account")
    environment       = getArgument("environment")
    execution_id      = getArgument("execution_id")
    sharepoint_site   = getArgument("sharepoint_site")
    sharepoint_folder = getArgument("sharepoint_folder")
    file_pattern      = getArgument("file_pattern")
except Exception:
    storage_account   = storage_account or "onelakesanmartin"
    environment       = environment or "dev"
    execution_id      = execution_id or "manual"
    sharepoint_site   = sharepoint_site or "https://contoso.sharepoint.com/sites/sanmartin"
    sharepoint_folder = sharepoint_folder or "Documentos/Operaciones"
    file_pattern      = file_pattern or "*.xlsx"

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import io
import fnmatch
import traceback
from datetime import datetime, timezone

import pandas as pd
import requests
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CONTAINER_LANDING = f"abfss://landing@{storage_account}.dfs.fabric.microsoft.com"
CONTAINER_LOGS    = f"abfss://logs@{storage_account}.dfs.fabric.microsoft.com"

LANDING_PATH = f"{CONTAINER_LANDING}/{environment}/sharepoint/"
LOG_PATH     = f"{CONTAINER_LOGS}/{environment}/nb_landing_sharepoint/"

# ---------------------------------------------------------------------------
# SharePoint helper — uses service principal token via mssparkutils
# ---------------------------------------------------------------------------
def get_sp_token(site: str) -> str:
    """Obtain SharePoint access token via mssparkutils credentials."""
    credential = mssparkutils.credentials.getToken("https://graph.microsoft.com/.default")  # type: ignore[name-defined]
    return credential

def list_sharepoint_files(site: str, folder: str, token: str, pattern: str) -> list:
    """Return list of {name, download_url} matching pattern from SharePoint folder."""
    # Graph API: /sites/{site-id}/drive/root:/{folder}:/children
    site_host = site.split("/sites/")[0].replace("https://", "")
    site_path = "/sites/" + site.split("/sites/")[1]
    graph_url = (
        f"https://graph.microsoft.com/v1.0/sites/{site_host}:{site_path}"
        f":/drive/root:/{folder}:/children"
    )
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(graph_url, headers=headers, timeout=30)
    resp.raise_for_status()
    items = resp.json().get("value", [])
    return [
        {"name": i["name"], "download_url": i["@microsoft.graph.downloadUrl"]}
        for i in items
        if fnmatch.fnmatch(i["name"], pattern)
    ]

# ---------------------------------------------------------------------------
# Ingestion loop
# ---------------------------------------------------------------------------
start_ts = datetime.now(timezone.utc)
status = "SUCCESS"
error_msg = ""
rows_written = 0

try:
    token = get_sp_token(sharepoint_site)
    files = list_sharepoint_files(sharepoint_site, sharepoint_folder, token, file_pattern)

    for file_info in files:
        file_name = file_info["name"]
        download_url = file_info["download_url"]

        response = requests.get(download_url, timeout=60)
        response.raise_for_status()
        content = response.content

        if file_name.endswith(".csv"):
            pdf = pd.read_csv(io.BytesIO(content))
        else:
            pdf = pd.read_excel(io.BytesIO(content), engine="openpyxl")

        df_spark = spark.createDataFrame(pdf.astype(str))
        count = df_spark.count()
        rows_written += count

        safe_name = file_name.replace(" ", "_").replace(".xlsx", "").replace(".csv", "")
        (
            df_spark
            .write
            .mode("overwrite")
            .parquet(f"{LANDING_PATH}{safe_name}/execution_id={execution_id}/")
        )

except Exception as exc:
    status = "ERROR"
    error_msg = traceback.format_exc()
    raise

finally:
    end_ts = datetime.now(timezone.utc)
    duration_s = (end_ts - start_ts).total_seconds()

    log_record = [{
        "notebook":      "nb_landing_sharepoint",
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

print(f"[nb_landing_sharepoint] status={status} rows={rows_written} duration={duration_s:.1f}s")
