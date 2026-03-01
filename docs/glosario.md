# Glosario — San Martín Contratistas Generales S.A.

## Siglas y Términos de Negocio

| Término              | Definición                                                                 |
|----------------------|----------------------------------------------------------------------------|
| **RDP**              | Rendimiento Diario de Producción — reporte operativo diario de equipos     |
| **HM**               | Horas de Movimiento — tiempo efectivo de operación de un equipo            |
| **TN**               | Tonelaje — masa de material movido (toneladas métricas)                    |
| **V/HR**             | Viajes por Hora — KPI de productividad de acarreo                         |
| **MTS/HRS**          | Metros por Hora — KPI de productividad de perforación                     |
| **TN×DIST**          | Tonelaje × Distancia — indicador de trabajo de acarreo (tkm)              |
| **TN/VJ**            | Tonelaje por Viaje — carga promedio por ciclo de acarreo                  |
| **Factor K**         | Factor de normalización de combustible por condiciones de operación        |
| **Factor PB**        | Factor de productividad base para benchmarking                             |
| **KOB1**             | Transacción SAP para consulta de costos reales por orden de mantenimiento  |
| **ZWS**              | Prefijo de Web Services SOAP personalizados en SAP (Z = custom)            |
| **CARGUIO**          | Tipo de flota: equipos de carguío (excavadoras, cargadores)               |
| **ACARREO**          | Tipo de flota: camiones de transporte de mineral                           |
| **PERFORACION**      | Tipo de flota: perforadoras rotativas y de percusión                       |
| **AUXILIAR**         | Tipo de flota: equipos de apoyo (motoniveladoras, tractores, cisternas)    |

---

## Términos de Arquitectura

| Término              | Definición                                                                 |
|----------------------|----------------------------------------------------------------------------|
| **Landing**          | Zona de ingesta cruda — datos sin transformar (Parquet/JSON)               |
| **Work**             | Zona limpia — datos normalizados y validados (Parquet, schema enforced)    |
| **Work Live**        | Zona de serving — Delta Tables para consumo Power BI                       |
| **Medallion**        | Patrón de arquitectura de datos con capas Bronze/Silver/Gold (equivalente a Landing/Work/Work Live) |
| **Truncate/Insert**  | Patrón de carga: borrar tabla destino y reescribir completo                |
| **Merge/Upsert**     | Patrón de carga: actualizar registros existentes e insertar nuevos         |
| **OneLake**          | Almacenamiento unificado de Microsoft Fabric (basado en ADLS Gen2)         |
| **ADLS Gen2**        | Azure Data Lake Storage Gen2                                               |
| **Delta Lake**       | Formato de tabla ACID open-source sobre Parquet                            |
| **execution_id**     | ID único de ejecución de notebook (GUID o timestamp) para trazabilidad     |

---

## Términos SAP

| Término              | Definición                                                                 |
|----------------------|----------------------------------------------------------------------------|
| **SOAP**             | Simple Object Access Protocol — protocolo de Web Services                  |
| **WSDL**             | Web Services Description Language — descriptor del servicio SAP            |
| **zeep**             | Librería Python para consumir Web Services SOAP                            |
| **Centro de Costo**  | Unidad organizacional SAP para imputación de costos                        |
| **Orden de Mantenimiento** | Documento SAP que agrupa costos de mantenimiento de un equipo        |

---

## Abreviaciones en Columnas

| Columna           | Significado completo                       |
|-------------------|--------------------------------------------|
| `EQUIPO_ID`       | Identificador del equipo (SAP)             |
| `TIPO_DE_FLOTA`   | Categoría operativa del equipo             |
| `NIVEL_I/II/III`  | Jerarquía de clasificación del equipo      |
| `MONTO`           | Monto monetario (USD por defecto)          |
| `CANTIDAD`        | Cantidad en unidad de medida del costo     |
| `TIPO_COSTO`      | Categoría del costo (COMBUSTIBLE, etc.)    |
