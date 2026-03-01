-- =============================================================================
-- DDL: dim_calendario
-- Description: Date dimension — supports time intelligence in Power BI
-- =============================================================================

CREATE TABLE IF NOT EXISTS dim_calendario (
    FECHA           DATE            NOT NULL,
    DIA             INT,
    MES             INT,
    ANIO            INT,
    TRIMESTRE       INT,
    SEMANA          INT,
    DIA_SEMANA      INT,            -- 1=Monday … 7=Sunday
    NOM_MES         VARCHAR(20),
    NOM_DIA         VARCHAR(20),
    ES_FIN_SEMANA   BIT             DEFAULT 0,
    ES_FERIADO      BIT             DEFAULT 0,
    PERIODO         VARCHAR(7),     -- "YYYY-MM"
    CONSTRAINT pk_dim_calendario PRIMARY KEY (FECHA)
);
