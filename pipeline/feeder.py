# -*- coding: utf-8 -*-

from datetime import date
from pyspark.sql import SparkSession, functions as F
import argparse
import logging
import time
import sys


# =========================
# ARGUMENTS
# =========================

parser = argparse.ArgumentParser()

parser.add_argument("--traffic_input", required=True)
parser.add_argument("--output_traffic", required=True)
parser.add_argument("--output_air", required=True)

parser.add_argument("--mysql_host", required=True)
parser.add_argument("--mysql_port", required=True)
parser.add_argument("--mysql_database", required=True)
parser.add_argument("--mysql_table", required=True)
parser.add_argument("--mysql_user", required=True)
parser.add_argument("--mysql_password", required=True)

args = parser.parse_args()


# =========================
# LOGGING
# =========================

logging.basicConfig(
    filename="feeder.txt",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger(__name__)

logger.info("========== FEEDER JOB STARTED ==========")


# =========================
# SPARK SESSION
# =========================

spark = (
    SparkSession.builder
    .appName("feeder")
    .getOrCreate()
)

logger.info("Spark session created successfully")


try:

    # =========================
    # READ TRAFFIC CSV
    # =========================

    logger.info("Reading traffic CSV")

    traffic_df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "false")
        .csv(args.traffic_input)
    )

    logger.info("Traffic CSV loaded successfully")


    # =========================
    # READ AIR QUALITY MYSQL
    # =========================

    logger.info("Reading air quality data from MySQL")

    jdbc_url = (
        "jdbc:mysql://{}:{}/{}"
        "?allowPublicKeyRetrieval=true"
        "&useSSL=false"
        "&permitMysqlScheme=true"
    ).format(
        args.mysql_host,
        args.mysql_port,
        args.mysql_database
    )

    air_quality_df = (
        spark.read
        .format("jdbc")
        .option("url", jdbc_url)
        .option("driver", "org.mariadb.jdbc.Driver")
        .option("user", args.mysql_user)
        .option("password", args.mysql_password)
        .option("dbtable", args.mysql_table)
        .load()
    )

    logger.info("Air quality data loaded successfully")


    # =========================
    # ADD PARTITION COLUMNS
    # =========================

    today = date.today()

    traffic_df2 = (
        traffic_df
        .withColumn("year", F.lit(today.year))
        .withColumn("month", F.lit(today.month))
        .withColumn("day", F.lit(today.day))
    )

    air_quality_df2 = (
        air_quality_df
        .withColumn("year", F.lit(today.year))
        .withColumn("month", F.lit(today.month))
        .withColumn("day", F.lit(today.day))
    )

    logger.info("Partition columns added successfully")


    # =========================
    # FORCE CACHE
    # =========================

    logger.info("Caching traffic dataframe")
    traffic_df2.cache()
    traffic_count = traffic_df2.count()
    logger.info("Traffic dataframe cached successfully")



    # =========================
    # COUNT ROWS
    # =========================


    air_count = air_quality_df2.count()
    print("Traffic rows :", traffic_count)
    print("Air quality rows :", air_count)

    logger.info("Traffic rows : {}".format(traffic_count))
    logger.info("Air quality rows : {}".format(air_count))


    # =========================
    # WAIT FOR SPARK UI
    # =========================

    time.sleep(10)


    # =========================
    # WRITE TRAFFIC RAW
    # =========================

    logger.info("Writing traffic RAW data")

    (
        traffic_df2
        .repartition(2)
        .write
        .mode("overwrite")
        .partitionBy("year", "month", "day")
        .parquet(args.output_traffic)
    )

    logger.info("Traffic RAW data written successfully")


    # =========================
    # WRITE AIR QUALITY RAW
    # =========================

    logger.info("Writing air quality RAW data")

    (
        air_quality_df2
        .repartition(2)
        .write
        .mode("overwrite")
        .partitionBy("year", "month", "day")
        .parquet(args.output_air)
    )

    logger.info("Air quality RAW data written successfully")


    # =========================
    # UNPERSIST
    # =========================

    traffic_df2.unpersist()

    logger.info("traffic_df2 unpersisted successfully")


    print("Data successfully written to HDFS")

    logger.info("========== FEEDER JOB COMPLETED ==========")


except Exception as e:

    logger.exception("ERROR IN FEEDER JOB")

    print("Error :", str(e))

    sys.exit(1)


finally:

    spark.stop()

    logger.info("Spark session stopped")