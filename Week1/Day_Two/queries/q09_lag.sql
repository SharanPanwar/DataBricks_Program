-- Q9 · LAG — month-over-month change
--
-- Question: monthly shipped order counts, with the previous month's figure and
-- the percentage change. Handle the first month, which has no previous value.
--
-- Proves: LAG honestly returns NULL for the first row; do not COALESCE to zero.

WITH monthly AS (
    SELECT
        substr(order_date, 1, 7) AS month,
        COUNT(*)                 AS orders
    FROM orders
    WHERE status = 'shipped'
    GROUP BY substr(order_date, 1, 7)
)
SELECT
    month,
    orders,
    LAG(orders) OVER (ORDER BY month) AS prev_orders,
    orders - LAG(orders) OVER (ORDER BY month) AS change,
    ROUND(
        100.0 * (orders - LAG(orders) OVER (ORDER BY month))
        / LAG(orders) OVER (ORDER BY month),
        2
    ) AS pct_change
FROM monthly
ORDER BY month;

-- LAG returns NULL for the first row of each partition. Returning NULL is the
-- honest answer — do not COALESCE it to zero, which would report a 100% drop
-- that never happened.
--
-- LEAD is the same function looking forward. LAG(orders, 3) looks back three rows.
