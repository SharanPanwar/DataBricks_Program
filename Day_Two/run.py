"""Run a query file and print the result.

    python run.py queries/q07_dedupe.sql
    python run.py queries/q01_grain.sql --plan
    python run.py --all

A query file may contain several statements. Only the last one produces the
result — the earlier ones exist so that a file can set something up. Comments
are stripped before splitting, because a semicolon inside a comment is not a
statement terminator and a naive split on ';' gets that wrong.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "sales.db"
QUERIES = Path(__file__).parent / "queries"

_LINE_COMMENT = re.compile(r"--[^\n]*")


def split_statements(sql: str) -> list[str]:
    """Strip line comments, then split on semicolons. Blank statements dropped."""
    without_comments = _LINE_COMMENT.sub("", sql)
    return [part.strip() for part in without_comments.split(";") if part.strip()]


def run_query_file(conn: sqlite3.Connection, path: Path) -> tuple[list[str], list[tuple]]:
    """Execute every statement in the file; return columns and rows of the last."""
    statements = split_statements(path.read_text(encoding="utf-8"))
    if not statements:
        raise ValueError(f"{path.name} contains no executable statement")
    cursor = None
    for statement in statements:
        cursor = conn.execute(statement)
    columns = [d[0] for d in cursor.description] if cursor.description else []
    return columns, cursor.fetchall()


def explain(conn: sqlite3.Connection, path: Path) -> list[str]:
    statements = split_statements(path.read_text(encoding="utf-8"))
    return [row[3] for row in conn.execute("EXPLAIN QUERY PLAN " + statements[-1])]


def render(columns: list[str], rows: list[tuple], limit: int = 25) -> str:
    if not columns:
        return "(no result set)"
    widths = [max(len(c), *(len(str(r[i])) for r in rows[:limit])) if rows else len(c)
              for i, c in enumerate(columns)]
    widths = [min(w, 34) for w in widths]
    line = "  ".join(c[:w].ljust(w) for c, w in zip(columns, widths))
    out = [line, "  ".join("-" * w for w in widths)]
    for row in rows[:limit]:
        out.append("  ".join(str(v)[:w].ljust(w) for v, w in zip(row, widths)))
    if len(rows) > limit:
        out.append(f"... {len(rows) - limit:,} more rows")
    out.append(f"({len(rows):,} rows)")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Lab 2 query file.")
    parser.add_argument("query", nargs="?", type=Path, help="path to a .sql file")
    parser.add_argument("--all", action="store_true", help="run every query in order")
    parser.add_argument("--plan", action="store_true", help="also print the execution plan")
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    if not args.db.exists():
        print(f"error: {args.db} not found. Run: python seed.py --small")
        return 2

    conn = sqlite3.connect(args.db)
    paths = sorted(QUERIES.glob("q*.sql")) if args.all else [args.query]
    if paths == [None]:
        parser.error("give a query file or --all")

    for path in paths:
        print(f"\n=== {path.name} " + "=" * max(0, 60 - len(path.name)))
        columns, rows = run_query_file(conn, path)
        print(render(columns, rows))
        if args.plan:
            print("\nplan:")
            for step in explain(conn, path):
                print("   ", step)
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
