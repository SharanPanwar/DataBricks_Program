from delta.tables import DeltaTable

target = DeltaTable.forName(
    spark,
    "investment_dev.silver.trades"
)

source = spark.table(
    "investment_dev.bronze.trades"
)

(
    target.alias("target")
    .merge(
        source.alias("source"),
        "target.trade_id = source.trade_id"
    )
    .whenMatchedUpdateAll()
    .whenNotMatchedInsertAll()
    .execute()
)

spark.sql("""
DESCRIBE HISTORY investment_dev.silver.trades
""").display()