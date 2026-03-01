# KPIs — San Martín Contratistas Generales S.A.

## Medidas DAX Principales

Las medidas están definidas en [`../powerbi/measures/kpi_measures.dax`](../powerbi/measures/kpi_measures.dax).

---

## RDP — Rendimiento Diario de Producción

### RDP (gal/HM)
**Consumo de combustible por hora de movimiento.**

```dax
RDP_gal_HM = DIVIDE([Combustible_gal], [HM_Total], BLANK())
```

| Componente       | Medida / Tabla                                                     |
|------------------|--------------------------------------------------------------------|
| Combustible_gal  | `CALCULATE(SUM(Costos_Totales[CANTIDAD]), TIPO_COSTO="COMBUSTIBLE")` |
| HM_Total         | `SUM(fact_rdp[HM])`                                               |

**Rango esperado:** 0 – 100 gal/HM (según tipo de equipo).

---

### HM Total
**Total de Horas de Movimiento.**

```dax
HM_Total = SUM(fact_rdp[HM])
```

---

### Viajes por Hora (V/HR)
**Productividad de acarreo — viajes por hora de movimiento.**

```dax
Viajes_por_hora = DIVIDE([Total_Viajes], [HM_Total], BLANK())
```

**Rango esperado:** 2 – 8 viajes/HM para camiones de acarreo.

---

### Producción (TN)

```dax
Produccion_TN = SUM(fact_rdp[TONELAJE])
```

---

### Costo Total

```dax
Costo_Total = SUM(Costos_Totales[MONTO])
```

---

### Costo por Tonelada

```dax
Costo_por_TN = DIVIDE([Costo_Total], [Produccion_TN], BLANK())
```

---

## Factor K / PB

| Medida            | Definición                                     |
|-------------------|------------------------------------------------|
| Factor_K_promedio | `AVERAGE(dim_dM_factordiario[FACTOR_K])`       |
| Factor_PB_promedio| `AVERAGE(dim_dM_factordiario[FACTOR_PB])`      |

---

## KPIs Acumulados (YTD / MTD)

| Medida              | Definición                                                           |
|---------------------|----------------------------------------------------------------------|
| RDP_YTD             | `CALCULATE([RDP_gal_HM], DATESYTD(dim_calendario[FECHA]))`          |
| Produccion_TN_YTD   | `CALCULATE([Produccion_TN], DATESYTD(dim_calendario[FECHA]))`       |
| Costo_Total_MTD     | `CALCULATE([Costo_Total], DATESMTD(dim_calendario[FECHA]))`         |

---

## KPIs vs. Targets

| Medida                | Definición                                                           |
|-----------------------|----------------------------------------------------------------------|
| HM_vs_Target          | `DIVIDE([HM_Total], MAX(dim_targets[HM_TARGET]), BLANK())`          |
| Produccion_vs_Target  | `DIVIDE([Produccion_TN], MAX(dim_targets[TN_TARGET]), BLANK())`     |
| RDP_vs_Target         | `DIVIDE([RDP_gal_HM], MAX(dim_targets[RDP_TARGET]), BLANK())`       |

---

## KPIs de Perforación

| Medida           | Definición                                                       |
|------------------|------------------------------------------------------------------|
| MTS_por_HRS      | `DIVIDE([Metros_Perforados], [Horas_Perforacion], BLANK())`     |

---

## Columnas Calculadas en fact_rdp (PySpark)

Calculadas en `nb_work_fact_rdp.py` durante la transformación:

| Columna  | Fórmula                         | Descripción              |
|----------|---------------------------------|--------------------------|
| V_HR     | VIAJES / HM                     | Viajes por hora          |
| MTS_HRS  | METROS / HORAS                  | Metros por hora          |
| TN_DIST  | TONELAJE × DISTANCIA            | Indicador tkm            |
| TN_VJ    | TONELAJE / VIAJES               | Tonelaje por viaje       |
