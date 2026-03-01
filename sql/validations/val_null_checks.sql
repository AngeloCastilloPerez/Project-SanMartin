-- =============================================================================
-- Validation Queries: Null Checks
-- Description: Validate mandatory fields are not null in fact and dimension tables
-- =============================================================================

-- ----------------------------------------------------------------------------
-- 1. fact_rdp — mandatory columns
-- ----------------------------------------------------------------------------
SELECT
    RDP_ID,
    FECHA,
    EQUIPO_ID,
    'fact_rdp: NULL in mandatory column' AS validation_message,
    CASE
        WHEN FECHA     IS NULL THEN 'FECHA'
        WHEN EQUIPO_ID IS NULL THEN 'EQUIPO_ID'
        WHEN HM        IS NULL THEN 'HM'
    END AS null_column
FROM fact_rdp
WHERE FECHA     IS NULL
   OR EQUIPO_ID IS NULL
   OR HM        IS NULL;

-- ----------------------------------------------------------------------------
-- 2. Costos_Totales — mandatory columns
-- ----------------------------------------------------------------------------
SELECT
    COSTO_ID,
    FECHA,
    EQUIPO_ID,
    TIPO_COSTO,
    'Costos_Totales: NULL in mandatory column' AS validation_message,
    CASE
        WHEN FECHA      IS NULL THEN 'FECHA'
        WHEN EQUIPO_ID  IS NULL THEN 'EQUIPO_ID'
        WHEN TIPO_COSTO IS NULL THEN 'TIPO_COSTO'
        WHEN MONTO      IS NULL THEN 'MONTO'
    END AS null_column
FROM Costos_Totales
WHERE FECHA      IS NULL
   OR EQUIPO_ID  IS NULL
   OR TIPO_COSTO IS NULL
   OR MONTO      IS NULL;

-- ----------------------------------------------------------------------------
-- 3. dim_equipos — mandatory columns
-- ----------------------------------------------------------------------------
SELECT
    EQUIPO_ID,
    'dim_equipos: NULL in mandatory column' AS validation_message,
    CASE
        WHEN EQUIPO_ID IS NULL THEN 'EQUIPO_ID'
        WHEN TIPO_DE_FLOTA IS NULL THEN 'TIPO_DE_FLOTA'
    END AS null_column
FROM dim_equipos
WHERE EQUIPO_ID    IS NULL
   OR TIPO_DE_FLOTA IS NULL;

-- ----------------------------------------------------------------------------
-- 4. Summary: count nulls per table
-- ----------------------------------------------------------------------------
SELECT 'fact_rdp'       AS table_name, COUNT(*) AS null_rows FROM fact_rdp      WHERE FECHA IS NULL OR EQUIPO_ID IS NULL
UNION ALL
SELECT 'Costos_Totales' AS table_name, COUNT(*) AS null_rows FROM Costos_Totales WHERE FECHA IS NULL OR EQUIPO_ID IS NULL
UNION ALL
SELECT 'dim_equipos'    AS table_name, COUNT(*) AS null_rows FROM dim_equipos   WHERE EQUIPO_ID IS NULL;
