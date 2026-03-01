# sanmartin-fabric-bi

**BI / Data Engineering platform for San Martín Contratistas Generales S.A.**
Mining operations in Peru — Microsoft Fabric + SAP integration.

---

## Overview

This project modernizes the data model and operational reports for San Martín Contratistas Generales S.A., migrating from manual Excel-based processes to an automated architecture on **Microsoft Fabric (Lakehouse)** with direct SAP integration via SOAP Web Services.

---

## Repository Structure

```
sanmartin-fabric-bi/
│
├── fabric/
│   ├── notebooks/                  # PySpark notebooks (.py)
│   │   ├── nb_landing_sap_equipos.py     # SAP SOAP → landing (fleet master)
│   │   ├── nb_landing_sap_costos.py      # SAP ZWS_GET_KOB1 → landing (costs)
│   │   ├── nb_landing_sharepoint.py      # SharePoint Excel/CSV → landing
│   │   ├── nb_work_dim_equipos.py        # Clean + normalize dim_equipos (hybrid)
│   │   ├── nb_work_fact_rdp.py           # Transform fact_rdp + KPI columns
│   │   ├── nb_work_costos_totales.py     # Clean Costos_Totales + join dim_equipos
│   │   └── nb_work_live_serving.py       # Serving layer merge (Work → Work Live)
│   └── lakehouses/
│       └── lakehouse_config.json         # Lakehouse container definitions
│
├── functions/
│   └── sap_integration/
│       ├── __init__.py
│       └── sap_client.py                 # SAP SOAP client using zeep
│
├── sql/
│   ├── ddl/                        # CREATE TABLE scripts
│   │   ├── dim_equipos.sql
│   │   ├── dim_calendario.sql
│   │   ├── dim_others.sql          # dim_actividad, dim_mina, dim_targets, etc.
│   │   ├── fact_rdp.sql
│   │   ├── fact_perforacion.sql
│   │   └── costos_totales.sql
│   └── validations/                # Data quality queries
│       ├── val_ratio_checks.sql
│       ├── val_null_checks.sql
│       └── val_referential_integrity.sql
│
├── powerbi/
│   ├── measures/
│   │   └── kpi_measures.dax        # All DAX measure definitions
│   └── model/
│       └── semantic_model.json     # Tables, columns, relationships
│
├── master_tables/                  # CSV seed files for dim_equipos enrichment
│   ├── map_equipo_contratista.csv
│   ├── map_codigo_tipo_flota.csv
│   └── map_equipo_niveles.csv
│
├── infra/
│   ├── fabric_workspace.json       # Fabric workspace config
│   ├── adf_pipelines.json          # ADF pipeline definitions
│   └── azure_devops_pipeline.yml   # CI/CD pipeline
│
├── docs/
│   ├── arquitectura.md             # Architecture overview
│   ├── modelo_datos.md             # Data model documentation
│   ├── kpis.md                     # KPI definitions
│   └── glosario.md                 # Business glossary
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Data Architecture (Medallion)

```
SAP ERP (SOAP)          SharePoint Online
      │                        │
      ▼                        ▼
 ┌─────────────────────────────────────┐
 │          LANDING (raw Parquet)      │  retention: 90d
 └─────────────────────┬───────────────┘
                       │ PySpark (nb_work_*)
                       ▼
 ┌─────────────────────────────────────┐
 │    WORK (cleansed Parquet)          │  pattern: truncate/insert
 └─────────────────────┬───────────────┘
                       │ Merge / Upsert
                       ▼
 ┌─────────────────────────────────────┐
 │  WORK LIVE (Delta Tables)           │  Power BI DirectQuery / Import
 └─────────────────────────────────────┘
