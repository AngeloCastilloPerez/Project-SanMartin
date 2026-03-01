-- =============================================================================
-- Validation Queries: Referential Integrity Checks
-- Description: Detect orphan records in fact tables (FK violations)
-- =============================================================================

-- ----------------------------------------------------------------------------
-- 1. fact_rdp → dim_equipos (orphan EQUIPO_ID)
-- ----------------------------------------------------------------------------
SELECT
    r.RDP_ID,
    r.FECHA,
    r.EQUIPO_ID,
    'fact_rdp: EQUIPO_ID not found in dim_equipos' AS validation_message
FROM fact_rdp r
LEFT JOIN dim_equipos e ON r.EQUIPO_ID = e.EQUIPO_ID
WHERE e.EQUIPO_ID IS NULL
  AND r.EQUIPO_ID IS NOT NULL;

-- ----------------------------------------------------------------------------
-- 2. fact_rdp → dim_calendario (orphan FECHA)
-- ----------------------------------------------------------------------------
SELECT
    r.RDP_ID,
    r.FECHA,
    'fact_rdp: FECHA not found in dim_calendario' AS validation_message
FROM fact_rdp r
LEFT JOIN dim_calendario c ON r.FECHA = c.FECHA
WHERE c.FECHA IS NULL
  AND r.FECHA IS NOT NULL;

-- ----------------------------------------------------------------------------
-- 3. Costos_Totales → dim_equipos (orphan EQUIPO_ID)
-- ----------------------------------------------------------------------------
SELECT
    ct.COSTO_ID,
    ct.FECHA,
    ct.EQUIPO_ID,
    'Costos_Totales: EQUIPO_ID not found in dim_equipos' AS validation_message
FROM Costos_Totales ct
LEFT JOIN dim_equipos e ON ct.EQUIPO_ID = e.EQUIPO_ID
WHERE e.EQUIPO_ID IS NULL
  AND ct.EQUIPO_ID IS NOT NULL;

-- ----------------------------------------------------------------------------
-- 4. Costos_Totales → dim_calendario (orphan FECHA)
-- ----------------------------------------------------------------------------
SELECT
    ct.COSTO_ID,
    ct.FECHA,
    'Costos_Totales: FECHA not found in dim_calendario' AS validation_message
FROM Costos_Totales ct
LEFT JOIN dim_calendario c ON ct.FECHA = c.FECHA
WHERE c.FECHA IS NULL
  AND ct.FECHA IS NOT NULL;

-- ----------------------------------------------------------------------------
-- 5. Summary: orphan counts per table + foreign key
-- ----------------------------------------------------------------------------
SELECT
    'fact_rdp → dim_equipos'       AS check_name,
    COUNT(*)                        AS orphan_rows
FROM fact_rdp r
LEFT JOIN dim_equipos e ON r.EQUIPO_ID = e.EQUIPO_ID
WHERE e.EQUIPO_ID IS NULL AND r.EQUIPO_ID IS NOT NULL
UNION ALL
SELECT
    'fact_rdp → dim_calendario'    AS check_name,
    COUNT(*)                        AS orphan_rows
FROM fact_rdp r
LEFT JOIN dim_calendario c ON r.FECHA = c.FECHA
WHERE c.FECHA IS NULL AND r.FECHA IS NOT NULL
UNION ALL
SELECT
    'Costos_Totales → dim_equipos' AS check_name,
    COUNT(*)                        AS orphan_rows
FROM Costos_Totales ct
LEFT JOIN dim_equipos e ON ct.EQUIPO_ID = e.EQUIPO_ID
WHERE e.EQUIPO_ID IS NULL AND ct.EQUIPO_ID IS NOT NULL;
