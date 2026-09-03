-- Q2 · INNER versus LEFT join
--
-- Question: how many customers have never placed an order? Show why an INNER
-- join cannot answer this and a LEFT join can.
--
-- Proves: a LEFT JOIN keeps unmatched left-side rows; filtering the right table
-- in WHERE (not ON) is what makes the anti-join work here.

SELECT
    c.customer_id,
    1 AS no_orders,
    c.customer_name,
    c.region
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.customer_id
WHERE o.order_row_id IS NULL;

-- Compare: this looks similar and is wrong. Putting a condition on the right
-- table in WHERE (rather than in ON) discards the unmatched rows first.
--
--   SELECT COUNT(*) FROM customers c
--   LEFT JOIN orders o ON o.customer_id = c.customer_id
--   WHERE o.status = 'shipped';       -- now an INNER join in all but name
