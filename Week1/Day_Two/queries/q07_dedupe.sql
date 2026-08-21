-- Q7 · Deduplicate: keep the latest record per key
--
-- Question: orders contains correction rows. Produce exactly one row per
-- order_id, keeping the latest updated_at, and prove the output grain is right.
--
-- Proves: ROW_NUMBER with a tie-breaker gives exactly one row per business key.

WITH ranked AS (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY o.order_id
            ORDER BY o.updated_at DESC, o.order_row_id DESC
        ) AS rn
    FROM orders AS o
)
SELECT
    order_id,
    customer_id,
    order_date,
    status,
    updated_at
FROM ranked
WHERE rn = 1
LIMIT 25;

-- Proof of grain — run this and expect zero rows back:
--
--   WITH ranked AS (...same as above...),
--        deduped AS (SELECT * FROM ranked WHERE rn = 1)
--   SELECT order_id, COUNT(*) FROM deduped GROUP BY order_id HAVING COUNT(*) > 1;
--
-- Why ROW_NUMBER and not RANK: RANK returns 1 for every tied row, so a tie
-- would give you two rows back and silently reintroduce the duplicate.
-- The second ORDER BY column is not decoration — without it, ties are arbitrary
-- and your output changes between runs.
