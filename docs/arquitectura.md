# Arquitectura de Datos — San Martín Contratistas Generales S.A.

## Visión General

Este proyecto reemplaza los procesos manuales basados en Excel por una arquitectura de datos automatizada sobre **Microsoft Fabric (Lakehouse)**, con integración directa a **SAP ERP** mediante Web Services SOAP.

---

## Stack Tecnológico

| Capa              | Tecnología                                      |
|-------------------|-------------------------------------------------|
| Ingesta           | Azure Data Factory + Python (`zeep`)            |
| Almacenamiento    | Microsoft Fabric Lakehouse (OneLake / ADLS Gen2)|
| Transformación    | Azure Databricks / PySpark (Fabric Notebooks)   |
| Serving           | Delta Tables (Work Live layer)                  |
| Visualización     | Power BI (modelo semántico + DAX)               |
| Orquestación      | Azure Data Factory (pipelines)                  |
| CI/CD             | Azure DevOps                                    |
| Fuentes           | SAP ERP (SOAP), SharePoint Online               |

---

## Arquitectura Medallion

```
┌────────────────────────────────────────────────────────────────┐
│                        FUENTES DE DATOS                         │
│   SAP ERP (SOAP/zeep)          SharePoint Online (Excel/CSV)   │
└──────────────┬─────────────────────────────┬───────────────────┘
               │                             │
               ▼                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                    LANDING LAYER (Lakehouse)                      │
│  Formato: Parquet particionado por execution_id                  │
│  Retención: 90 días                                              │
│  Tablas: sap/equipos, sap/costos, sharepoint/rdp, ...           │
└──────────────────────────────┬───────────────────────────────────┘
                               │  PySpark Notebooks
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                      WORK LAYER (Lakehouse)                      │
│  Formato: Parquet (schema-enforced)                              │
│  Patrón: Truncate/Insert (overwrite)                            │
│  Tablas: dim_equipos, fact_rdp, costos_totales, ...             │
└──────────────────────────────┬───────────────────────────────────┘
                               │  Merge / Upsert
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                   WORK LIVE LAYER (Delta Tables)                 │
│  Formato: Delta Lake (ACID)                                      │
│  Acceso: Power BI DirectQuery / Import                          │
│  Tablas: todas las dimensiones + facts                          │
└──────────────────────────────────────────────────────────────────┘
```

---

## Notebooks PySpark

| Notebook                     | Origen             | Destino              | Patrón       |
|------------------------------|--------------------|----------------------|--------------|
| `nb_landing_sap_equipos`     | SAP ZWS_GET_EQUIPOS| Landing/sap/equipos  | Overwrite    |
| `nb_landing_sap_costos`      | SAP ZWS_GET_KOB1   | Landing/sap/costos   | Overwrite    |
| `nb_landing_sharepoint`      | SharePoint Online  | Landing/sharepoint   | Overwrite    |
| `nb_work_dim_equipos`        | Landing + Master   | Work/dim_equipos     | Overwrite    |
| `nb_work_fact_rdp`           | Landing/sharepoint | Work/fact_rdp        | Overwrite    |
| `nb_work_costos_totales`     | Landing/costos     | Work/costos_totales  | Overwrite    |
| `nb_work_live_serving`       | Work layer         | Work Live (Delta)    | Merge/Upsert |

---

## Parámetros Comunes de Notebooks

Todos los notebooks aceptan los siguientes parámetros via `mssparkutils.notebook.run` o widgets:

| Parámetro         | Tipo   | Descripción                              |
|-------------------|--------|------------------------------------------|
| `storage_account` | string | Nombre de la cuenta ADLS Gen2 / OneLake  |
| `environment`     | string | `dev` \| `qa` \| `prod`                 |
| `execution_id`    | string | ID único del run (GUID o timestamp)      |

---

## Logs de Ejecución

Cada notebook escribe un registro de log en la capa `logs/`:

```
logs/{environment}/{notebook_name}/date={YYYY-MM-DD}/
```

Campos del log: `notebook`, `execution_id`, `environment`, `start_ts`, `end_ts`, `duration_s`, `rows_written`, `status`, `error_msg`.

---

## Integración SAP

Ver [`../functions/sap_integration/sap_client.py`](../functions/sap_integration/sap_client.py) y [`kpis.md`](kpis.md).

Los Web Services SOAP se consumen con `zeep`. Las credenciales se leen desde variables de entorno:

```
SAP_WSDL_BASE_URL=https://sap-host:443
SAP_USERNAME=svc_bi_user
SAP_PASSWORD=<secret>
```

---

## CI/CD

Ver [`../infra/azure_devops_pipeline.yml`](../infra/azure_devops_pipeline.yml).

- **develop** → deploy automático a workspace `dev`
- **main** → deploy con aprobación manual a workspace `prod`
