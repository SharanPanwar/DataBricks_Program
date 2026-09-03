CREATE TABLE dbo.CartProducts (
    cart_id         BIGINT         NOT NULL,
    product_id      BIGINT         NOT NULL,
    user_id         BIGINT         NULL,
    product_title   NVARCHAR(256)  NULL,
    quantity        INT            NULL,
    price           DECIMAL(18,4)  NULL,
    line_total      DECIMAL(18,4)  NULL,
    cart_total      DECIMAL(18,4)  NULL,
    last_updated    DATETIME2(3)   NOT NULL,
    is_active       BIT            NOT NULL DEFAULT 1,
    CONSTRAINT PK_CartProducts PRIMARY KEY (cart_id, product_id)
);