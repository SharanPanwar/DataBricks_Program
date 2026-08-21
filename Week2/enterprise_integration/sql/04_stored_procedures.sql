CREATE PROCEDURE dbo.usp_MergeCartProducts
AS
BEGIN
    SET NOCOUNT ON;

    MERGE dbo.CartProducts AS t
    USING (
        SELECT cart_id, product_id, user_id, product_title,
               quantity, price, line_total, cart_total,
               MAX(ingest_ts) AS last_updated
        FROM dbo.stg_CartProducts
        GROUP BY cart_id, product_id, user_id, product_title,
                 quantity, price, line_total, cart_total
    ) AS s
    ON t.cart_id = s.cart_id AND t.product_id = s.product_id
    WHEN MATCHED THEN
        UPDATE SET user_id = s.user_id,
                   product_title = s.product_title,
                   quantity = s.quantity,
                   price = s.price,
                   line_total = s.line_total,
                   cart_total = s.cart_total,
                   last_updated = s.last_updated
    WHEN NOT MATCHED THEN
        INSERT (cart_id, product_id, user_id, product_title,
                quantity, price, line_total, cart_total, last_updated)
        VALUES (s.cart_id, s.product_id, s.user_id, s.product_title,
                s.quantity, s.price, s.line_total, s.cart_total, s.last_updated);
END;
GO

CREATE PROCEDURE dbo.usp_UpdateWatermark
    @SourceSystem   NVARCHAR(100),
    @EntityName     NVARCHAR(100),
    @NewWatermark   NVARCHAR(100),
    @RowsExtracted  BIGINT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.ETL_Watermark
    SET WatermarkValue = @NewWatermark,
        LastRunUtc     = SYSUTCDATETIME(),
        RowsExtracted  = @RowsExtracted,
        Status         = 'Success'
    WHERE SourceSystem = @SourceSystem
      AND EntityName   = @EntityName;
END;