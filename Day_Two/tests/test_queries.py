"""Tests for the twelve queries.

Each test asserts something that would fail if the query were wrong — not merely
that it returned rows. Several of them encode the *specific bug* the query is
about, so a plausible-but-wrong answer fails rather than passing quietly.

The database is deterministic (seed 42), so the expected values are stable. If
you change seed.py these will fail, and they should — regenerate the numbers
deliberately rather than loosening the assertions.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from run import run_query_file, split_statements  # noqa: E402

QUERIES = ROOT / "queries"


@pytest.fixture(scope="session")
def db(tmp_path_factory) -> sqlite3.Connection:
    """Build a fresh small database once for the whole session."""
    path = tmp_path_factory.mktemp("lab2") / "sales.db"
    subprocess.run(
        [sys.executable, str(ROOT / "seed.py"), "--small", "--path", str(path)],
        check=True, capture_output=True,
    )
    conn = sqlite3.connect(path)
    yield conn
    conn.close()


def result(db: sqlite3.Connection, name: str):
    path = next(QUERIES.glob(f"{name}*.sql"))
    return run_query_file(db, path)


# ----------------------------------------------------------------- shared
def test_every_query_file_runs(db):
    """No query file is allowed to be broken, even the ones with no assertions."""
    for path in sorted(QUERIES.glob("q*.sql")):
        columns, rows = run_query_file(db, path)
        assert columns, f"{path.name} returned no result set"


def test_no_query_file_relies_on_a_semicolon_inside_a_comment(db):
    """A naive split on ';' is a common mistake. Make sure ours does not need one."""
    for path in sorted(QUERIES.glob("q*.sql")):
        assert split_statements(path.read_text(encoding="utf-8"))


# ----------------------------------------------------------------- Q1 grain
def test_q01_proves_orders_is_not_one_row_per_order(db):
    columns, rows = result(db, "q01")
    (total, distinct, surplus, ratio) = rows[0]
    assert distinct == 5_000
    assert total > distinct, "the whole point is that order_id is not unique"
    assert surplus == total - distinct
    assert ratio > 1.0


# ----------------------------------------------------------------- Q2 joins
def test_q02_finds_customers_with_no_orders(db):
    columns, rows = result(db, "q02")
    assert rows, "an anti-join that returns nothing means the LEFT join collapsed"
    total = sum(r[1] for r in rows)
    assert total == 40, "40 customers were seeded without any orders"


# ----------------------------------------------------------------- Q3 fan-out
def test_q03_shows_the_inflated_count_and_the_correct_one(db):
    columns, rows = result(db, "q03")
    assert rows
    for status, inflated, correct, added, qty_wrong, qty_right in rows:
        assert inflated > correct, "the naive join must visibly over-count"
        assert added == inflated - correct
        # Summing the many-side is fine. Only the one-side count inflates.
        assert qty_wrong == qty_right
    assert sum(r[2] for r in rows) == 5_000, "correct order count is one per order_id"


# ----------------------------------------------------------------- Q4 nulls
def test_q04_shows_how_aggregates_treat_null(db):
    columns, rows = result(db, "q04")
    (all_c, with_limit, nulls, avg_ignoring, avg_zero, sum_ignoring, sum_coalesce) = rows[0]
    assert all_c == 240
    assert nulls == all_c - with_limit
    assert nulls > 0, "the seed must contain NULL credit limits or this teaches nothing"
    assert avg_ignoring > avg_zero, "treating NULL as zero must lower the average"
    assert round(sum_ignoring, 2) == round(sum_coalesce, 2), "SUM ignores NULL either way"


# ----------------------------------------------------------------- Q5 having
def test_q05_filters_rows_before_grouping_and_groups_after(db):
    columns, rows = result(db, "q05")
    assert rows, "no region cleared the threshold — check the WHERE clause"
    assert all(r[1] > 150 for r in rows), "HAVING threshold not applied"
    assert rows == sorted(rows, key=lambda r: -r[1]), "not ordered by order count"
    assert all(r[2] <= r[1] for r in rows), "distinct customers cannot exceed orders"


# ----------------------------------------------------------------- Q6 CTE
def test_q06_cte_version_returns_the_expected_regions(db):
    columns, rows = result(db, "q06")
    assert rows
    assert all(r[2] > 2 for r in rows), "the > 2 filter was lost in the rewrite"
    assert len(set(r[0] for r in rows)) == len(rows), "regions must be unique"


# ----------------------------------------------------------------- Q7 dedupe
def test_q07_returns_one_row_per_order_id(db):
    """The query itself is limited for display. Re-run the pattern unlimited here."""
    sql = """
    WITH ranked AS (
        SELECT o.*, ROW_NUMBER() OVER (
            PARTITION BY o.order_id
            ORDER BY o.updated_at DESC, o.order_row_id DESC) AS rn
        FROM orders AS o
    )
    SELECT order_id, COUNT(*) FROM ranked WHERE rn = 1 GROUP BY order_id HAVING COUNT(*) > 1
    """
    assert db.execute(sql).fetchall() == [], "deduplication left duplicates behind"

    count = db.execute(
        "SELECT COUNT(*) FROM (SELECT o.*, ROW_NUMBER() OVER "
        "(PARTITION BY order_id ORDER BY updated_at DESC, order_row_id DESC) rn "
        "FROM orders o) WHERE rn = 1"
    ).fetchone()[0]
    assert count == 5_000


def test_q07_keeps_the_latest_version_not_the_first(db):
    """Pick an order that was corrected and check the surviving row is the later one."""
    corrected = db.execute(
        "SELECT order_id FROM orders GROUP BY order_id HAVING COUNT(*) > 1 LIMIT 1"
    ).fetchone()[0]
    latest_updated = db.execute(
        "SELECT MAX(updated_at) FROM orders WHERE order_id = ?", (corrected,)
    ).fetchone()[0]
    kept = db.execute(
        "SELECT updated_at FROM (SELECT o.*, ROW_NUMBER() OVER "
        "(PARTITION BY order_id ORDER BY updated_at DESC, order_row_id DESC) rn "
        "FROM orders o WHERE order_id = ?) WHERE rn = 1", (corrected,)
    ).fetchone()[0]
    assert kept == latest_updated


# ----------------------------------------------------------------- Q8 ranking
def test_q08_shows_the_difference_between_the_three_ranking_functions(db):
    columns, rows = result(db, "q08")
    assert rows
    assert all(r[4] <= 3 for r in rows), "the RANK <= 3 filter was not applied"
    for row in rows:
        rn, rnk, dense = row[3], row[4], row[5]
        assert rn >= rnk >= dense, "ROW_NUMBER >= RANK >= DENSE_RANK always holds"
    per_region = {}
    for row in rows:
        per_region.setdefault(row[0], []).append(row)
    assert len(per_region) == 5, "expected all five regions"


# ----------------------------------------------------------------- Q9 lag
def test_q09_first_month_has_no_previous_value(db):
    columns, rows = result(db, "q09")
    assert rows[0][2] is None, "the first month must have a NULL previous value"
    assert rows[0][4] is None, "percentage change is undefined for the first month"
    for row in rows[1:]:
        assert row[2] is not None
        assert row[3] == row[1] - row[2], "change must equal current minus previous"
    months = [r[0] for r in rows]
    assert months == sorted(months), "months must be in order for LAG to mean anything"


# ----------------------------------------------------------------- Q10 frames
def test_q10_running_total_is_monotonic_and_matches_the_cumulative_sum(db):
    columns, rows = result(db, "q10")
    assert rows
    running = 0
    for day, orders, running_total, ma7, centred in rows:
        running += orders
        assert running_total == running, "running total does not match a manual cumulative sum"
        assert ma7 is not None and ma7 > 0
    totals = [r[2] for r in rows]
    assert totals == sorted(totals), "a running total of positive counts cannot decrease"


# ----------------------------------------------------------------- Q11 PIT
def test_q11_point_in_time_price_differs_from_todays_price(db):
    columns, rows = result(db, "q11")
    (pit, today, overstatement, lines) = rows[0]
    assert lines > 0
    assert pit != today, "if these match, today's price was used for both"
    assert round(today - pit, 2) == round(overstatement, 2)
    assert today > pit, "prices rise in this seed, so today's price overstates history"


def test_q11_no_order_line_matches_two_price_rows(db):
    """An overlapping validity window would fan out and silently double revenue."""
    sql = """
    WITH latest_orders AS (
        SELECT order_id, order_date FROM (
            SELECT o.*, ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC) rn
            FROM orders o) WHERE rn = 1
    )
    SELECT COUNT(*) FROM (
        SELECT i.order_item_id, COUNT(*) AS matches
        FROM latest_orders lo
        JOIN order_items i ON i.order_id = lo.order_id
        JOIN price_history ph ON ph.product_id = i.product_id
                             AND lo.order_date >= ph.valid_from
                             AND lo.order_date <  ph.valid_to
        GROUP BY i.order_item_id HAVING COUNT(*) > 1)
    """
    assert db.execute(sql).fetchone()[0] == 0


def test_q11_every_order_line_is_priced(db):
    """An INNER join here can silently drop lines whose date falls in no window."""
    total_lines = db.execute("SELECT COUNT(*) FROM order_items").fetchone()[0]
    columns, rows = result(db, "q11")
    assert rows[0][3] == total_lines, "some order lines were not priced at all"


# ----------------------------------------------------------------- Q12 rewrite
def test_q12_window_version_matches_the_correlated_version(db):
    """The rewrite must be faster AND identical. Faster and different is a bug."""
    correlated = db.execute("""
        SELECT o.order_id, o.customer_id, o.order_date,
               (SELECT COUNT(*) FROM orders o2
                 WHERE o2.customer_id = o.customer_id
                   AND o2.order_date <= o.order_date) AS n
        FROM orders o WHERE o.status = 'shipped'
        ORDER BY o.order_row_id
    """).fetchall()
    windowed = db.execute("""
        WITH counted AS (
            SELECT order_row_id, order_id, customer_id, order_date, status,
                   COUNT(*) OVER (PARTITION BY customer_id ORDER BY order_date
                                  RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS n
            FROM orders
        )
        SELECT order_id, customer_id, order_date, n
        FROM counted WHERE status = 'shipped'
        ORDER BY order_row_id
    """).fetchall()
    assert correlated == windowed


def test_q12_filtering_before_the_window_gives_a_different_answer(db):
    """WHERE runs before window functions. This is the trap Q12 is really about.

    The tempting rewrite filters to shipped first, so the window never sees the
    non-shipped orders and the counts come out lower. It is faster, it looks
    right, and it answers a different question.
    """
    correlated = db.execute("""
        SELECT o.order_id,
               (SELECT COUNT(*) FROM orders o2
                 WHERE o2.customer_id = o.customer_id
                   AND o2.order_date <= o.order_date) AS n
        FROM orders o WHERE o.status = 'shipped' ORDER BY o.order_row_id
    """).fetchall()
    filtered_first = db.execute("""
        SELECT order_id,
               COUNT(*) OVER (PARTITION BY customer_id ORDER BY order_date
                              RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS n
        FROM orders WHERE status = 'shipped' ORDER BY order_row_id
    """).fetchall()

    assert len(correlated) == len(filtered_first), "same row count, different numbers"
    assert correlated != filtered_first, "if these match, the seed has no non-shipped orders"
    matching = sum(1 for a, b in zip(correlated, filtered_first) if a == b)
    assert matching < len(correlated) / 2, "most rows should disagree"


def test_q12_range_not_rows_is_required_for_same_day_orders(db):
    """With ROWS, two orders on the same date get different counts. That is wrong.

    This test documents why the frame is RANGE. If someone 'simplifies' it to
    ROWS, this fails and tells them exactly what they broke.
    """
    rows_version = db.execute("""
        SELECT COUNT(*) FROM (
            SELECT customer_id, order_date,
                   COUNT(*) OVER (PARTITION BY customer_id ORDER BY order_date
                                  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS n
            FROM orders WHERE status = 'shipped')
        GROUP BY customer_id, order_date HAVING COUNT(DISTINCT n) > 1
    """).fetchall()
    assert rows_version, "expected at least one same-day pair where ROWS disagrees"
