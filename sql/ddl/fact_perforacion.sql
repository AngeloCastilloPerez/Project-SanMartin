-- =============================================================================
-- DDL: fact_perforacion
-- Description: Drilling (perforación) fact table
-- =============================================================================

CREATE TABLE IF NOT EXISTS fact_perforacion (
    PERF_ID         BIGINT          NOT NULL IDENTITY(1,1),
    FECHA           DATE            NOT NULL,
    EQUIPO_ID       VARCHAR(20)     NOT NULL,
    MINA_ID         VARCHAR(20),
    TURNO           VARCHAR(10),
    METROS_PERF     DECIMAL(10, 2),
    HORAS_PERF      DECIMAL(10, 2),
    MTS_HRS         DECIMAL(10, 4),                 -- Metros / Horas
    TIPO_ROCA       VARCHAR(50),
    execution_id    VARCHAR(100),
    load_ts         DATETIME2       DEFAULT GETUTCDATE(),
    CONSTRAINT pk_fact_perforacion PRIMARY KEY (PERF_ID),
    CONSTRAINT fk_perf_equipo  FOREIGN KEY (EQUIPO_ID) REFERENCES dim_equipos (EQUIPO_ID),
    CONSTRAINT fk_perf_fecha   FOREIGN KEY (FECHA)     REFERENCES dim_calendario (FECHA),
    CONSTRAINT fk_perf_mina    FOREIGN KEY (MINA_ID)   REFERENCES dim_mina (MINA_ID)
);

CREATE INDEX IF NOT EXISTS idx_fact_perf_fecha  ON fact_perforacion (FECHA);
CREATE INDEX IF NOT EXISTS idx_fact_perf_equipo ON fact_perforacion (EQUIPO_ID);
