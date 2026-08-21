CREATE VIEW dbo.vw_CartProductSummary AS
SELECT cart_id,
       user_id,
       COUNT(*) AS product_lines,
       SUM(quantity) AS total_units,
       SUM(line_total) AS revenue
FROM dbo.CartProducts
WHERE is_active = 1
GROUP BY cart_id, user_id;