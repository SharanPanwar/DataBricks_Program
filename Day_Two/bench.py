"""Measure the correlated subquery against its rewrites.

    python bench.py                 # against sales.db
    python bench.py --repeat 3      # average of three runs

Q12 asks you to measure the improvement rather than assert it. This is the
harness. Run it, put the numbers in your pull request, and be ready to say why
the fast version is fast — "it uses a window function" is not an answer, it is
a restatement.
"""

from __future__ import annotations

import argparse
import sqlite3
import time
from pathlib import Path

DB = Path(__file__).parent / "sales.db"

CORRELATED = """
SELECT
    o.order_id,
    o.customer_id,
    o.order_date,
    (SELECT COUNT(*)
       FROM orders AS o2
      WHERE o2.customer_id = o.customer_id
        AND o2.order_date <= o.order_date) AS orders_to_date
FROM orders AS o
WHERE o.status = 'shipped'
"""

SELF_JOIN = """
SELECT
    o.order_id,
    o.customer_id,
    o.order_date,
    COUNT(*) AS orders_to_date
FROM orders AS o
JOIN orders AS o2
  ON o2.customer_id = o.customer_id
 AND o2.order_date <= o.order_date
WHERE o.status = 'shipped'
GROUP BY o.order_row_id, o.order_id, o.customer_id, o.order_date
"""

# The correct rewrite: window over every row, filter afterwards.
WINDOWED = """
WITH counted AS (
    SELECT order_id, customer_id, order_date, status,
           COUNT(*) OVER (
               PARTITION BY customer_id
               ORDER BY order_date
               RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
           ) AS orders_to_date
    FROM orders
)
SELECT order_id, customer_id, order_date, orders_to_date
FROM counted
WHERE status = 'shipped'
"""

# The tempting rewrite that is faster and WRONG: filtering before the window
# means the window never sees the non-shipped rows. Benchmarked only so you can
# see that being fast is not the same as being right.
WINDOWED_WRONG = """
SELECT order_id, customer_id, order_date,
       COUNT(*) OVER (
           PARTITION BY customer_id
           ORDER BY order_date
           RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS orders_to_date
FROM orders
WHERE status = 'shipped'
"""

INDEX_SQL = "CREATE INDEX IF NOT EXISTS idx_orders_customer_date ON orders (customer_id, order_date)"
DROP_INDEX_SQL = "DROP INDEX IF EXISTS idx_orders_customer_date"


def time_query(conn: sqlite3.Connection, sql: str, repeat: int) -> tuple[float, int]:
    """Return (best seconds, row count). Best of N, not the mean.

    Best-of is the right statistic for a benchmark: it is the run least polluted
    by whatever else the machine was doing. The mean measures your laptop's
    background processes as much as the query.
    """
    best = float("inf")
    rows = 0
    for _ in range(repeat):
        start = time.perf_counter()
        rows = len(conn.execute(sql).fetchall())
        best = min(best, time.perf_counter() - start)
    return best, rows


def plan(conn: sqlite3.Connection, sql: str) -> list[str]:
    """SQLite's execution plan. Read it bottom-up: the deepest line runs first.

    In Postgres this is EXPLAIN ANALYZE; in Databricks it is EXPLAIN or the
    Spark UI. Different output, identical question: what is it actually doing,
    and how many rows does it think it will touch?
    """
    return [row[3] for row in conn.execute("EXPLAIN QUERY PLAN " + sql)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark the Q12 rewrites.")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--skip-correlated", action="store_true",
                        help="skip the slow one when iterating on the others")
    args = parser.parse_args()

    if not args.db.exists():
        print(f"error: {args.db} not found. Run: python seed.py")
        return 2

    conn = sqlite3.connect(args.db)
    conn.execute(DROP_INDEX_SQL)

    variants: list[tuple[str, str]] = []
    if not args.skip_correlated:
        variants.append(("correlated subquery", CORRELATED))
    variants += [("self-join + group by", SELF_JOIN),
                 ("window function", WINDOWED),
                 ("window, filtered first (WRONG)", WINDOWED_WRONG)]

    print(f"database: {args.db}  ·  best of {args.repeat}\n")
    print(f"{'variant':<34}{'index':<8}{'seconds':>10}{'rows':>10}")
    print("-" * 62)

    results: dict[tuple[str, str], float] = {}
    plans_without_index: dict[str, list[str]] = {}
    for index_state in ("no", "yes"):
        if index_state == "no":
            # Capture the plans before the index exists, otherwise the plan you
            # print is not the plan that produced the slow timing.
            for name, sql in variants:
                plans_without_index[name] = plan(conn, sql)
        else:
            conn.execute(INDEX_SQL)
            conn.commit()
        for name, sql in variants:
            seconds, rows = time_query(conn, sql, args.repeat)
            results[(name, index_state)] = seconds
            print(f"{name:<34}{index_state:<8}{seconds:>10.3f}{rows:>10,}")

    print()
    baseline = results.get(("correlated subquery", "no"))
    fastest = results.get(("window function", "yes"))
    if baseline and fastest:
        print(f"window + index is {baseline / fastest:,.0f}x faster than the "
              f"correlated subquery with no index")

    # Correctness check. A rewrite that is faster and different is not a rewrite.
    total = conn.execute(f"SELECT COUNT(*) FROM ({CORRELATED})").fetchone()[0]
    same = conn.execute(f"SELECT COUNT(*) FROM ({CORRELATED}) a "
                        f"JOIN ({WINDOWED}) b ON b.order_id = a.order_id "
                        f"AND b.orders_to_date = a.orders_to_date").fetchone()[0]
    wrong = conn.execute(f"SELECT COUNT(*) FROM ({CORRELATED}) a "
                         f"JOIN ({WINDOWED_WRONG}) b ON b.order_id = a.order_id "
                         f"AND b.orders_to_date = a.orders_to_date").fetchone()[0]
    print(f"\ncorrectness check against the correlated version ({total:,} rows)")
    print(f"    window over all rows, filtered after : {same:,} rows match")
    print(f"    filtered before the window (WRONG)   : {wrong:,} rows match")
    if wrong < total:
        print("    -> the fast-looking rewrite answers a different question")

    for name in plans_without_index:
        print(f"\nexecution plan (no index) — {name}")
        for line in plans_without_index[name]:
            print("   ", line)
    print("\nexecution plan (with index) — correlated subquery")
    for line in plan(conn, CORRELATED):
        print("   ", line)

    conn.execute(DROP_INDEX_SQL)
    conn.commit()
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
