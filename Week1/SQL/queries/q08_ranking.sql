-- Q8 · ROW_NUMBER versus RANK versus DENSE_RANK
--
-- Question: top 3 products by quantity sold in each region. Show all three
-- ranking functions side by side so the difference at a tie is visible.
--
-- Proves: ROW_NUMBER, RANK, and DENSE_RANK behave differently at ties, so
-- "top 3" is ambiguous until you pick one.

WITH latest_orders AS (
    SELECT order_id, customer_id
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
regional_sales AS (
    SELECT
        c.region,
        p.product_id,
        p.product_name,
        SUM(i.quantity) AS total_qty
    FROM latest_orders AS lo
    JOIN order_items AS i  ON i.order_id = lo.order_id
    JOIN customers AS c    ON c.customer_id = lo.customer_id
    JOIN products AS p     ON p.product_id = i.product_id
    GROUP BY c.region, p.product_id, p.product_name
),
ranked AS (
    SELECT
        region,
        product_id,
        product_name,
        total_qty,
        ROW_NUMBER() OVER (PARTITION BY region ORDER BY total_qty DESC) AS row_num,
        RANK()       OVER (PARTITION BY region ORDER BY total_qty DESC) AS rnk,
        DENSE_RANK() OVER (PARTITION BY region ORDER BY total_qty DESC) AS dense_rnk
    FROM regional_sales
)
SELECT region, product_id, product_name, total_qty, row_num, rnk, dense_rnk
FROM ranked
WHERE rnk <= 3
ORDER BY region, rnk, product_id;

--   ROW_NUMBER  1,2,3,4  — always unique, arbitrary at a tie unless you break it
--   RANK        1,2,2,4  — ties share a rank, then it skips
--   DENSE_RANK  1,2,2,3  — ties share a rank, no gap
--
-- "Top 3" is ambiguous when there are ties. Ask which behaviour is wanted before
-- you pick one. Choosing ROW_NUMBER silently drops a genuinely tied product.
