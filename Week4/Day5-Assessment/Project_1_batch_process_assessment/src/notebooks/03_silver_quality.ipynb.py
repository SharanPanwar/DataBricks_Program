# Databricks notebook source
from pyspark.sql import functions as F

CATALOG = "week4_batch"
SCHEMA = "trades"
BRONZE = f"{CATALOG}.{SCHEMA}.bronze_trades"
QUARANTINE = f"{CATALOG}.{SCHEMA}.quarantine_trades"

bronze = spark.table(BRONZE)
print("bronze rows:", bronze.count())
display(bronze.limit(10))


# COMMAND ----------

typed = (
    bronze
    .withColumn("account_id", F.when(F.trim(F.col("account_id")) == "", None).otherwise(F.col("account_id")))
    .withColumn("trade_id", F.when(F.trim(F.col("trade_id")) == "", None).otherwise(F.col("trade_id")))
    .withColumn("trade_date", F.to_date("trade_date"))
    .withColumn("quantity", F.col("quantity").cast("decimal(18,4)"))
    .withColumn("price", F.col("price").cast("decimal(18,4)"))
    .withColumn("trade_value", F.col("quantity") * F.col("price"))
    .withColumn("side", F.upper(F.trim("side")))
    .withColumn("currency", F.upper(F.trim("currency")))
)

display(typed.limit(10))


# COMMAND ----------

dq = typed.withColumn(
    "_dq_reason",
    F.when(F.col("trade_id").isNull(), "NULL_TRADE_ID")
     .when(F.col("account_id").isNull(), "NULL_ACCOUNT_ID")
     .when(F.col("quantity") <= 0, "INVALID_QUANTITY")
     .when(F.col("price") <= 0, "INVALID_PRICE")
     .when(~F.col("side").isin("BUY", "SELL"), "INVALID_SIDE")
     .otherwise(None),
)

quarantine = dq.filter(F.col("_dq_reason").isNotNull())
valid = dq.filter(F.col("_dq_reason").isNull()).drop("_dq_reason")

print("valid rows      :", valid.count())
print("quarantine rows :", quarantine.count())


# COMMAND ----------

display(
    dq.groupBy("_dq_reason")
      .count()
      .orderBy(F.col("count").desc())
)


# COMMAND ----------

display(quarantine)


# COMMAND ----------

quarantine.write.mode("overwrite").format("delta").saveAsTable(QUARANTINE)
valid.write.mode("overwrite").format("delta").saveAsTable(f"{CATALOG}.{SCHEMA}.valid_trades_staging")


# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT _dq_reason, COUNT(*) AS rows
# MAGIC FROM week4_batch.trades.quarantine_trades
# MAGIC GROUP BY _dq_reason
# MAGIC ORDER BY rows DESC;
# MAGIC
# MAGIC SELECT COUNT(*) AS valid_staging_rows
# MAGIC FROM week4_batch.trades.valid_trades_staging;
# MAGIC