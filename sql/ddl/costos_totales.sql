-- =============================================================================
-- DDL: Costos_Totales
-- Description: Total equipment costs from SAP (ZWS_GET_KOB1)
-- =============================================================================

CREATE TABLE IF NOT EXISTS Costos_Totales (
    COSTO_ID        BIGINT          NOT NULL IDENTITY(1,1),
    FECHA           DATE            NOT NULL,
    EQUIPO_ID       VARCHAR(20)     NOT NULL,
    CENTRO_COSTO    VARCHAR(20),
    TIPO_COSTO      VARCHAR(50),    -- COMBUSTIBLE | MANTENIMIENTO | NEUMATICOS | LUBRICANTES | OTROS
    DESCRIPCION     VARCHAR(200),
    CANTIDAD        DECIMAL(14, 4),
    UNIDAD          VARCHAR(20),
    MONTO           DECIMAL(16, 2),
    MONEDA          VARCHAR(5)      DEFAULT 'USD',
    -- Enriched from dim_equipos
    EMPRESA_CONTRATISTA VARCHAR(100),
    TIPO_DE_FLOTA   VARCHAR(50),
    NIVEL_I         VARCHAR(100),
    NIVEL_II        VARCHAR(100),
    execution_id    VARCHAR(100),
    load_ts         DATETIME2       DEFAULT GETUTCDATE(),
    CONSTRAINT pk_costos_totales PRIMARY KEY (COSTO_ID),
    CONSTRAINT fk_costos_equipo FOREIGN KEY (EQUIPO_ID) REFERENCES dim_equipos (EQUIPO_ID),
    CONSTRAINT fk_costos_fecha  FOREIGN KEY (FECHA)     REFERENCES dim_calendario (FECHA)
);

CREATE INDEX IF NOT EXISTS idx_costos_fecha      ON Costos_Totales (FECHA);
CREATE INDEX IF NOT EXISTS idx_costos_equipo     ON Costos_Totales (EQUIPO_ID);
CREATE INDEX IF NOT EXISTS idx_costos_tipo       ON Costos_Totales (TIPO_COSTO);
CREATE INDEX IF NOT EXISTS idx_costos_periodo    ON Costos_Totales (FECHA, EQUIPO_ID, TIPO_COSTO);
