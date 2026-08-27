from pyspark.sql import functions as F

stream_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "<KAFKA_SERVER>")
    .option("subscribe", "trades")
    .option("startingOffsets", "latest")
    .load()
)

parsed = (
    stream_df
    .selectExpr("CAST(value AS STRING) AS json")
    .select(
        F.from_json(
            "json",
            """
            trade_id STRING,
            trade_ts TIMESTAMP,
            portfolio_id STRING,
            security_id STRING,
            side STRING,
            quantity DOUBLE,
            price DOUBLE
            """
        ).alias("trade")
    )
    .select("trade.*")
)

clean_stream = (
    parsed
    .withWatermark("trade_ts", "10 minutes")
    .dropDuplicates(["trade_id"])
)

query = (
    clean_stream.writeStream
    .format("delta")
    .outputMode("append")
    .option(
        "checkpointLocation",
        "/Volumes/investment_dev/checkpoints/trades"
    )
    .toTable("investment_dev.bronze.streaming_trades")
)