# Databricks notebook source
# MAGIC %sql
# MAGIC CREATE OR REPLACE VIEW week4_batch.trades.vw_trade_quality AS
# MAGIC SELECT
# MAGIC   COUNT(*) AS total_rows,
# MAGIC   SUM(CASE WHEN trade_id IS NULL THEN 1 ELSE 0 END) AS null_trade_id,
# MAGIC   SUM(CASE WHEN quantity <= 0 THEN 1 ELSE 0 END) AS invalid_quantity,
# MAGIC   SUM(CASE WHEN price <= 0 THEN 1 ELSE 0 END) AS invalid_price
# MAGIC FROM week4_batch.trades.silver_trades;
# MAGIC
# MAGIC SELECT * FROM week4_batch.trades.vw_trade_quality;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE VIEW week4_batch.trades.vw_trade_quality AS
# MAGIC SELECT
# MAGIC   COUNT(*) AS total_rows,
# MAGIC   SUM(CASE WHEN trade_id IS NULL THEN 1 ELSE 0 END) AS null_trade_id,
# MAGIC   SUM(CASE WHEN quantity <= 0 THEN 1 ELSE 0 END) AS invalid_quantity,
# MAGIC   SUM(CASE WHEN price <= 0 THEN 1 ELSE 0 END) AS invalid_price
# MAGIC FROM week4_batch.trades.silver_trades;
# MAGIC
# MAGIC SELECT * FROM week4_batch.trades.vw_trade_quality;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   (SELECT COUNT(*) FROM week4_batch.trades.bronze_trades) AS bronze_rows,
# MAGIC   (SELECT COUNT(*) FROM week4_batch.trades.quarantine_trades) AS quarantine_rows,
# MAGIC   (SELECT COUNT(*) FROM week4_batch.trades.silver_trades) AS silver_rows,
# MAGIC   (SELECT COUNT(*) FROM week4_batch.trades.gold_daily_position) AS gold_rows;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT _dq_reason, COUNT(*) AS rows
# MAGIC FROM week4_batch.trades.quarantine_trades
# MAGIC GROUP BY _dq_reason
# MAGIC ORDER BY rows DESC;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM week4_batch.trades.gold_daily_position
# MAGIC ORDER BY trade_date, symbol;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE HISTORY week4_batch.trades.silver_trades;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE DETAIL week4_batch.trades.silver_trades;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW TABLES IN week4_batch.trades;
# MAGIC