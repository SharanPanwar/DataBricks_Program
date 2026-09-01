# Databricks notebook source
# DBTITLE 1,Config
CATALOG = "practice_ecommerce"
BRONZE = f"{CATALOG}.bronze"
SILVER = f"{CATALOG}.silver"

# COMMAND ----------

# DBTITLE 1,Silver : Customers
from pyspark.sql.functions import trim, lower, upper, to_date, col
from pyspark.sql.window import Window

df = spark.table(f"{BRONZE}.customers")

silver_customers = (
    df
    .withColumn("first_name", trim(col("first_name")))
    .withColumn("last_name", trim(col("last_name")))
    .withColumn("email", lower(trim(col("email"))))
    .withColumn("country", upper(trim(col("country"))))
    .withColumn("signup_date", to_date(col("signup_date")))
    .dropDuplicates(["customer_id"])
)

silver_customers.write.mode("overwrite").saveAsTable(f"{SILVER}.customers")
print(f"silver.customers: {silver_customers.count()} rows")

# COMMAND ----------

# DBTITLE 1,Silver : Products
from pyspark.sql.functions import trim, lower, coalesce, lit, col

df = spark.table(f"{BRONZE}.products")

silver_products = (
    df
    .withColumn("product_name", trim(col("product_name")))
    .withColumn("category", lower(trim(col("category"))))
    .withColumn("unit_price", col("unit_price").cast("decimal(10,2)"))
    .withColumn("stock_qty", coalesce(col("stock_qty").cast("int"), lit(0)))
)

silver_products.write.mode("overwrite").saveAsTable(f"{SILVER}.products")
print(f"silver.products: {silver_products.count()} rows")

# COMMAND ----------

# DBTITLE 1,Silver : Orders
from pyspark.sql.functions import trim, lower, coalesce, try_to_date, col

df = spark.table(f"{BRONZE}.orders")
valid_customers = spark.table(f"{SILVER}.customers").select("customer_id")

silver_orders = (
    df
    .withColumn(
        "order_date",
        coalesce(
            try_to_date(col("order_date").cast("string"), "yyyy-MM-dd"),
            try_to_date(col("order_date").cast("string"), "MM/dd/yyyy")
        )
    )
    .withColumn("order_status", lower(trim(col("order_status"))))
    .withColumn("total_amount", col("total_amount").cast("decimal(10,2)"))
    .join(valid_customers, "customer_id", "inner")
)

silver_orders.write.mode("overwrite").saveAsTable(f"{SILVER}.orders")
print(f"silver.orders: {silver_orders.count()} rows")

# COMMAND ----------

# DBTITLE 1,Silver : Order items
from pyspark.sql.functions import col

df = spark.table(f"{BRONZE}.order_items")
valid_orders = spark.table(f"{SILVER}.orders").select("order_id")
valid_products = spark.table(f"{SILVER}.products").select("product_id")

silver_order_items = (
    df
    .dropDuplicates(["order_item_id"])
    .withColumn("quantity", col("quantity").cast("int"))
    .withColumn("unit_price", col("unit_price").cast("decimal(10,2)"))
    .withColumn("line_total", col("line_total").cast("decimal(10,2)"))
    .join(valid_orders, "order_id", "inner")
    .join(valid_products, "product_id", "inner")
)

silver_order_items.write.mode("overwrite").saveAsTable(f"{SILVER}.order_items")
print(f"silver.order_items: {silver_order_items.count()} rows")

# COMMAND ----------

# DBTITLE 1,Verification SQL
# MAGIC %sql
# MAGIC SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM practice_ecommerce.silver.customers
# MAGIC UNION ALL
# MAGIC SELECT 'products', COUNT(*) FROM practice_ecommerce.silver.products
# MAGIC UNION ALL
# MAGIC SELECT 'orders', COUNT(*) FROM practice_ecommerce.silver.orders
# MAGIC UNION ALL
# MAGIC SELECT 'order_items', COUNT(*) FROM practice_ecommerce.silver.order_items;

# COMMAND ----------

order_lines_enriched = spark.sql(f"""
    SELECT
        oi.order_item_id,
        oi.order_id,
        o.order_date,
        o.order_status,
        o.customer_id,
        c.first_name,
        c.last_name,
        c.email,
        c.country,
        oi.product_id,
        p.product_name,
        p.category,
        oi.quantity,
        oi.unit_price,
        oi.line_total
    FROM {SILVER}.order_items oi
    INNER JOIN {SILVER}.orders o
        ON oi.order_id = o.order_id
    INNER JOIN {SILVER}.customers c
        ON o.customer_id = c.customer_id
    INNER JOIN {SILVER}.products p
        ON oi.product_id = p.product_id
""")

order_lines_enriched.write.mode("overwrite").saveAsTable(f"{SILVER}.order_lines_enriched")
print(f"silver.order_lines_enriched: {order_lines_enriched.count()} rows")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM practice_ecommerce.silver.order_lines_enriched LIMIT 10;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS row_count FROM practice_ecommerce.silver.order_lines_enriched;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT ROUND(SUM(line_total), 2) AS total_revenue
# MAGIC FROM practice_ecommerce.silver.order_lines_enriched;

# COMMAND ----------

# DBTITLE 1,post job run query
# MAGIC %sql
# MAGIC -- Bronze (unchanged if no new files)
# MAGIC SELECT 'bronze.customers' AS tbl, COUNT(*) AS cnt FROM practice_ecommerce.bronze.customers
# MAGIC UNION ALL SELECT 'silver.customers', COUNT(*) FROM practice_ecommerce.silver.customers
# MAGIC UNION ALL SELECT 'silver.order_lines_enriched', COUNT(*) FROM practice_ecommerce.silver.order_lines_enriched;