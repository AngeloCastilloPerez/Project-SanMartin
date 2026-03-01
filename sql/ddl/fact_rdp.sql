-- =============================================================================
-- DDL: fact_rdp
-- Description: RDP (Rendimiento Diario de Producción) fact table
--              Contains production KPIs per equipment per day
-- =============================================================================

CREATE TABLE IF NOT EXISTS fact_rdp (
    RDP_ID          BIGINT          NOT NULL IDENTITY(1,1),
    FECHA           DATE            NOT NULL,
    EQUIPO_ID       VARCHAR(20)     NOT NULL,
    MINA_ID         VARCHAR(20),
    ACTIVIDAD_ID    VARCHAR(20),
    TURNO           VARCHAR(10),    -- DIA | NOCHE
    HM              DECIMAL(10, 2),                 -- Horas de Movimiento
    HORAS           DECIMAL(10, 2),                 -- Total horas
    VIAJES          INT,
    METROS          DECIMAL(10, 2),
    TONELAJE        DECIMAL(14, 2),
    DISTANCIA       DECIMAL(10, 2),
    -- Derived KPI columns (computed in nb_work_fact_rdp)
    V_HR            DECIMAL(10, 4),                 -- Viajes / HM
    MTS_HRS         DECIMAL(10, 4),                 -- Metros / Horas
    TN_DIST         DECIMAL(16, 4),                 -- Tonelaje × Distancia
    TN_VJ           DECIMAL(10, 4),                 -- Tonelaje / Viaje
    execution_id    VARCHAR(100),
    load_ts         DATETIME2       DEFAULT GETUTCDATE(),
    CONSTRAINT pk_fact_rdp PRIMARY KEY (RDP_ID),
    CONSTRAINT fk_fact_rdp_equipo     FOREIGN KEY (EQUIPO_ID)    REFERENCES dim_equipos (EQUIPO_ID),
    CONSTRAINT fk_fact_rdp_fecha      FOREIGN KEY (FECHA)        REFERENCES dim_calendario (FECHA),
    CONSTRAINT fk_fact_rdp_mina       FOREIGN KEY (MINA_ID)      REFERENCES dim_mina (MINA_ID),
    CONSTRAINT fk_fact_rdp_actividad  FOREIGN KEY (ACTIVIDAD_ID) REFERENCES dim_actividad (ACTIVIDAD_ID)
);

CREATE INDEX IF NOT EXISTS idx_fact_rdp_fecha     ON fact_rdp (FECHA);
CREATE INDEX IF NOT EXISTS idx_fact_rdp_equipo    ON fact_rdp (EQUIPO_ID);
CREATE INDEX IF NOT EXISTS idx_fact_rdp_periodo   ON fact_rdp (FECHA, EQUIPO_ID);
