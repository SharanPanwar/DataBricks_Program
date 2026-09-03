"""LAB A — skeleton.

The structure is here; the decisions are not. Every `TODO` is a choice you have
to make and be able to defend in the demo.

    python -m laba.seeds generate ./landing
    python -m laba.ingest ./landing ./submission
    python -m laba.ingest ./landing ./submission     # run it AGAIN. Same counts?

Deliver into ./submission:

    bronze/orders      bronze/customers    bronze/products
    bronze/rescued     run_manifest.json

You may use Auto Loader on Databricks or a plain read locally. The rubric does
not care HOW you did it — it checks whether the output has the properties the
brief asks for.

Two things it does check, and they are worth reading twice:

  * The malformed file contains SIX bad rows and TWO good ones. Both good rows
    must land. Failing the file, or skipping it, loses them.
  * Two full runs from the same landing zone must produce the same count.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType


def build_session(app: str = "lab-a") -> SparkSession:
    session = (SparkSession.builder.master("local[2]").appName(app)
               .config("spark.sql.shuffle.partitions", "4")
               .config("spark.ui.showConsoleProgress", "false").getOrCreate())
    session.sparkContext.setLogLevel("ERROR")
    return session


# The source columns, in order. Note every one is a STRING.
#
# That is deliberate and you should be able to say why: inferring types means
# one row with 'two' in a numeric column changes that column's type for the
# whole batch, so your bronze schema ends up depending on the worst row in the
# file.
ORDERS_COLUMNS = ["order_line_id", "order_id", "customer_id", "product_id",
                  "quantity", "unit_price", "order_ts", "status", "updated_at"]


# ==========================================================================
# SOURCE 1 — FILE DROP
# ==========================================================================
def read_orders(spark: SparkSession, landing: Path) -> tuple[DataFrame, DataFrame]:
    """Read the CSV drop. Return (good, rescued).

    TODO 1 — pick a read mode, and be ready to defend it.

        FAILFAST        the whole read raises on the first bad row
        DROPMALFORMED   bad rows silently vanish
        PERMISSIVE      bad rows kept, unparseable fields NULL

        One of these satisfies BOTH halves of "survive a malformed file without
        losing the batch". Work out which, and why the other two do not.

    TODO 2 — if you choose to capture unparseable rows, the corrupt-record
        column has to be part of the schema you pass. A schema without it
        silently drops the column and you get nothing.

    TODO 3 — some rows PARSE but are still unusable: a timestamp that is not a
        timestamp, a quantity that is not a number. Decide whether those belong
        in `good` or in `rescued`, and be consistent about it. Whichever you
        choose, silver will need a matching rule later.

    TODO 4 — add lineage. At minimum _source_file and _ingested_at. The first
        thing anyone asks at 3am is "where did this row come from".
    """
    raise NotImplementedError("read_orders")


# ==========================================================================
# SOURCE 2 — DATABASE
# ==========================================================================
def read_customers(spark: SparkSession, landing: Path) -> DataFrame:
    """Read the customer master from SQLite.

    On Databricks this would be a JDBC read against Azure SQL. Locally, sqlite3
    into a list and then createDataFrame is fine — the rubric does not care.

    TODO 5 — decide what a re-run should do. This source has no watermark
        column in Lab A, so a full read each time is acceptable. Say so in your
        README rather than leaving it implicit.
    """
    raise NotImplementedError("read_customers")


# ==========================================================================
# SOURCE 3 — API
# ==========================================================================
def read_products(spark: SparkSession, landing: Path) -> DataFrame:
    """Read the paged JSON API.

    TODO 6 — follow the CURSOR, not a computed page count.

        Each page has a `nextPage` field which is null on the last page. There
        is deliberately no `totalCount`, because arithmetic over page counts is
        how people stop one page early and never notice.

    TODO 7 — one page repeats a record that appeared on the previous page.
        Real cursor-paged APIs do this when the underlying data shifts while
        you are reading it. Decide what to do about it, and say so.

    TODO 8 — one record has a null in a required field. It is not your job to
        fix it here; bronze rejects nothing. But know it is there.
    """
    raise NotImplementedError("read_products")


# ==========================================================================
def write(df: DataFrame, path: Path) -> None:
    """Write a table.

    TODO 9 — this is where re-runnability is won or lost.

        A plain append means a second run appends whatever it already appended.
        Work out what mode, or what key, makes a re-run a no-op.
    """
    raise NotImplementedError("write")


def read_count(spark: SparkSession, path: Path) -> int:
    """Count what was actually WRITTEN, not what the plan would produce.

    Counting a DataFrame after writing it re-executes the whole plan, including
    current_timestamp() and input_file_name() — so it is a different
    computation from the table on disk, and the two can disagree. Count the
    table.
    """
    return spark.read.parquet(str(path)).count()


def run(spark: SparkSession, landing: Path, out: Path) -> dict:
    """One full ingestion run. Returns the counts for the manifest."""
    out.mkdir(parents=True, exist_ok=True)

    good, rescued = read_orders(spark, landing)
    write(good, out / "bronze" / "orders")
    write(rescued, out / "bronze" / "rescued")
    write(read_customers(spark, landing), out / "bronze" / "customers")
    write(read_products(spark, landing), out / "bronze" / "products")

    return {
        "bronze_rows": read_count(spark, out / "bronze" / "orders"),
        "rescued_rows": read_count(spark, out / "bronze" / "rescued"),
        "customers": read_count(spark, out / "bronze" / "customers"),
        "products": read_count(spark, out / "bronze" / "products"),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="laba.ingest")
    parser.add_argument("landing", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args(argv[1:])

    spark = build_session()
    try:
        result = run(spark, args.landing, args.out)

        # The manifest is how re-runnability is scored. It must record TWO runs
        # with equal bronze counts.
        #
        # TODO 10 — append this run to the manifest rather than overwriting it,
        # so that running the script twice produces a manifest with two entries.
        manifest_path = args.out / "run_manifest.json"
        raise NotImplementedError("run_manifest.json")

    finally:
        spark.stop()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
