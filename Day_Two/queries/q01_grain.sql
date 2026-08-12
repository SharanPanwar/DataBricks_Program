-- Q1 · Grain
--
-- Question: what is the grain of the orders table? Prove it with a query rather
-- than asserting it, and show how many order_ids have more than one row.
--
-- Proves: orders is one row per *version*, not one row per order_id. Any query
-- that treats order_id as unique will double-count corrected orders.

SELECT
    COUNT(*)                                              AS total_rows,
    COUNT(DISTINCT order_id)                              AS distinct_order_ids,
    COUNT(*) - COUNT(DISTINCT order_id)                   AS surplus_rows,
    CAST(COUNT(*) AS REAL) / COUNT(DISTINCT order_id)     AS rows_per_order_id
FROM orders;
