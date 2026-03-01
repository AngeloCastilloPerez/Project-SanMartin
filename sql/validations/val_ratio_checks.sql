-- =============================================================================
-- Validation Queries: Ratio Checks
-- Description: Validate KPI ratios are within expected business ranges
-- =============================================================================

-- ----------------------------------------------------------------------------
-- 1. V/HR (Viajes por Hora) should be between 0 and 20 for acarreo equipment
-- ----------------------------------------------------------------------------
SELECT
    FECHA,
    EQUIPO_ID,
    V_HR,
    'V_HR out of range [0-20]' AS validation_message
FROM fact_rdp
WHERE V_HR IS NOT NULL
  AND (V_HR < 0 OR V_HR > 20);

-- ----------------------------------------------------------------------------
-- 2. MTS/HRS (Metros por Hora) should be > 0 and < 200
-- ----------------------------------------------------------------------------
SELECT
    FECHA,
    EQUIPO_ID,
    MTS_HRS,
    'MTS_HRS out of range (0-200]' AS validation_message
FROM fact_rdp
WHERE MTS_HRS IS NOT NULL
  AND (MTS_HRS <= 0 OR MTS_HRS > 200);

-- ----------------------------------------------------------------------------
-- 3. TN/VJ (Tonelaje por Viaje) — expect 30–250 t for haul trucks
-- ----------------------------------------------------------------------------
SELECT
    r.FECHA,
    r.EQUIPO_ID,
    e.TIPO_DE_FLOTA,
    r.TN_VJ,
    'TN_VJ out of expected range for ACARREO' AS validation_message
FROM fact_rdp r
JOIN dim_equipos e ON r.EQUIPO_ID = e.EQUIPO_ID
WHERE e.TIPO_DE_FLOTA = 'ACARREO'
  AND r.TN_VJ IS NOT NULL
  AND (r.TN_VJ < 30 OR r.TN_VJ > 250);

-- ----------------------------------------------------------------------------
-- 4. RDP (gal/HM) — fuel efficiency ratio should be 0–100
-- ----------------------------------------------------------------------------
SELECT
    ct.FECHA,
    ct.EQUIPO_ID,
    SUM(ct.CANTIDAD)                                     AS combustible_gal,
    MAX(r.HM)                                            AS hm_total,
    CASE
        WHEN MAX(r.HM) > 0
        THEN SUM(ct.CANTIDAD) / MAX(r.HM)
        ELSE NULL
    END                                                  AS rdp_gal_hm,
    'RDP_gal_HM out of range (0-100]' AS validation_message
FROM Costos_Totales ct
JOIN fact_rdp r
  ON ct.EQUIPO_ID = r.EQUIPO_ID
 AND ct.FECHA     = r.FECHA
WHERE ct.TIPO_COSTO = 'COMBUSTIBLE'
GROUP BY ct.FECHA, ct.EQUIPO_ID
HAVING
    (MAX(r.HM) > 0 AND SUM(ct.CANTIDAD) / MAX(r.HM) > 100)
    OR (MAX(r.HM) > 0 AND SUM(ct.CANTIDAD) / MAX(r.HM) < 0);
