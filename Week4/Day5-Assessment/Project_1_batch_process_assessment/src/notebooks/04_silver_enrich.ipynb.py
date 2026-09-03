# Databricks notebook source
from pyspark.sql import functions as F

CATALOG = "week4_batch"
SCHEMA = "trades"
VOLUME = "landing"
SOURCE = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}/data"
SILVER = f"{CATALOG}.{SCHEMA}.silver_trades"
STAGING = f"{CATALOG}.{SCHEMA}.valid_trades_staging"

valid = spark.table(STAGING)
customers = spark.read.option("header", True).option("inferSchema", True).csv(f"{SOURCE}/customers.csv")
accounts = spark.read.option("header", True).option("inferSchema", True).csv(f"{SOURCE}/accounts.csv")

print("valid     :", valid.count())
print("accounts  :", accounts.count())
print("customers :", customers.count())


# COMMAND ----------

silver = (
    valid.join(accounts, "account_id", "left")
         .join(customers, "customer_id", "left")
         .withColumn("_processed_at", F.current_timestamp())
)

print("silver rows:", silver.count())
print("rows with no customer:", silver.filter(F.col("customer_id").isNull()).count())
display(silver.limit(20))


# COMMAND ----------

silver.write.mode("overwrite").format("delta").saveAsTable(SILVER)


# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS silver_rows FROM week4_batch.trades.silver_trades;
# MAGIC
# MAGIC SELECT segment, COUNT(*) AS trades
# MAGIC FROM week4_batch.trades.silver_trades
# MAGIC GROUP BY segment
# MAGIC ORDER BY trades DESC;
# MAGIC
# MAGIC SELECT * FROM week4_batch.trades.silver_trades
# MAGIC WHERE trade_id LIKE 'BAD%';
# MAGIC