# Databricks notebook source
# MAGIC %sql
# MAGIC SELECT COUNT(*) AS total_trades FROM week4_batch.trades.silver_trades;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT ROUND(SUM(trade_value), 2) AS gross_trade_value FROM week4_batch.trades.silver_trades;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT ROUND(
# MAGIC   SUM(CASE WHEN side = 'BUY' THEN trade_value ELSE -trade_value END), 2
# MAGIC ) AS net_flow FROM week4_batch.trades.silver_trades;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS quarantined_rows FROM week4_batch.trades.quarantine_trades;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT trade_date, ROUND(SUM(trade_value), 2) AS gross_value
# MAGIC FROM week4_batch.trades.silver_trades
# MAGIC GROUP BY trade_date
# MAGIC ORDER BY trade_date;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT symbol, COUNT(*) AS trades, ROUND(SUM(trade_value), 2) AS gross_value
# MAGIC FROM week4_batch.trades.silver_trades
# MAGIC GROUP BY symbol
# MAGIC ORDER BY gross_value DESC
# MAGIC LIMIT 10;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT side, COUNT(*) AS trades, ROUND(SUM(trade_value), 2) AS trade_value
# MAGIC FROM week4_batch.trades.silver_trades
# MAGIC GROUP BY side;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT segment, COUNT(*) AS trades, ROUND(SUM(trade_value), 2) AS gross_value
# MAGIC FROM week4_batch.trades.silver_trades
# MAGIC GROUP BY segment
# MAGIC ORDER BY gross_value DESC;
# MAGIC