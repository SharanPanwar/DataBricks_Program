-- Q4 · Aggregation and NULL behaviour
--
-- Question: some customers have no credit_limit. Show how COUNT, AVG and SUM
-- each treat those NULLs, and produce the figure a business user actually means
-- when they ask for "average credit limit".
--
-- Proves: COUNT(col) skips NULLs, AVG ignores them in the denominator, and
-- COALESCE(col, 0) changes the business meaning of the average.

SELECT
    COUNT(*)                                    AS all_customers,
    COUNT(credit_limit)                         AS customers_with_limit,
    COUNT(*) - COUNT(credit_limit)              AS null_credit_limits,
    AVG(credit_limit)                           AS avg_ignoring_nulls,
    AVG(COALESCE(credit_limit, 0))              AS avg_treating_null_as_zero,
    SUM(credit_limit)                           AS sum_ignoring_nulls,
    SUM(COALESCE(credit_limit, 0))              AS sum_with_coalesce
FROM customers;

-- The question to ask the business is which they mean. "Average limit across
-- customers who have one" and "average limit across all customers, counting
-- unset as zero" are different numbers and both are defensible. Guessing is not.
--
-- Also worth knowing: NULL = NULL is not true, it is NULL. Use IS NULL.