```

---

## Data Model

**Fact tables:** `fact_rdp`, `fact_perforacion`, `Costos_Totales`

**Dimensions:** `dim_equipos`, `dim_calendario`, `dim_actividad`, `dim_mina`, `dim_dM_factordiario`, `dim_targets`, `dim_tecnologia`

---

## Key DAX Measures

| Measure              | Formula                                                        |
|----------------------|----------------------------------------------------------------|
| `HM_Total`           | `SUM(fact_rdp[HM])`                                           |
| `Combustible_gal`    | `CALCULATE(SUM(Costos_Totales[CANTIDAD]), TIPO_COSTO="COMBUSTIBLE")` |
| `RDP_gal_HM`         | `DIVIDE([Combustible_gal], [HM_Total], BLANK())`              |
| `Produccion_TN`      | `SUM(fact_rdp[TONELAJE])`                                     |
| `Viajes_por_hora`    | `DIVIDE([Total_Viajes], [HM_Total], BLANK())`                 |
| `Costo_Total`        | `SUM(Costos_Totales[MONTO])`                                  |

---

## SAP Web Services

| Method                  | SAP WSDL            | Description                  |
|-------------------------|---------------------|------------------------------|
| `get_equipos()`         | ZWS_GET_EQUIPOS     | Fleet master data            |
| `get_costos_equipos()`  | ZWS_GET_KOB1        | Equipment costs (Costos Eq.) |
| `get_inventario()`      | ZWS_GET_INVENTARIO  | Inventory                    |
| `get_partes()`          | ZWS_GET_PARTES      | Spare parts                  |
| `get_servicios()`       | ZWS_GET_SERVICIOS   | Services                     |
| `get_movimientos()`     | ZWS_GET_MOVIMIENTOS | Accounting movements         |

Configure via environment variables:
```
SAP_WSDL_BASE_URL=https://sap-host:443
SAP_USERNAME=svc_bi_user
SAP_PASSWORD=<secret>
```

---

## dim_equipos Hybrid Model

`dim_equipos` combines SAP master data with 3 CSV seed files (left joins):

| Master Table                   | Enriched Field       | Logic                      |
|--------------------------------|----------------------|----------------------------|
| `map_equipo_contratista.csv`   | EMPRESA_CONTRATISTA  | JOIN by EQUIPO_ID          |
| `map_codigo_tipo_flota.csv`    | TIPO_DE_FLOTA        | Prefix-based classification|
| `map_equipo_niveles.csv`       | NIVEL_I/II/III       | JOIN by EQUIPO_ID          |

**Fleet type prefixes:** `C-` → CARGUIO, `V-` → ACARREO, `RE-` → CARGUIO, `P-` → PERFORACION

---

## Notebook Parameters

All notebooks accept these parameters via `mssparkutils.notebook.run` or widgets:

| Parameter         | Description                                    |
|-------------------|------------------------------------------------|
| `storage_account` | ADLS Gen2 / OneLake account name               |
| `environment`     | `dev` \| `qa` \| `prod`                       |
| `execution_id`    | Unique run ID (GUID or timestamp)              |

---

## Tech Stack

- **Microsoft Fabric** (Lakehouse, OneLake)
- **Azure Data Factory** — optional orchestration
- **Azure Databricks / PySpark** — data transformation
- **Azure DevOps** — CI/CD
- **Power BI** — semantic model + DAX measures
- **SAP ERP** — SOAP Web Services via `zeep`
- **SharePoint Online** — Excel/CSV files
- **SQL Server / Azure SQL** — relational layer

---

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Set SAP credentials
export SAP_WSDL_BASE_URL=https://your-sap-host:443
export SAP_USERNAME=svc_bi_user
export SAP_PASSWORD=your_password

# Run SAP client (example)
python -c "
from functions.sap_integration import SapSoapClient
client = SapSoapClient()
equipos = client.get_equipos()
print(f'Retrieved {len(equipos)} equipment records')
"
```

---

## Documentation

| Document                              | Description                    |
|---------------------------------------|--------------------------------|
| [docs/arquitectura.md](docs/arquitectura.md) | Architecture overview   |
| [docs/modelo_datos.md](docs/modelo_datos.md) | Data model documentation|
| [docs/kpis.md](docs/kpis.md)                 | KPI definitions         |
| [docs/glosario.md](docs/glosario.md)         | Business glossary       |

---

## License

Internal project — San Martín Contratistas Generales S.A. All rights reserved.
