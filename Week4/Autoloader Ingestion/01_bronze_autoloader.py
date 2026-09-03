# Databricks notebook source
# DBTITLE 1,Configuration Cell
# Config — reuse for all tables later
STORAGE_ACCOUNT = "stpracticeecom"
CONTAINER = "practice-ecommerce"
BASE_PATH = f"abfss://{CONTAINER}@{STORAGE_ACCOUNT}.dfs.core.windows.net"

CATALOG = "practice_ecommerce"
BRONZE_SCHEMA = "bronze"

# COMMAND ----------

# DBTITLE 1,Autoloader CSV Read
tables = ["customers", "products", "orders", "order_items"]

for table_name in tables:
    print(f"Ingesting: {table_name}")

    landing_path = f"{BASE_PATH}/landing/{table_name}/"
    checkpoint_path = f"{BASE_PATH}/checkpoints/bronze/{table_name}/"
    schema_path = f"{BASE_PATH}/checkpoints/bronze/{table_name}/_schema"
    target_table = f"{CATALOG}.{BRONZE_SCHEMA}.{table_name}"

    (
        spark.readStream
            .format("cloudFiles")
            .option("cloudFiles.format", "csv")
            .option("header", "true")
            .option("cloudFiles.inferColumnTypes", "true")
            .option("cloudFiles.schemaLocation", schema_path)
            .load(landing_path)
            .writeStream
            .option("checkpointLocation", checkpoint_path)
            .option("mergeSchema", "true")
            .trigger(availableNow=True)
            .table(target_table)
    )

    print(f"Done: {table_name}")

# COMMAND ----------

# DBTITLE 1,Verification SQL
# MAGIC %sql
# MAGIC SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM practice_ecommerce.bronze.customers
# MAGIC UNION ALL
# MAGIC SELECT 'products', COUNT(*) FROM practice_ecommerce.bronze.products
# MAGIC UNION ALL
# MAGIC SELECT 'orders', COUNT(*) FROM practice_ecommerce.bronze.orders
# MAGIC UNION ALL
# MAGIC SELECT 'order_items', COUNT(*) FROM practice_ecommerce.bronze.order_items;

# COMMAND ----------

# DBTITLE 1,post autoloader run verification
# MAGIC %sql
# MAGIC SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM practice_ecommerce.bronze.customers
# MAGIC UNION ALL
# MAGIC SELECT 'products', COUNT(*) FROM practice_ecommerce.bronze.products
# MAGIC UNION ALL
# MAGIC SELECT 'orders', COUNT(*) FROM practice_ecommerce.bronze.orders
# MAGIC UNION ALL
# MAGIC SELECT 'order_items', COUNT(*) FROM practice_ecommerce.bronze.order_items;