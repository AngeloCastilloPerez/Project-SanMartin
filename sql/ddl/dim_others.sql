-- =============================================================================
-- DDL: dim_actividad, dim_mina, dim_dM_factordiario, dim_targets, dim_tecnologia
-- =============================================================================

-- ----------------------------------------------------------------------------
-- dim_actividad
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_actividad (
    ACTIVIDAD_ID    VARCHAR(20)     NOT NULL,
    DESCRIPCION     VARCHAR(200),
    CATEGORIA       VARCHAR(100),
    CONSTRAINT pk_dim_actividad PRIMARY KEY (ACTIVIDAD_ID)
);

-- ----------------------------------------------------------------------------
-- dim_mina
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_mina (
    MINA_ID         VARCHAR(20)     NOT NULL,
    NOMBRE          VARCHAR(100),
    UBICACION       VARCHAR(200),
    TIPO_MINA       VARCHAR(50),    -- TAJO ABIERTO | SOCAVON
    CONSTRAINT pk_dim_mina PRIMARY KEY (MINA_ID)
);

-- ----------------------------------------------------------------------------
-- dim_dM_factordiario
-- Description: Daily factor (Factor K / PB) for KPI normalization
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_dM_factordiario (
    FECHA           DATE            NOT NULL,
    EQUIPO_ID       VARCHAR(20)     NOT NULL,
    FACTOR_K        DECIMAL(10, 4),
    FACTOR_PB       DECIMAL(10, 4),
    OBSERVACION     VARCHAR(200),
    execution_id    VARCHAR(100),
    load_ts         DATETIME2       DEFAULT GETUTCDATE(),
    CONSTRAINT pk_dim_factordiario PRIMARY KEY (FECHA, EQUIPO_ID)
);

-- ----------------------------------------------------------------------------
-- dim_targets
-- Description: Production and cost targets per period and equipment type
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_targets (
    TARGET_ID       INT             NOT NULL IDENTITY(1,1),
    PERIODO         VARCHAR(7),     -- "YYYY-MM"
    TIPO_DE_FLOTA   VARCHAR(50),
    MINA_ID         VARCHAR(20),
    HM_TARGET       DECIMAL(12, 2),
    TN_TARGET       DECIMAL(14, 2),
    COSTO_TARGET    DECIMAL(14, 2),
    RDP_TARGET      DECIMAL(10, 4),
    CONSTRAINT pk_dim_targets PRIMARY KEY (TARGET_ID)
);

-- ----------------------------------------------------------------------------
-- dim_tecnologia
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_tecnologia (
    TECNOLOGIA_ID   VARCHAR(20)     NOT NULL,
    DESCRIPCION     VARCHAR(200),
    CATEGORIA       VARCHAR(100),   -- ELECTRICO | DIESEL | HIBRIDO
    CONSTRAINT pk_dim_tecnologia PRIMARY KEY (TECNOLOGIA_ID)
);
