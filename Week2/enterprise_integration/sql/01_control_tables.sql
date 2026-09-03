CREATE TABLE dbo.ETL_Watermark (
    SourceSystem   NVARCHAR(100)  NOT NULL,
    EntityName     NVARCHAR(100)  NOT NULL,
    WatermarkValue NVARCHAR(100)  NOT NULL,
    LastRunUtc     DATETIME2(3)   NOT NULL,
    RowsExtracted  BIGINT         NULL,
    Status         NVARCHAR(20)   NOT NULL,
    CONSTRAINT PK_ETL_Watermark PRIMARY KEY (SourceSystem, EntityName)
);

INSERT INTO dbo.ETL_Watermark (SourceSystem, EntityName, WatermarkValue, LastRunUtc, Status)
VALUES ('DummyJSON', 'Carts', '0', SYSUTCDATETIME(), 'Success');    