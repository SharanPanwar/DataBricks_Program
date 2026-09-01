# Databricks notebook source
CATALOG = "practice_ecommerce"
SILVER = f"{CATALOG}.silver"
GOLD = f"{CATALOG}.gold"

# COMMAND ----------

# DBTITLE 1,Gold Table
#includes only completed orders (excludes pending, cancelled)
#aggregation by order date
daily_sales_summary = spark.sql(f"""
    SELECT
        order_date,
        COUNT(DISTINCT order_id) AS total_orders,
        COUNT(order_item_id) AS total_line_items,
        ROUND(SUM(line_total), 2) AS total_revenue,
        ROUND(SUM(line_total) / COUNT(DISTINCT order_id), 2) AS avg_order_value,
        COUNT(DISTINCT customer_id) AS unique_customers
    FROM {SILVER}.order_lines_enriched
    WHERE order_status = 'completed'
    GROUP BY order_date
    ORDER BY order_date
""")

daily_sales_summary.write.mode("overwrite").saveAsTable(f"{GOLD}.daily_sales_summary")
display(daily_sales_summary)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM practice_ecommerce.gold.daily_sales_summary ORDER BY order_date;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     SUM(total_orders) AS orders,
# MAGIC     SUM(total_line_items) AS line_items,
# MAGIC     ROUND(SUM(total_revenue), 2) AS revenue
# MAGIC FROM practice_ecommerce.gold.daily_sales_summary;

# COMMAND ----------

# DBTITLE 1,post job verification run
# MAGIC %sql
# MAGIC SELECT * FROM practice_ecommerce.gold.daily_sales_summary ORDER BY order_date;