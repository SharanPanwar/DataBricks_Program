from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.appName(
    "InvestmentDataPlatform"
).getOrCreate()

# Read sample trades
trades_df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv("/Volumes/investment_dev/raw/trades/trades.csv")
)

# Inspect schema
trades_df.printSchema()

# Sample records
display(trades_df.limit(10))

# Select required columns
trades = trades_df.select(
    "trade_id",
    "trade_ts",
    "portfolio_id",
    "security_id",
    "side",
    "quantity",
    "price",
    "trader_id"
)

# Calculate trade value
trades = trades.withColumn(
    "trade_value",
    F.col("quantity") * F.col("price")
)

# Filter valid trades
valid_trades = trades.filter(
    (F.col("quantity") > 0) &
    (F.col("price") > 0)
)

# Portfolio summary
portfolio_summary = (
    valid_trades
    .groupBy("portfolio_id")
    .agg(
        F.count("*").alias("trade_count"),
        F.sum("quantity").alias("total_quantity"),
        F.sum("trade_value").alias("gross_trade_value")
    )
    .orderBy(F.desc("gross_trade_value"))
)

display(portfolio_summary)