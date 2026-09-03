# Databricks notebook source
# MAGIC %md
# MAGIC # Lab A — bronze ingestion (Databricks)
# MAGIC
# MAGIC The Databricks version of the same lab. The local skeleton in
# MAGIC `src/laba/ingest.py` is the same problem; solve it wherever you prefer.
# MAGIC
# MAGIC Upload the generated landing files to a Unity Catalog volume first:
# MAGIC
# MAGIC ```bash
# MAGIC python -m laba.seeds generate ./landing
# MAGIC ```
# MAGIC
# MAGIC Catalog → your catalog → bronze → landing → Upload.

# COMMAND ----------
# EVERY widget in the first cell.
#
# Widgets are created when the cell that defines them runs. Definitions in cell
# 5 read in cell 3 means a fresh Run All fails on the first pass and works on
# the second - which looks like flakiness and is not.
dbutils.widgets.text("catalog", "aurora_dev", "Catalog")
dbutils.widgets.text("load_date", "2026-08-31", "Load date")
dbutils.widgets.text("batch_id", "1", "Batch id")

# COMMAND ----------
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType

CATALOG = dbutils.widgets.get("catalog")
LOAD_DATE = dbutils.widgets.get("load_date")
BATCH_ID = int(dbutils.widgets.get("batch_id"))   # get() ALWAYS returns a string

LANDING = f"/Volumes/{CATALOG}/bronze/landing"
CHECKPOINTS = f"/Volumes/{CATALOG}/ops/checkpoints"
spark.sql(f"USE CATALOG {CATALOG}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## TODO 1 — the schema
# MAGIC
# MAGIC Every column a STRING. Inference means one row with `two` in a numeric
# MAGIC column changes that column's type for the whole batch, so your bronze
# MAGIC schema ends up depending on the worst row in the file.
# MAGIC
# MAGIC If you are capturing unparseable rows, the corrupt-record column has to
# MAGIC be **part of the schema you pass**. A schema without it silently drops
# MAGIC the column and you get nothing.

# COMMAND ----------
ORDERS_SCHEMA = StructType([
    # TODO: the nine source columns, all StringType
    # TODO: plus the corrupt-record column, if you are using one
])

# COMMAND ----------
# MAGIC %md
# MAGIC ## TODO 2 — read the file drop
# MAGIC
# MAGIC Auto Loader or a plain read. Four options carry the weight if you use
# MAGIC Auto Loader:
# MAGIC
# MAGIC | Option | What it does |
# MAGIC |---|---|
# MAGIC | `cloudFiles.schemaLocation` | Where the schema lives between runs |
# MAGIC | `cloudFiles.schemaEvolutionMode` | What happens when a new column appears |
# MAGIC | `rescuedDataColumn` | Captures what does not fit, rather than dropping it |
# MAGIC | `checkpointLocation` | **This is the watermark.** Put it in a volume |
# MAGIC
# MAGIC And pick a read mode deliberately: `FAILFAST`, `DROPMALFORMED` or
# MAGIC `PERMISSIVE`. One of the three satisfies both halves of the brief.

# COMMAND ----------
# TODO
raw = None

# COMMAND ----------
# MAGIC %md
# MAGIC ## TODO 3 — split good from rescued
# MAGIC
# MAGIC Some rows PARSE but are still unusable — a timestamp that is not a
# MAGIC timestamp, `N/A` in a numeric field. A corrupt-record check alone will
# MAGIC not see those.
# MAGIC
# MAGIC Note `try_to_timestamp`, not `to_timestamp`: Spark 4 enables ANSI mode
# MAGIC by default, so a malformed cast raises rather than returning NULL — and
# MAGIC in a rescue check that means the job dies on the row you were trying to
# MAGIC catch.

# COMMAND ----------
# TODO
good = None
rescued = None

# COMMAND ----------
# MAGIC %md
# MAGIC ## TODO 4 — lineage, then write
# MAGIC
# MAGIC At minimum `_source_file` and `_ingested_at`. `_metadata.file_path` gives
# MAGIC you the first one free.
# MAGIC
# MAGIC Then write in a way that makes a second run a no-op. `replaceWhere` on
# MAGIC the load-date partition, or a merge on the natural key — but not a plain
# MAGIC append, which appends whatever it already appended.

# COMMAND ----------
# TODO

# COMMAND ----------
# MAGIC %md
# MAGIC ## TODO 5 — the other two sources
# MAGIC
# MAGIC The database and the paged API. For the API: follow the **cursor**, never
# MAGIC a computed page count. There is no `totalCount` field on purpose.

# COMMAND ----------
# TODO

# COMMAND ----------
# MAGIC %md
# MAGIC ## Prove it re-runs
# MAGIC
# MAGIC Run every cell above a second time. The counts must not move.
# MAGIC
# MAGIC Then write `run_manifest.json` with both runs. That file is how the
# MAGIC re-runnability criterion is scored — five marks, and the one people lose
# MAGIC most.

# COMMAND ----------
# TODO
