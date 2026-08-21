-- Q11 · Point-in-time lookup
--
-- Question: value each order using the price that was in force ON THE ORDER
-- DATE, not the price today. Show what using today's price would have cost you.
--
-- Proves: point-in-time joins need both valid_from and valid_to (exclusive);
-- joining on product_id alone misprices historical orders.

WITH latest_orders AS (
    SELECT order_id, order_date
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
pit AS (
    SELECT SUM(i.quantity * ph.unit_price) AS revenue
    FROM latest_orders AS lo
    JOIN order_items AS i ON i.order_id = lo.order_id
    JOIN price_history AS ph
        ON ph.product_id = i.product_id
       AND lo.order_date >= ph.valid_from
       AND lo.order_date <  ph.valid_to
),
today AS (
    SELECT SUM(i.quantity * ph.unit_price) AS revenue
    FROM latest_orders AS lo
    JOIN order_items AS i ON i.order_id = lo.order_id
    JOIN price_history AS ph
        ON ph.product_id = i.product_id
       AND ph.valid_to = '9999-12-31'
)
SELECT
    pit.revenue                         AS pit_revenue,
    today.revenue                       AS today_revenue,
    today.revenue - pit.revenue         AS overstatement,
    (SELECT COUNT(*) FROM order_items)  AS priced_lines
FROM pit, today;

-- Two checks worth running before you trust this:
--   1. priced_lines should equal the number of order_item rows for latest orders.
--      If it is lower, some order dates fall outside every validity window and
--      the INNER join has silently dropped them.
--   2. No order line should match two price rows. If the count is higher than
--      expected, your validity windows overlap and you have a fan-out.
