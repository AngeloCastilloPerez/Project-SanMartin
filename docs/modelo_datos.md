# Modelo de Datos — San Martín Contratistas Generales S.A.

## Diagrama ER (Simplified)

```
dim_calendario ──────────────────────────────┐
                                             │
dim_mina ─────────────────────────────────┐  │
                                          │  │
dim_actividad ──────────────────────────┐ │  │
                                        │ │  │
dim_equipos ─────────────────────────┐  │ │  │
     │                               │  │ │  │
     │  dim_tecnologia               │  │ │  │
     │  dim_targets                  │  │ │  │
     │                               ▼  ▼ ▼  ▼
     │                           ┌────────────────┐
     │                           │   fact_rdp     │
     │                           └────────────────┘
     │
     └──────────────────────────►┌──────────────────────┐
                                 │  fact_perforacion    │
                                 └──────────────────────┘
     │
     └──────────────────────────►┌──────────────────────┐
                                 │   Costos_Totales     │
                                 └──────────────────────┘

dim_dM_factordiario → dim_equipos + dim_calendario
```

---

## Tablas de Hechos

### fact_rdp
Rendimiento Diario de Producción — granularidad: equipo × día × turno.

| Columna       | Tipo         | Descripción                           |
|---------------|--------------|---------------------------------------|
| RDP_ID        | BIGINT (PK)  | Surrogate key                         |
| FECHA         | DATE         | FK → dim_calendario                   |
| EQUIPO_ID     | VARCHAR(20)  | FK → dim_equipos                      |
| MINA_ID       | VARCHAR(20)  | FK → dim_mina                         |
| ACTIVIDAD_ID  | VARCHAR(20)  | FK → dim_actividad                    |
| TURNO         | VARCHAR(10)  | DIA / NOCHE                           |
| HM            | DECIMAL      | Horas de Movimiento                   |
| HORAS         | DECIMAL      | Horas totales                         |
| VIAJES        | INT          | Número de viajes                      |
| METROS        | DECIMAL      | Metros perforados                     |
| TONELAJE      | DECIMAL      | Tonelaje movido                       |
| DISTANCIA     | DECIMAL      | Distancia recorrida (km)              |
| V_HR          | DECIMAL      | **KPI**: Viajes / HM                  |
| MTS_HRS       | DECIMAL      | **KPI**: Metros / Horas               |
| TN_DIST       | DECIMAL      | **KPI**: Tonelaje × Distancia         |
| TN_VJ         | DECIMAL      | **KPI**: Tonelaje / Viaje             |

### Costos_Totales
Costos de equipos de SAP (ZWS_GET_KOB1) — granularidad: equipo × día × tipo de costo.

| Columna             | Tipo        | Descripción                          |
|---------------------|-------------|--------------------------------------|
| COSTO_ID            | BIGINT (PK) | Surrogate key                        |
| FECHA               | DATE        | FK → dim_calendario                  |
| EQUIPO_ID           | VARCHAR(20) | FK → dim_equipos                     |
| TIPO_COSTO          | VARCHAR(50) | COMBUSTIBLE, MANTENIMIENTO, etc.     |
| CANTIDAD            | DECIMAL     | Cantidad en unidad medida            |
| MONTO               | DECIMAL     | Monto en USD                         |
| EMPRESA_CONTRATISTA | VARCHAR(100)| Enriquecido desde dim_equipos        |
| TIPO_DE_FLOTA       | VARCHAR(50) | Enriquecido desde dim_equipos        |

---

## Dimensiones

### dim_equipos (Híbrido: SAP + Master Tables)

Fuente primaria: SAP Web Service `ZWS_GET_EQUIPOS`.
Enriquecida con 3 tablas maestras (CSV):

| Master Table               | Campo enriquecido         | Lógica                                    |
|----------------------------|---------------------------|-------------------------------------------|
| map_equipo_contratista.csv | EMPRESA_CONTRATISTA       | JOIN por EQUIPO_ID                        |
| map_codigo_tipo_flota.csv  | TIPO_DE_FLOTA             | JOIN por EQUIPO_ID (basado en prefijo)    |
| map_equipo_niveles.csv     | NIVEL_I, NIVEL_II, NIVEL_III | JOIN por EQUIPO_ID                     |

**Prefijos de TIPO_DE_FLOTA:**

| Prefijo | TIPO_DE_FLOTA |
|---------|---------------|
| `C-`    | CARGUIO       |
| `V-`    | ACARREO       |
| `RE-`   | CARGUIO       |
| `P-`    | PERFORACION   |
| `AUX-`  | AUXILIAR      |

### dim_calendario
Dimensión fecha estándar para time intelligence en Power BI.
Incluye: DIA, MES, ANIO, TRIMESTRE, SEMANA, NOM_MES, PERIODO, ES_FIN_SEMANA.

### dim_dM_factordiario
Factor de normalización diario por equipo (Factor K y Factor PB).
Usado en medidas DAX de ratio acumulado.

### dim_targets
Metas de producción y costo por periodo y tipo de flota.

---

## Normalización de Texto

Todos los campos string en el pipeline Work aplican:
1. Eliminar acentos (`unicodedata.normalize("NFKD")`)
2. Convertir a ASCII
3. UPPERCASE
4. STRIP (eliminar espacios al inicio/fin)

---

## Schema del Modelo Semántico Power BI

Ver [`../powerbi/model/semantic_model.json`](../powerbi/model/semantic_model.json).
