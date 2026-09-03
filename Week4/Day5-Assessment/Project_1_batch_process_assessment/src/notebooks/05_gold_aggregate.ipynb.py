# Databricks notebook source
from pyspark.sql import functions as F

CATALOG = "week4_batch"
SCHEMA = "trades"
SILVER = f"{CATALOG}.{SCHEMA}.silver_trades"
GOLD = f"{CATALOG}.{SCHEMA}.gold_daily_position"

silver = spark.table(SILVER)
print("silver rows:", silver.count())


# COMMAND ----------

gold = (
    silver.groupBy("trade_date", "symbol", "currency")
          .agg(
              F.sum(F.when(F.col("side") == "BUY", F.col("trade_value")).otherwise(0)).alias("buy_value"),
              F.sum(F.when(F.col("side") == "SELL", F.col("trade_value")).otherwise(0)).alias("sell_value"),
              F.sum("trade_value").alias("gross_value"),
              F.countDistinct("trade_id").alias("trade_count"),
          )
          .withColumn("net_flow", F.col("buy_value") - F.col("sell_value"))
)

print("gold rows:", gold.count())
display(gold.orderBy("trade_date", "symbol", "currency"))


# COMMAND ----------

gold.write.mode("overwrite").format("delta").saveAsTable(GOLD)


# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM week4_batch.trades.gold_daily_position
# MAGIC ORDER BY trade_date, symbol, currency
# MAGIC LIMIT 50;
# MAGIC
# MAGIC SELECT
# MAGIC   ROUND(SUM(buy_value), 2) AS buy_value,
# MAGIC   ROUND(SUM(sell_value), 2) AS sell_value,
# MAGIC   ROUND(SUM(gross_value), 2) AS gross_value,
# MAGIC   ROUND(SUM(net_flow), 2) AS net_flow,
# MAGIC   SUM(trade_count) AS trade_count
# MAGIC FROM week4_batch.trades.gold_daily_position;
# MAGIC