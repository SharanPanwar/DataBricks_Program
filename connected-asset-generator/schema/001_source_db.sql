-- Connected Asset Analytics Platform — source system schema (Azure SQL)
-- Run once via: python -m asset_generator init

-- ---------------------------------------------------------------------------
-- Master / reference data
-- ---------------------------------------------------------------------------

IF OBJECT_ID(N'dbo.domains', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.domains (
        domain_id       NVARCHAR(32)  NOT NULL,
        name            NVARCHAR(64)  NOT NULL,
        description     NVARCHAR(256) NULL,
        created_at      DATETIME2(3)  NOT NULL CONSTRAINT DF_domains_created_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_domains PRIMARY KEY (domain_id)
    );
END;
GO

IF OBJECT_ID(N'dbo.locations', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.locations (
        location_id     NVARCHAR(32)  NOT NULL,
        location_name   NVARCHAR(128) NOT NULL,
        location_type   NVARCHAR(64)  NOT NULL,
        city            NVARCHAR(64)  NOT NULL,
        state           NVARCHAR(64)  NULL,
        country         NVARCHAR(64)  NOT NULL,
        latitude        DECIMAL(9, 6) NULL,
        longitude       DECIMAL(9, 6) NULL,
        manager         NVARCHAR(32)  NULL,
        status          NVARCHAR(16)  NOT NULL CONSTRAINT DF_locations_status DEFAULT N'ACTIVE',
        created_at      DATETIME2(3)  NOT NULL CONSTRAINT DF_locations_created_at DEFAULT SYSUTCDATETIME(),
        updated_at      DATETIME2(3)  NOT NULL CONSTRAINT DF_locations_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_locations PRIMARY KEY (location_id)
    );
END;
GO

IF OBJECT_ID(N'dbo.asset_types', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.asset_types (
        asset_type_id   NVARCHAR(32)  NOT NULL,
        domain_id       NVARCHAR(32)  NOT NULL,
        name            NVARCHAR(64)  NOT NULL,
        description     NVARCHAR(256) NULL,
        CONSTRAINT PK_asset_types PRIMARY KEY (asset_type_id),
        CONSTRAINT FK_asset_types_domain FOREIGN KEY (domain_id) REFERENCES dbo.domains (domain_id)
    );
END;
GO

IF OBJECT_ID(N'dbo.operators', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.operators (
        operator_id           NVARCHAR(32)  NOT NULL,
        name                  NVARCHAR(128) NOT NULL,
        role                  NVARCHAR(64)  NOT NULL,
        department            NVARCHAR(64)  NOT NULL,
        hire_date             DATE          NOT NULL,
        certification_level   NVARCHAR(32)  NULL,
        status                NVARCHAR(16)  NOT NULL CONSTRAINT DF_operators_status DEFAULT N'ACTIVE',
        created_at            DATETIME2(3)  NOT NULL CONSTRAINT DF_operators_created_at DEFAULT SYSUTCDATETIME(),
        updated_at            DATETIME2(3)  NOT NULL CONSTRAINT DF_operators_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_operators PRIMARY KEY (operator_id)
    );
END;
GO

IF OBJECT_ID(N'dbo.assets', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.assets (
        asset_id                  NVARCHAR(32)   NOT NULL,
        domain_id                 NVARCHAR(32)   NOT NULL,
        asset_type_id             NVARCHAR(32)   NOT NULL,
        manufacturer              NVARCHAR(64)   NOT NULL,
        model                     NVARCHAR(64)   NOT NULL,
        serial_number             NVARCHAR(64)   NOT NULL,
        location_id               NVARCHAR(32)   NOT NULL,
        operator_id               NVARCHAR(32)   NULL,
        installation_date         DATE           NOT NULL,
        purchase_cost             DECIMAL(12, 2) NULL,
        status                    NVARCHAR(16)   NOT NULL CONSTRAINT DF_assets_status DEFAULT N'ACTIVE',
        expected_lifespan_years   INT            NULL,
        created_at                DATETIME2(3)   NOT NULL CONSTRAINT DF_assets_created_at DEFAULT SYSUTCDATETIME(),
        updated_at                DATETIME2(3)   NOT NULL CONSTRAINT DF_assets_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_assets PRIMARY KEY (asset_id),
        CONSTRAINT FK_assets_domain FOREIGN KEY (domain_id) REFERENCES dbo.domains (domain_id),
        CONSTRAINT FK_assets_asset_type FOREIGN KEY (asset_type_id) REFERENCES dbo.asset_types (asset_type_id),
        CONSTRAINT FK_assets_location FOREIGN KEY (location_id) REFERENCES dbo.locations (location_id),
        CONSTRAINT FK_assets_operator FOREIGN KEY (operator_id) REFERENCES dbo.operators (operator_id)
    );

    CREATE INDEX IX_assets_domain_id ON dbo.assets (domain_id);
    CREATE INDEX IX_assets_location_id ON dbo.assets (location_id);
END;
GO

-- Per-asset runtime state (carried forward day-to-day by the generator)
IF OBJECT_ID(N'dbo.asset_state', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.asset_state (
        asset_id          NVARCHAR(32)   NOT NULL,
        state             NVARCHAR(32)   NOT NULL CONSTRAINT DF_asset_state_state DEFAULT N'ACTIVE',
        battery_level     DECIMAL(5, 2)  NULL,
        fuel_level        DECIMAL(5, 2)  NULL,
        operating_hours   DECIMAL(10, 2) NOT NULL CONSTRAINT DF_asset_state_operating_hours DEFAULT 0,
        odometer          DECIMAL(12, 2) NULL,
        health_score      INT            NOT NULL CONSTRAINT DF_asset_state_health_score DEFAULT 100,
        last_maintenance  DATETIME2(3)   NULL,
        updated_at        DATETIME2(3)   NOT NULL CONSTRAINT DF_asset_state_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_asset_state PRIMARY KEY (asset_id),
        CONSTRAINT FK_asset_state_asset FOREIGN KEY (asset_id) REFERENCES dbo.assets (asset_id),
        CONSTRAINT CK_asset_state_health_score CHECK (health_score BETWEEN 0 AND 100)
    );
END;
GO

-- ---------------------------------------------------------------------------
-- Transactional / fact data
-- ---------------------------------------------------------------------------

IF OBJECT_ID(N'dbo.telemetry', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.telemetry (
        telemetry_id      NVARCHAR(32)   NOT NULL,
        asset_id          NVARCHAR(32)   NOT NULL,
        recorded_at       DATETIME2(3)   NOT NULL,
        temperature       DECIMAL(8, 3)  NULL,
        pressure          DECIMAL(8, 3)  NULL,
        vibration         DECIMAL(8, 4)  NULL,
        power_consumption DECIMAL(10, 3) NULL,
        voltage           DECIMAL(8, 3)  NULL,
        current_amps      DECIMAL(8, 3)  NULL,
        sensor_status     NVARCHAR(16)   NULL,
        batch_id          NVARCHAR(64)   NULL,
        source_created_at DATETIME2(3)   NOT NULL CONSTRAINT DF_telemetry_source_created_at DEFAULT SYSUTCDATETIME(),
        updated_at        DATETIME2(3)   NOT NULL CONSTRAINT DF_telemetry_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_telemetry PRIMARY KEY (telemetry_id),
        CONSTRAINT FK_telemetry_asset FOREIGN KEY (asset_id) REFERENCES dbo.assets (asset_id)
    );

    CREATE INDEX IX_telemetry_asset_recorded ON dbo.telemetry (asset_id, recorded_at);
    CREATE INDEX IX_telemetry_recorded_at ON dbo.telemetry (recorded_at);
    CREATE INDEX IX_telemetry_batch_id ON dbo.telemetry (batch_id);
    CREATE INDEX IX_telemetry_updated_at ON dbo.telemetry (updated_at);
END;
GO

-- Domain-specific telemetry extensions (1:1 with common telemetry row per timestamp)
IF OBJECT_ID(N'dbo.telemetry_automotive', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.telemetry_automotive (
        telemetry_id      NVARCHAR(32)   NOT NULL,
        asset_id          NVARCHAR(32)   NOT NULL,
        recorded_at       DATETIME2(3)   NOT NULL,
        battery_soc       DECIMAL(5, 2)  NULL,
        motor_temperature DECIMAL(8, 3)  NULL,
        vehicle_speed     DECIMAL(8, 3)  NULL,
        charging_status   NVARCHAR(16)   NULL,
        fuel_level        DECIMAL(5, 2)  NULL,
        CONSTRAINT PK_telemetry_automotive PRIMARY KEY (telemetry_id),
        CONSTRAINT FK_telemetry_automotive_asset FOREIGN KEY (asset_id) REFERENCES dbo.assets (asset_id)
    );
    CREATE INDEX IX_telemetry_automotive_asset_recorded ON dbo.telemetry_automotive (asset_id, recorded_at);
END;
GO

IF OBJECT_ID(N'dbo.telemetry_construction', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.telemetry_construction (
        telemetry_id       NVARCHAR(32)   NOT NULL,
        asset_id           NVARCHAR(32)   NOT NULL,
        recorded_at        DATETIME2(3)   NOT NULL,
        fuel_level         DECIMAL(5, 2)  NULL,
        hydraulic_pressure DECIMAL(10, 2) NULL,
        engine_rpm         INT            NULL,
        operating_hours    DECIMAL(10, 2) NULL,
        CONSTRAINT PK_telemetry_construction PRIMARY KEY (telemetry_id),
        CONSTRAINT FK_telemetry_construction_asset FOREIGN KEY (asset_id) REFERENCES dbo.assets (asset_id)
    );
    CREATE INDEX IX_telemetry_construction_asset_recorded ON dbo.telemetry_construction (asset_id, recorded_at);
END;
GO

IF OBJECT_ID(N'dbo.telemetry_medical', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.telemetry_medical (
        telemetry_id     NVARCHAR(32)   NOT NULL,
        asset_id         NVARCHAR(32)   NOT NULL,
        recorded_at      DATETIME2(3)   NOT NULL,
        magnetic_field   DECIMAL(10, 4) NULL,
        coolant_pressure DECIMAL(8, 3)  NULL,
        coolant_level    DECIMAL(5, 2)  NULL,
        operating_hours  DECIMAL(10, 2) NULL,
        CONSTRAINT PK_telemetry_medical PRIMARY KEY (telemetry_id),
        CONSTRAINT FK_telemetry_medical_asset FOREIGN KEY (asset_id) REFERENCES dbo.assets (asset_id)
    );
    CREATE INDEX IX_telemetry_medical_asset_recorded ON dbo.telemetry_medical (asset_id, recorded_at);
END;
GO

IF OBJECT_ID(N'dbo.telemetry_aerospace', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.telemetry_aerospace (
        telemetry_id        NVARCHAR(32)   NOT NULL,
        asset_id            NVARCHAR(32)   NOT NULL,
        recorded_at         DATETIME2(3)   NOT NULL,
        altitude            DECIMAL(10, 2) NULL,
        airspeed            DECIMAL(8, 3)  NULL,
        engine_temperature  DECIMAL(8, 3)  NULL,
        fuel_level          DECIMAL(5, 2)  NULL,
        engine_rpm          INT            NULL,
        CONSTRAINT PK_telemetry_aerospace PRIMARY KEY (telemetry_id),
        CONSTRAINT FK_telemetry_aerospace_asset FOREIGN KEY (asset_id) REFERENCES dbo.assets (asset_id)
    );
    CREATE INDEX IX_telemetry_aerospace_asset_recorded ON dbo.telemetry_aerospace (asset_id, recorded_at);
END;
GO

IF OBJECT_ID(N'dbo.telemetry_industrial', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.telemetry_industrial (
        telemetry_id   NVARCHAR(32)   NOT NULL,
        asset_id       NVARCHAR(32)   NOT NULL,
        recorded_at    DATETIME2(3)   NOT NULL,
        spindle_speed  INT            NULL,
        tool_wear      DECIMAL(5, 2)  NULL,
        cycle_count    INT            NULL,
        CONSTRAINT PK_telemetry_industrial PRIMARY KEY (telemetry_id),
        CONSTRAINT FK_telemetry_industrial_asset FOREIGN KEY (asset_id) REFERENCES dbo.assets (asset_id)
    );
    CREATE INDEX IX_telemetry_industrial_asset_recorded ON dbo.telemetry_industrial (asset_id, recorded_at);
END;
GO

IF OBJECT_ID(N'dbo.telemetry_energy', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.telemetry_energy (
        telemetry_id      NVARCHAR(32)   NOT NULL,
        asset_id          NVARCHAR(32)   NOT NULL,
        recorded_at       DATETIME2(3)   NOT NULL,
        output_power      DECIMAL(10, 3) NULL,
        wind_speed        DECIMAL(8, 3)  NULL,
        solar_irradiance  DECIMAL(10, 3) NULL,
        grid_frequency    DECIMAL(6, 3)  NULL,
        CONSTRAINT PK_telemetry_energy PRIMARY KEY (telemetry_id),
        CONSTRAINT FK_telemetry_energy_asset FOREIGN KEY (asset_id) REFERENCES dbo.assets (asset_id)
    );
    CREATE INDEX IX_telemetry_energy_asset_recorded ON dbo.telemetry_energy (asset_id, recorded_at);
END;
GO

IF OBJECT_ID(N'dbo.telemetry_agriculture', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.telemetry_agriculture (
        telemetry_id    NVARCHAR(32)   NOT NULL,
        asset_id        NVARCHAR(32)   NOT NULL,
        recorded_at     DATETIME2(3)   NOT NULL,
        soil_moisture   DECIMAL(5, 2)  NULL,
        implement_depth DECIMAL(6, 2)  NULL,
        fuel_level      DECIMAL(5, 2)  NULL,
        CONSTRAINT PK_telemetry_agriculture PRIMARY KEY (telemetry_id),
        CONSTRAINT FK_telemetry_agriculture_asset FOREIGN KEY (asset_id) REFERENCES dbo.assets (asset_id)
    );
    CREATE INDEX IX_telemetry_agriculture_asset_recorded ON dbo.telemetry_agriculture (asset_id, recorded_at);
END;
GO

IF OBJECT_ID(N'dbo.telemetry_electronics', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.telemetry_electronics (
        telemetry_id         NVARCHAR(32)   NOT NULL,
        asset_id             NVARCHAR(32)   NOT NULL,
        recorded_at          DATETIME2(3)   NOT NULL,
        cpu_usage            DECIMAL(5, 2)  NULL,
        memory_usage         DECIMAL(5, 2)  NULL,
        network_throughput   DECIMAL(12, 3) NULL,
        ups_battery_level    DECIMAL(5, 2)  NULL,
        CONSTRAINT PK_telemetry_electronics PRIMARY KEY (telemetry_id),
        CONSTRAINT FK_telemetry_electronics_asset FOREIGN KEY (asset_id) REFERENCES dbo.assets (asset_id)
    );
    CREATE INDEX IX_telemetry_electronics_asset_recorded ON dbo.telemetry_electronics (asset_id, recorded_at);
END;
GO

IF OBJECT_ID(N'dbo.events', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.events (
        event_id              NVARCHAR(32)  NOT NULL,
        asset_id              NVARCHAR(32)  NOT NULL,
        occurred_at           DATETIME2(3)  NOT NULL,
        event_type            NVARCHAR(64)  NOT NULL,
        severity              NVARCHAR(16)  NOT NULL,
        error_code            NVARCHAR(32)  NULL,
        description           NVARCHAR(512) NULL,
        resolved              BIT           NOT NULL CONSTRAINT DF_events_resolved DEFAULT 0,
        resolution_timestamp  DATETIME2(3)  NULL,
        batch_id              NVARCHAR(64)  NULL,
        source_created_at     DATETIME2(3)  NOT NULL CONSTRAINT DF_events_source_created_at DEFAULT SYSUTCDATETIME(),
        updated_at            DATETIME2(3)  NOT NULL CONSTRAINT DF_events_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_events PRIMARY KEY (event_id),
        CONSTRAINT FK_events_asset FOREIGN KEY (asset_id) REFERENCES dbo.assets (asset_id)
    );

    CREATE INDEX IX_events_asset_occurred ON dbo.events (asset_id, occurred_at);
    CREATE INDEX IX_events_severity ON dbo.events (severity);
    CREATE INDEX IX_events_updated_at ON dbo.events (updated_at);
END;
GO

IF OBJECT_ID(N'dbo.maintenance', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.maintenance (
        maintenance_id    NVARCHAR(32)   NOT NULL,
        asset_id          NVARCHAR(32)   NOT NULL,
        maintenance_date  DATETIME2(3)   NOT NULL,
        maintenance_type  NVARCHAR(32)   NOT NULL,
        reason            NVARCHAR(128)  NOT NULL,
        technician_id     NVARCHAR(32)   NULL,
        parts_replaced    NVARCHAR(256)  NULL,
        labor_hours       DECIMAL(6, 2)  NULL,
        parts_cost        DECIMAL(10, 2) NULL,
        labor_cost        DECIMAL(10, 2) NULL,
        total_cost        DECIMAL(10, 2) NULL,
        status            NVARCHAR(16)   NOT NULL CONSTRAINT DF_maintenance_status DEFAULT N'COMPLETED',
        batch_id          NVARCHAR(64)   NULL,
        source_created_at DATETIME2(3)   NOT NULL CONSTRAINT DF_maintenance_source_created_at DEFAULT SYSUTCDATETIME(),
        updated_at        DATETIME2(3)   NOT NULL CONSTRAINT DF_maintenance_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_maintenance PRIMARY KEY (maintenance_id),
        CONSTRAINT FK_maintenance_asset FOREIGN KEY (asset_id) REFERENCES dbo.assets (asset_id)
    );

    CREATE INDEX IX_maintenance_asset_date ON dbo.maintenance (asset_id, maintenance_date);
    CREATE INDEX IX_maintenance_updated_at ON dbo.maintenance (updated_at);
END;
GO
