# Databricks notebook source
# MAGIC %sql
# MAGIC CREATE CATALOG IF NOT EXISTS week4_batch;
# MAGIC CREATE SCHEMA IF NOT EXISTS week4_batch.trades;
# MAGIC CREATE VOLUME IF NOT EXISTS week4_batch.trades.landing;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW SCHEMAS IN week4_batch;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW VOLUMES IN week4_batch.trades;
# MAGIC