# -*- coding: utf-8 -*-
 
import argparse
import logging
import sys
 
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.storagelevel import StorageLevel
 
 
# =========================
# ARGUMENTS
# =========================
 
parser = argparse.ArgumentParser(description="Datamart Job")
 
parser.add_argument("--hive_table",      required=True)
parser.add_argument("--mysql_url",       required=True)
parser.add_argument("--mysql_user",      required=True)
parser.add_argument("--mysql_password",  required=True)
parser.add_argument("--mysql_driver",    default="org.mariadb.jdbc.Driver")
 
args = parser.parse_args()
 
 
# =========================
# LOGGING
# =========================
 
logging.basicConfig(
    filename="datamart_log.txt",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
 
logger = logging.getLogger(__name__)
 
logger.info("========== DATAMART JOB STARTED ==========")
 
 
def write_to_mysql(df, table_name, args):
    """Ecrit un dataframe vers MySQL en une seule partition."""
    logger.info("Writing {} to MySQL".format(table_name))
    (
        df.coalesce(1)
        .write
        .format("jdbc")
        .option("url",      args.mysql_url)
        .option("dbtable",  table_name)
        .option("user",     args.mysql_user)
        .option("password", args.mysql_password)
        .option("driver",   args.mysql_driver)
        .mode("overwrite")
        .save()
    )
    logger.info("{} written successfully".format(table_name))
 
 
try:
 
    # =========================
    # SPARK SESSION
    # =========================
 

    spark = (
        SparkSession.builder
        .appName("Spark-Hive-Integration")
        .config(
            "spark.hadoop.hive.metastore.uris",
            "thrift://hive-metastore:9083"
        )
        .enableHiveSupport()
        .getOrCreate()
    )

    logger.info("Spark session created successfully")
 
 
    # =========================
    # READ HIVE TABLE
    # =========================
 
    logger.info("Reading silver table from Hive")
 
    silver_df = (
        spark.table(args.hive_table)
        # Reduit a 4 partitions des la lecture pour alleger la memoire
        .coalesce(4)
    )
 
    # DISK_ONLY evite de saturer la RAM contrairement a MEMORY_AND_DISK
    silver_df.persist(StorageLevel.DISK_ONLY)
 
    row_count = silver_df.count()
 
    logger.info("Silver dataframe cached : {} rows".format(row_count))
    print("Silver rows : {}".format(row_count))
 
 
    # =====================================================
    # DATAMART 1
    # WHICH ZONES ARE THE MOST POLLUTED?
    # =====================================================
 
    logger.info("Creating pollution datamart")
 
    pollution_datamart = (
        silver_df
        .groupBy("zone", "year", "month", "day")
        .agg(
            F.round(F.avg("pollution_value"),   2).alias("avg_pollution"),
            F.round(F.max("pollution_value"),   2).alias("max_pollution"),
            F.round(F.avg("air_quality_index"), 2).alias("avg_aqi")
        )
        .orderBy(F.desc("avg_pollution"))
    )
 
    pollution_datamart.show(20, False)
 
    write_to_mysql(pollution_datamart, "datamart_pollution", args)
 
    # Libere la memoire apres ecriture
    pollution_datamart.unpersist()
 
    logger.info("Pollution datamart done")
 
 
    # =====================================================
    # DATAMART 2
    # WHAT ARE THE MOST CONGESTED HOURS?
    # =====================================================
 
    logger.info("Creating traffic datamart")
 
    traffic_datamart = (
        silver_df
        .groupBy("zone", "hour", "year", "month", "day")
        .agg(
            F.round(F.avg("debit_horaire"), 2).alias("avg_traffic"),
            F.round(F.max("debit_horaire"), 2).alias("max_traffic")
        )
        .orderBy(F.desc("avg_traffic"))
    )
 
    traffic_datamart.show(20, False)
 
    write_to_mysql(traffic_datamart, "datamart_traffic", args)
 
    traffic_datamart.unpersist()
 
    logger.info("Traffic datamart done")
 
 
    # =====================================================
    # DATAMART 3
    # IS TRAFFIC RELATED TO POLLUTION?
    # =====================================================
 
    logger.info("Creating traffic pollution datamart")
 
    traffic_pollution_datamart = (
        silver_df
        .groupBy("zone", "hour", "year", "month", "day")
        .agg(
            F.round(F.avg("pollution_value"), 2).alias("avg_pollution"),
            F.round(F.avg("debit_horaire"),   2).alias("avg_traffic"),
            F.round(F.avg("temperature"),     2).alias("avg_temperature"),
            F.round(F.avg("humidity"),        2).alias("avg_humidity")
        )
        .withColumn(
            "traffic_level",
            F.when(F.col("avg_traffic") < 500, "Low Traffic")
            .when(
                (F.col("avg_traffic") >= 500) &
                (F.col("avg_traffic") < 1000),
                "Medium Traffic"
            )
            .otherwise("High Traffic")
        )
    )
 
    traffic_pollution_datamart.show(20, False)
 
    write_to_mysql(traffic_pollution_datamart, "datamart_traffic_pollution", args)
 
    traffic_pollution_datamart.unpersist()
 
    logger.info("Traffic pollution datamart done")
 
 
    # =========================
    # UNPERSIST SILVER
    # =========================
 
    silver_df.unpersist()
 
    logger.info("Cache removed successfully")
 
    print("Datamart job completed successfully")
 
    logger.info("========== DATAMART JOB COMPLETED ==========")
 
 
except Exception as e:
 
    logger.exception("ERROR IN DATAMART JOB")
 
    print("Error :", str(e))
 
    sys.exit(1)
 
 
finally:
 
    spark.stop()
 
    logger.info("Spark session stopped")
 