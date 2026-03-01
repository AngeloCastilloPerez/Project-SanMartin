-- =============================================================================
-- DDL: dim_equipos
-- Description: Equipment (fleet) dimension — enriched from SAP + master tables
-- =============================================================================

CREATE TABLE IF NOT EXISTS dim_equipos (
    EQUIPO_ID           VARCHAR(20)     NOT NULL,   -- SAP equipment number
    DESCRIPCION         VARCHAR(200),
    EMPRESA_CONTRATISTA VARCHAR(100),               -- from map_equipo_contratista
    TIPO_DE_FLOTA       VARCHAR(50),                -- CARGUIO | ACARREO | PERFORACION | AUXILIAR
    NIVEL_I             VARCHAR(100),               -- from map_equipo_niveles
    NIVEL_II            VARCHAR(100),
    NIVEL_III           VARCHAR(100),
    CENTRO_COSTO        VARCHAR(20),
    CLASE_EQUIPO        VARCHAR(50),
    ESTADO              VARCHAR(20),
    MODELO              VARCHAR(100),
    FABRICANTE          VARCHAR(100),
    ANIO_FABRICACION    INT,
    CAPACIDAD_TN        DECIMAL(10, 2),
    TECNOLOGIA          VARCHAR(50),
    execution_id        VARCHAR(100),
    load_ts             DATETIME2       DEFAULT GETUTCDATE(),
    CONSTRAINT pk_dim_equipos PRIMARY KEY (EQUIPO_ID)
);

CREATE INDEX IF NOT EXISTS idx_dim_equipos_tipo_flota  ON dim_equipos (TIPO_DE_FLOTA);
CREATE INDEX IF NOT EXISTS idx_dim_equipos_contratista ON dim_equipos (EMPRESA_CONTRATISTA);
