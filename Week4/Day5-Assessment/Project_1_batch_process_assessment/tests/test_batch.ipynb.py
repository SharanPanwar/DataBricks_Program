# Databricks notebook source
def test_trade_value(spark):
    df = spark.createDataFrame([(2, 10.5)], ["quantity","price"])
    row = df.selectExpr("quantity * price as trade_value").first()
    assert float(row.trade_value) == 21.0


# COMMAND ----------

def test_valid_sides():
    assert {"BUY","SELL"}.issuperset({"BUY"})