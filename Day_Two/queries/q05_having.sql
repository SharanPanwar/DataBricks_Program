-- Q5 · HAVING versus WHERE
--
-- Question: for shipped orders only, list regions with more than 150 orders,
-- ordered by order count. Use WHERE and HAVING correctly and explain in a
-- comment why each clause is where it is.
--
-- Proves: WHERE filters rows before grouping; HAVING filters groups after.

SELECT
    c.region,
    COUNT(*)                        AS shipped_orders,
    COUNT(DISTINCT o.customer_id)   AS distinct_customers
FROM orders AS o
JOIN customers AS c ON c.customer_id = o.customer_id
WHERE o.status = 'shipped'          -- row filter: only shipped orders enter the aggregation
GROUP BY c.region
HAVING COUNT(*) > 150               -- group filter: only regions above the threshold survive
ORDER BY shipped_orders DESC;
