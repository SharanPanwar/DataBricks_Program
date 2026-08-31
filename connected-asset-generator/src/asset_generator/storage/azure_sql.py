"""Azure SQL storage layer — connection, DDL, and bulk writes."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Iterable, Sequence

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_DIR = PACKAGE_ROOT / "schema"

# GO is a client-side batch separator; SQLAlchemy sends one statement at a time.
_GO_SPLIT = re.compile(r"^\s*GO\s*$", re.IGNORECASE | re.MULTILINE)


class DatabaseError(Exception):
    """Raised when database operations fail."""


def get_connection_string() -> str:
    """Read Azure SQL connection string from environment."""
    value = os.environ.get("AZURE_SQL_CONNECTION_STRING")
    if not value:
        raise DatabaseError(
            "AZURE_SQL_CONNECTION_STRING is not set. "
            "Example: mssql+pyodbc://user:pass@server.database.windows.net/db"
            "?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes"
        )
    return value


def get_engine(connection_string: str | None = None, *, echo: bool = False) -> Engine:
    conn = connection_string or get_connection_string()
    return create_engine(conn, echo=echo, pool_pre_ping=True)


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _split_sql_batches(sql: str) -> list[str]:
    return [batch.strip() for batch in _GO_SPLIT.split(sql) if batch.strip()]


def execute_sql_file(engine: Engine, path: Path) -> None:
    """Execute a T-SQL script file, splitting on GO batch separators."""
    if not path.exists():
        raise DatabaseError(f"SQL file not found: {path}")
    sql = path.read_text(encoding="utf-8")
    batches = _split_sql_batches(sql)
    with engine.begin() as conn:
        for batch in batches:
            conn.execute(text(batch))


def apply_schema(engine: Engine) -> None:
    """Apply all schema/*.sql files in sorted order."""
    if not SCHEMA_DIR.is_dir():
        raise DatabaseError(f"Schema directory not found: {SCHEMA_DIR}")
    for path in sorted(SCHEMA_DIR.glob("*.sql")):
        execute_sql_file(engine, path)


def bulk_insert_mappings(
    session: Session,
    table_name: str,
    rows: Sequence[dict[str, Any]],
    *,
    batch_size: int = 5000,
) -> int:
    """Insert rows in batches using parameterized INSERT statements."""
    if not rows:
        return 0

    columns = list(rows[0].keys())
    col_list = ", ".join(columns)
    param_list = ", ".join(f":{col}" for col in columns)
    stmt = text(f"INSERT INTO {table_name} ({col_list}) VALUES ({param_list})")

    inserted = 0
    for start in range(0, len(rows), batch_size):
        chunk = rows[start : start + batch_size]
        for row in chunk:
            session.execute(stmt, row)
        inserted += len(chunk)
    return inserted


def table_has_rows(engine: Engine, table_name: str) -> bool:
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT TOP 1 1 AS ok FROM {table_name}"))
        return result.first() is not None


def truncate_tables(engine: Engine, table_names: Iterable[str]) -> None:
    """Truncate tables in FK-safe order (caller provides order)."""
    with engine.begin() as conn:
        for table in table_names:
            conn.execute(text(f"TRUNCATE TABLE {table}"))
