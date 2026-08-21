# Day 2 · Lab 2 — twelve queries on a sales schema

Twelve queries against a deliberately awkward schema. Each one targets something
that comes up in real work and gets asked in technical screens.

Time: the afternoon workshop, 13:30–16:15. Demo at 16:15.

---

## Setup

```bash
python seed.py --small        # 5,000 orders — use this while you work
python run.py queries/q01_grain.sql
python run.py --all           # run every query in order
python -m pytest              # the tests that grade your answers
```

Once, near the end, build the full database and run the benchmark — the headline
number for Q12 only shows up at scale:

```bash
python seed.py                # 50,000 orders, takes about 20 seconds
python bench.py --db sales.db
```

No server, no Docker, no credentials. SQLite has window functions, CTEs and
`EXPLAIN QUERY PLAN`, which is everything this lab needs. The patterns transfer
directly to Databricks SQL, Postgres and T-SQL — section "Dialect notes" below
lists the handful of differences.

## The schema

Five tables, shaped like a landing zone rather than a textbook:

| Table | Grain | The catch |
|---|---|---|
| `customers` | one row per customer | ~19% have a NULL `credit_limit`; 40 have never ordered |
| `products` | one row per product | some discontinued |
| `price_history` | one row per product per validity window | prices change over time — Q11 depends on this |
| `orders` | **one row per order *version*** | no PK on `order_id`; corrections arrive as later rows |
| `order_items` | one row per line | one-to-many against orders — this is what makes Q3 possible |

## The twelve queries

| # | Topic | What it teaches |
|---|---|---|
| 1 | Grain | Prove the grain, do not assume it. `orders` is not one row per order |
| 2 | INNER vs LEFT join | The anti-join, and how a `WHERE` on the right table silently undoes a `LEFT JOIN` |
| 3 | The fan-out trap | Joining one-to-many inflates `COUNT(*)` on the one-side; aggregate the many-side first |
| 4 | NULL and aggregates | `COUNT(*)` vs `COUNT(col)`, why `AVG` ignoring NULL is a different number |
| 5 | HAVING vs WHERE | Row filters before grouping, group filters after |
| 6 | CTEs | Rewrite nested subqueries so a reviewer can read them top-down |
| 7 | Deduplication | `ROW_NUMBER` to keep the latest per key — the most reused pattern in data engineering |
| 8 | ROW_NUMBER / RANK / DENSE_RANK | What each does at a tie, and why "top 3" is ambiguous |
| 9 | LAG | Month-over-month change, and why the first month is honestly NULL |
| 10 | Running totals and framing | `ROWS` vs `RANGE`, and why you should always write the frame out |
| 11 | Point-in-time lookup | Price as at the order date, not today's price. The one most people get wrong |
| 12 | Rewriting a correlated subquery | Measure the speed-up — and discover that the obvious rewrite is wrong |

## Q12 is the one to spend time on

It contains two separate traps and only one of them is about speed.

**The performance trap.** The correlated subquery runs once per outer row. On the
full database it takes around 87 seconds; the window version takes under a tenth
of a second. Run `bench.py` and put your own numbers in the pull request — do not
quote these.

**The correctness trap, which matters more.** The obvious rewrite filters to
shipped orders and then applies the window. That is faster and it is wrong,
because `WHERE` is evaluated *before* window functions, so the window never sees
the non-shipped rows. On the seeded data it agrees with the correct answer on
362 rows out of 3,265.

The logical order of evaluation, which is not the order you write it in:

```
FROM → WHERE → GROUP BY → HAVING → WINDOW → SELECT → ORDER BY → LIMIT
```

If you need to filter before a window sees the data, or filter on a window's
result, you need a second query level. There is a test that fails if someone
"simplifies" this later.

## Reading an execution plan

```bash
python run.py queries/q12_correlated_rewrite.sql --plan
```

SQLite's plan is short. Read it bottom-up — the deepest line runs first. The
three things to look for are the same in every engine:

- **A scan where you expected a search.** `SCAN orders` means every row was read.
- **A correlated scalar subquery.** That line means "this runs once per row".
- **A temporary B-tree for ORDER BY or GROUP BY.** The engine had to sort because no index gave it the order for free.

In Postgres this is `EXPLAIN (ANALYZE, BUFFERS)`; in Databricks it is `EXPLAIN`
or the Spark UI. Different output, identical question: what is it actually doing,
and how many rows does it think it will touch?

## Definition of done

- [ ] `python -m pytest` passes — 19 tests
- [ ] Every query runs via `python run.py --all` with no errors
- [ ] You have run `bench.py` on the full database and recorded your own timings
- [ ] You can explain, out loud, why the filtered-first window rewrite is wrong
- [ ] Every query has a comment saying what it proves, not just what it does
- [ ] Opened as a pull request, reviewed by a peer, comments addressed, merged

## Pull request checklist

Reviewers: do not approve until you can answer yes to all of these.

- [ ] Can I tell the grain of every result set from reading the query?
- [ ] Is there a `LEFT JOIN` anywhere with a condition on the right table in `WHERE`?
- [ ] Does any `COUNT(*)` sit on the one-side of a one-to-many join?
- [ ] Is every window frame written out explicitly rather than left to the default?
- [ ] For Q11, does the join use both `valid_from` and `valid_to`, and is `valid_to` treated as exclusive?
- [ ] Did the author measure Q12 rather than assert it?

## Dialect notes

Everything here is standard SQL and runs on Databricks, Postgres and SQL Server
with these adjustments:

| SQLite (here) | Databricks SQL | Postgres |
|---|---|---|
| `substr(order_date, 1, 7)` | `date_format(order_date, 'yyyy-MM')` | `to_char(order_date, 'YYYY-MM')` |
| dates stored as TEXT | real `DATE` type | real `DATE` type |
| `EXPLAIN QUERY PLAN` | `EXPLAIN` or the Spark UI | `EXPLAIN (ANALYZE, BUFFERS)` |
| `QUALIFY` not supported | `QUALIFY rn = 1` — use it, it is cleaner | not supported; use a subquery |
| indexes as here | no indexes; think partitioning, Z-order, liquid clustering | as here |

The one worth knowing before Week 2: Databricks supports `QUALIFY`, which lets
you filter on a window result without an extra query level. Q7 becomes four lines
instead of eight. It does not change the logical order of evaluation — it is
sugar over exactly the same second level.

## Stretch, if you finish early

Do not start these until the definition of done is met.

1. Add a thirteenth query: customers whose order count fell for three consecutive months. `LAG` twice, or a window over a window.
2. Rewrite Q11 as an `AS OF`-style join and compare the plan.
3. Add an index that makes Q8 faster and prove it with `bench.py`. Then explain why it helps.
4. Find a query in this set whose result changes if you swap `ROWS` for `RANGE`, and write the test that catches it.
