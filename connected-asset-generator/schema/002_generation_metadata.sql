-- Generation metadata and state transition audit tables

IF OBJECT_ID(N'dbo.generation_batches', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.generation_batches (
        batch_id              NVARCHAR(64)  NOT NULL,
        batch_date            DATE          NOT NULL,
        profile               NVARCHAR(16)  NOT NULL,
        status                NVARCHAR(16)  NOT NULL CONSTRAINT DF_generation_batches_status DEFAULT N'COMPLETED',
        telemetry_rows        INT           NOT NULL CONSTRAINT DF_generation_batches_telemetry DEFAULT 0,
        event_rows            INT           NOT NULL CONSTRAINT DF_generation_batches_events DEFAULT 0,
        maintenance_rows      INT           NOT NULL CONSTRAINT DF_generation_batches_maintenance DEFAULT 0,
        asset_mutations       INT           NOT NULL CONSTRAINT DF_generation_batches_asset_mutations DEFAULT 0,
        source_system         NVARCHAR(64)  NOT NULL CONSTRAINT DF_generation_batches_source DEFAULT N'connected_asset_platform',
        generated_at          DATETIME2(3)  NOT NULL CONSTRAINT DF_generation_batches_generated_at DEFAULT SYSUTCDATETIME(),
        completed_at          DATETIME2(3)  NULL,
        error_message         NVARCHAR(MAX) NULL,
        CONSTRAINT PK_generation_batches PRIMARY KEY (batch_id)
    );

    CREATE INDEX IX_generation_batches_batch_date ON dbo.generation_batches (batch_date);
END;
GO

IF OBJECT_ID(N'dbo.asset_state_history', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.asset_state_history (
        history_id        BIGINT IDENTITY(1, 1) NOT NULL,
        asset_id          NVARCHAR(32)          NOT NULL,
        previous_state    NVARCHAR(32)          NULL,
        new_state         NVARCHAR(32)          NOT NULL,
        reason            NVARCHAR(128)         NULL,
        batch_id          NVARCHAR(64)          NULL,
        transitioned_at   DATETIME2(3)          NOT NULL CONSTRAINT DF_asset_state_history_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_asset_state_history PRIMARY KEY (history_id),
        CONSTRAINT FK_asset_state_history_asset FOREIGN KEY (asset_id) REFERENCES dbo.assets (asset_id)
    );

    CREATE INDEX IX_asset_state_history_asset ON dbo.asset_state_history (asset_id, transitioned_at);
END;
GO
