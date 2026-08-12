-- Q3 · The fan-out trap
--
-- Question: one row per order joined to many rows per order_item. Show the
-- inflated figure a naive join produces, then produce the correct one.
--
-- Proves: joining one-to-many inflates COUNT(*) on the one side, but summing
-- the many side is unaffected. Aggregate the many side first for correct counts.

WITH latest_orders AS (
    SELECT *
    FROM (
        SELECT
            o.*,
            ROW_NUMBER() OVER (
                PARTITION BY o.order_id
                ORDER BY o.updated_at DESC, o.order_row_id DESC
            ) AS rn
        FROM orders AS o
    )
    WHERE rn = 1
),
wrong AS (
    SELECT
        lo.status,
        COUNT(*)         AS inflated_count,
        SUM(oi.quantity) AS qty_wrong
    FROM latest_orders AS lo
    JOIN order_items AS oi ON oi.order_id = lo.order_id
    GROUP BY lo.status
),
correct AS (
    SELECT
        lo.status,
        COUNT(*)           AS correct_count,
        SUM(ip.total_qty)  AS qty_right
    FROM latest_orders AS lo
    JOIN (
        SELECT order_id, SUM(quantity) AS total_qty
        FROM order_items
        GROUP BY order_id
    ) AS ip ON ip.order_id = lo.order_id
    GROUP BY lo.status
)
SELECT
    w.status,
    w.inflated_count,
    c.correct_count,
    w.inflated_count - c.correct_count AS added_by_fanout,
    w.qty_wrong,
    c.qty_right
FROM wrong AS w
JOIN correct AS c ON c.status = w.status
ORDER BY w.status;

-- Note that total_quantity is identical in both. Summing the many-side is fine.
-- It is COUNT(*) and any aggregate over the ONE-side that get inflated.
