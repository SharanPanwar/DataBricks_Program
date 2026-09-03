CREATE TABLE dbo.stg_CartProducts (
    cart_id         BIGINT         NOT NULL,
    user_id         BIGINT         NULL,
    product_id      BIGINT         NULL,
    product_title   NVARCHAR(256)  NULL,
    quantity        INT            NULL,
    price           DECIMAL(18,4)  NULL,
    line_total      DECIMAL(18,4)  NULL,
    cart_total      DECIMAL(18,4)  NULL,
    ingest_ts       DATETIME2(3)   NOT NULL DEFAULT SYSUTCDATETIME(),
    source_file     NVARCHAR(500)  NULL
);