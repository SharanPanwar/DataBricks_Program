# Databricks notebook source
from pyspark.sql import functions as F

CATALOG = "week4_batch"
SCHEMA = "trades"
VOLUME = "landing"
SOURCE = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}/data"
BRONZE = f"{CATALOG}.{SCHEMA}.bronze_trades"

print(SOURCE)
print(BRONZE)


# COMMAND ----------

customers = spark.read.option("header", True).option("inferSchema", True).csv(f"{SOURCE}/customers.csv")
accounts = spark.read.option("header", True).option("inferSchema", True).csv(f"{SOURCE}/accounts.csv")
trades = spark.read.option("header", True).option("inferSchema", True).csv(f"{SOURCE}/transactions.csv")
bad_trades = spark.read.option("header", True).option("inferSchema", True).csv(f"{SOURCE}/transactions_bad.csv")

print("customers :", customers.count())
print("accounts  :", accounts.count())
print("trades    :", trades.count())
print("bad_trades:", bad_trades.count())


# COMMAND ----------

display(customers.limit(10))


# COMMAND ----------

display(accounts.limit(10))


# COMMAND ----------

display(trades.limit(10))


# COMMAND ----------

display(bad_trades)


# COMMAND ----------

bronze = (
    trades
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_source_file", F.col("_metadata.file_path"))
)

bad_bronze = (
    bad_trades
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_source_file", F.col("_metadata.file_path"))
)

bronze.write.mode("overwrite").format("delta").saveAsTable(BRONZE)
bad_bronze.write.mode("append").format("delta").saveAsTable(BRONZE)


# COMMAND ----------

bronze_tbl = spark.table(BRONZE)
print("bronze rows:", bronze_tbl.count())
display(bronze_tbl.orderBy(F.col("trade_id").desc()).limit(20))


# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS bronze_rows FROM week4_batch.trades.bronze_trades;
# MAGIC
# MAGIC SELECT * FROM week4_batch.trades.bronze_trades
# MAGIC WHERE trade_id LIKE 'BAD%'
# MAGIC ORDER BY trade_id;
# MAGIC