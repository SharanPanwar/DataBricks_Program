-- Q12 · Rewrite a slow correlated subquery, and measure the improvement
--
-- Question: for every SHIPPED order, how many orders had that customer placed
-- in total (any status) up to and including that date? The correlated version
-- below is correct and slow. Rewrite it with a window function, prove the
-- answers are identical, and measure both with bench.py.
--
-- Proves: WHERE runs before window functions, so the filter to shipped must
-- happen in an outer query after the window sees all rows. Use RANGE for
-- same-day orders.

WITH counted AS (
    SELECT
        order_row_id,
        order_id,
        customer_id,
        order_date,
        status,
        COUNT(*) OVER (
            PARTITION BY customer_id
            ORDER BY order_date
            RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS orders_to_date
    FROM orders
)
SELECT
    order_id,
    customer_id,
    order_date,
    orders_to_date
FROM counted
WHERE status = 'shipped'
ORDER BY order_row_id;

-- The logical order of evaluation, which is not the order you write it in:
--
--   FROM -> WHERE -> GROUP BY -> HAVING -> WINDOW -> SELECT -> ORDER BY -> LIMIT
--
-- WHERE runs before window functions. HAVING runs before window functions.
-- If you need to filter on a window result, or filter after one, you need a
-- second query level. That is not a limitation, it is the definition.

-- RANGE, not ROWS, is also deliberate. The question says "up to and including
-- that date". With ROWS, two orders on the same date get different counts
-- depending on their arbitrary order within the day. RANGE groups tied ORDER BY
-- values together, which is what "up to and including that date" means.
