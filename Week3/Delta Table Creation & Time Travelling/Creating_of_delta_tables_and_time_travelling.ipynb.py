# Databricks notebook source
# MAGIC %sql
# MAGIC use catalog demo_catalog_sharan

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS demo_catalog_sharan.demo_schema;

# COMMAND ----------

data = [
    (101, "Ravi", "Hyderabad", 30),
    (102, "Sita", "Chennai", 25),
    (103, "John", "Bangalore", 35),
    (104, "Priya", "Mumbai", 28)
]

columns = ["customer_id", "customer_name", "city", "age"]

df = spark.createDataFrame(data, columns)

df.show()
df.printSchema()

# COMMAND ----------

df.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("demo_catalog_sharan.demo_schema.customers")

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE detail demo_catalog_sharan.demo_schema.customers;

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE IF EXISTS demo_catalog_sharan.demo_schema.customers;

# COMMAND ----------

df.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable(
        "demo_catalog_sharan.demo_schema.customers"
    )

# COMMAND ----------

# MAGIC %sql
# MAGIC --select * from demo_catalog_sharan.demo_schema.customers
# MAGIC
# MAGIC DESCRIBE HISTORY demo_catalog_sharan.demo_schema.customers

# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO demo_catalog_sharan.demo_schema.customers
# MAGIC (customer_id, customer_name, city, age)
# MAGIC VALUES
# MAGIC (106, 'Kiran', 'Delhi', 29),
# MAGIC (107, 'Meena', 'Kochi', 31),
# MAGIC (108, 'Vijay', 'Mumbai', 27);

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE HISTORY demo_catalog_sharan.demo_schema.customers

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from demo_catalog_sharan.demo_schema.customers

# COMMAND ----------

# MAGIC %sql
# MAGIC UPDATE demo_catalog_sharan.demo_schema.customers
# MAGIC SET city = 'Hyderabad'
# MAGIC WHERE customer_id = 104;

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE HISTORY demo_catalog_sharan.demo_schema.customers

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM demo_catalog_sharan.demo_schema.customers VERSION AS OF 0;
# MAGIC
# MAGIC --SELECT * FROM demo_catalog_sharan.demo_schema.customers TIMESTAMP AS OF '2026-08-24T03:23:59Z';

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM demo_catalog_sharan.demo_schema.customers VERSION AS OF 1
# MAGIC
# MAGIC EXCEPT
# MAGIC
# MAGIC SELECT *
# MAGIC FROM demo_catalog_sharan.demo_schema.customers VERSION AS OF 2;

# COMMAND ----------

# MAGIC %sql 
# MAGIC --RESTORE TABLE demo_catalog_sharan.demo_schema.customers TO VERSION AS OF 0;
# MAGIC
# MAGIC SELECT * FROM demo_catalog_sharan.demo_schema.customers

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE HISTORY demo_catalog_sharan.demo_schema.customers

# COMMAND ----------

