# -*- coding: utf-8 -*-
 
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.window import Window
from itertools import chain
import argparse
import logging
import time
import sys
 
 
# =========================
# ARGUMENTS
# =========================
 
parser = argparse.ArgumentParser()
 
parser.add_argument("--air_input", required=True)
parser.add_argument("--traffic_input", required=True)
parser.add_argument("--silver_output", required=True)
 
args = parser.parse_args()
 
 
# =========================
# LOGGING
# =========================
 
logging.basicConfig(
    filename="processor.txt",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
 
logger = logging.getLogger(__name__)
 
logger.info("========== PROCESSOR JOB STARTED ==========")
 
 
# =========================
# SPARK SESSION
# =========================
 
spark = (
    SparkSession.builder
    .appName("processor")
    .enableHiveSupport()
    .getOrCreate()
)
 
logger.info("Spark session created successfully")
 
 
try:
 
    # =========================
    # READ RAW DATA
    # =========================
 
    logger.info("Reading RAW datasets")
 
    air_df = spark.read.parquet(args.air_input)
 
    traffic_df = spark.read.parquet(args.traffic_input)
 
    logger.info("RAW datasets loaded successfully")
 
 
    # =========================
    # VALIDATION RULES
    # =========================
 
    logger.info("Applying validation rules")
 
    # AIR QUALITY VALIDATIONS
 
    air_df = (
        air_df
        .filter(F.col("pollution_value").isNotNull())
        .filter(F.col("air_quality_index") >= 0)
        .filter(
            (F.col("temperature") >= -50) &
            (F.col("temperature") <= 60)
        )
        .filter(
            (F.col("humidity") >= 0) &
            (F.col("humidity") <= 100)
        )
        .filter(
            (F.col("latitude") >= -90) &
            (F.col("latitude") <= 90)
        )
    )
 
    # TRAFFIC VALIDATIONS
 
    traffic_df = (
        traffic_df
        .filter(F.col("debit_horaire").isNotNull())
        .filter(F.col("debit_horaire") >= 0)
        .filter(F.col("etat_arc") == "Ouvert")
    )
 
    logger.info("Validation rules applied successfully")
 
 
    # =========================
    # CREATE HOUR COLUMNS
    # =========================
 
    logger.info("Creating hour columns")
 
    air_df = air_df.withColumn(
        "hour",
        F.hour(
            F.to_timestamp(
                "datetime",
                "dd/MM/yyyy HH:mm"
            )
        )
    )
 
    traffic_df = traffic_df.withColumn(
        "hour",
        F.hour(
            F.to_timestamp(
                "date_et_heure_de_comptage"
            )
        )
    )
 
    logger.info("Hour columns created successfully")
 
 
    # =========================
    # NORMALIZE ZONES
    # =========================
 
    logger.info("Normalizing zone names")
 
    air_df = air_df.withColumn(
        "zone",
        F.lower(
            F.regexp_replace(
                F.regexp_replace(F.col("station"), "-", "_"),
                " ",
                "_"
            )
        )
    )
 
    traffic_df = traffic_df.withColumn(
        "zone",
        F.lower(
            F.regexp_replace(
                F.regexp_replace(F.col("libelle"), "Bd_", ""),
                " ",
                "_"
            )
        )
    )
 
    logger.info("Zone normalization completed")
 
 
    # =========================
    # ZONE MAPPING (traffic -> air)
    # =========================
 
    logger.info("Applying zone mapping")
 
    zone_mapping = {
 
        # saint_michel
        "st_michel"              : "saint_michel",
        "quai_st_michel"         : "saint_michel",
        "pt_st_michel"           : "saint_michel",
        "gay_lussac"             : "saint_michel",
        "monge"                  : "saint_michel",
        "lagrange"               : "saint_michel",
 
        # nation
        "pl_de_la_nation"        : "nation",
        "cours_de_vincennes"     : "nation",
        "av_du_trone"            : "nation",
        "davout"                 : "nation",
        "soult"                  : "nation",
        "av_ph_Auguste"          : "nation",
        "philippe_auguste"       : "nation",
        "roquette"               : "nation",
        "av_ledru_rollin"        : "nation",
        "ledru_rollin"           : "nation",
 
        # gare_du_nord
        "magenta"                : "gare_du_nord",
        "maubeuge"               : "gare_du_nord",
        "marx_dormoy"            : "gare_du_nord",
        "max_dormoy"             : "gare_du_nord",
        "la_fayette"             : "gare_du_nord",
        "ornano"                 : "gare_du_nord",
        "barbes"                 : "gare_du_nord",
        "de_rochechouart"        : "gare_du_nord",
        "poissonniere"           : "gare_du_nord",
        "rue_fbg_st_denis"       : "gare_du_nord",
        "rue_du_fbg_st_denis"    : "gare_du_nord",
 
        # paris_centre
        "rivoli"                 : "paris_centre",
        "rue_de_rivoli"          : "paris_centre",
        "du_palais"              : "paris_centre",
        "cite"                   : "paris_centre",
        "petit_pont"             : "paris_centre",
        "rue_du_petit_pont"      : "paris_centre",
        "pt_notre_dame"          : "paris_centre",
        "pt_au_change"           : "paris_centre",
        "quai_de_la_megisserie"  : "paris_centre",
        "quai_hotel_de_ville"    : "paris_centre",
        "pl_hotel_de_ville"      : "paris_centre",
        "carrousel"              : "paris_centre",
        "pl_du_carrousel"        : "paris_centre",
        "pt_du_carrousel"        : "paris_centre",
        "pt_carrousel"           : "paris_centre",
        "pyramides"              : "paris_centre",
        "4_septembre"            : "paris_centre",
 
 
    }
 
    mapping_expr = F.create_map([F.lit(x) for x in chain(*zone_mapping.items())])
 
    traffic_df = traffic_df.withColumn(
        "zone",
        F.coalesce(
            mapping_expr[F.col("zone")],
            F.col("zone")
        )
    )
 
    logger.info("Zone mapping applied successfully")
 
 
    # =========================
    # SELECT USEFUL COLUMNS
    # =========================
 
    air_df = air_df.select(
        "zone",
        "hour",
        "pollution_value",
        "air_quality_index",
        "temperature",
        "humidity",
        "year",
        "month",
        "day"
    )
 
    traffic_df = traffic_df.select(
        "zone",
        "hour",
        "debit_horaire"
    )
 
 
    # =========================
    # JOIN DATASETS
    # =========================
 
    logger.info("Joining datasets")
 
    joined_df = (
        air_df.join(
            traffic_df,
            ["zone", "hour"],
            "inner"
        )
    )
 
    logger.info("Datasets joined successfully")
 
 
    # =========================
    # CACHE
    # =========================
 
    logger.info("Applying cache")
 
    joined_df.cache()
 
    joined_count = joined_df.count()
 
    logger.info(
        "Cache applied successfully : {} rows".format(joined_count)
    )
 
 
    # =========================
    # LIGHT AGGREGATION
    # =========================
 
    logger.info("Running aggregation")
 
    traffic_stats_df = (
        joined_df
        .groupBy("hour")
        .agg(
            F.avg("debit_horaire").alias("avg_hourly_traffic")
        )
    )
 
    traffic_stats_df.show()
 
    logger.info("Aggregation completed successfully")
 
 
    # =========================
    # WINDOW FUNCTION
    # =========================
 
    logger.info("Applying window function")
 
    window_spec = (
        Window
        .partitionBy("zone")
        .orderBy("hour")
    )
 
    joined_df = joined_df.withColumn(
        "rolling_avg_pollution",
        F.avg("pollution_value").over(window_spec)
    )
 
    logger.info("Window function applied successfully")
 
 
    # =========================
    # WAIT FOR SPARK UI
    # =========================
 
    time.sleep(10)
 
 
    # =========================
    # WRITE SILVER PARQUET
    # =========================
 
    logger.info("Writing SILVER parquet data")
 
    (
        joined_df
        .repartition(2)
        .write
        .mode("overwrite")
        .format("parquet")
        .partitionBy("year", "month", "day")
        .save(args.silver_output)
    )
 
    logger.info("SILVER parquet data written successfully")
 
 
    # =========================
    # CREATE HIVE TABLE
    # =========================
 
    logger.info("Creating Hive table")
 
    spark.sql("DROP TABLE IF EXISTS default.air_traffic_silver")
 
    create_table_query = """
    CREATE TABLE IF NOT EXISTS default.air_traffic_silver
    USING PARQUET
    PARTITIONED BY (year, month, day)
    LOCATION '{}'
    """.format(args.silver_output)
 
    spark.sql(create_table_query)
 
    logger.info("Hive table created successfully")
 
 
    # =========================
    # UNPERSIST
    # =========================
 
    joined_df.unpersist()
 
    logger.info("Cache removed successfully")
 
 
    print("Processor completed successfully")
 
    logger.info("========== PROCESSOR JOB COMPLETED ==========")
 
 
except Exception as e:
 
    logger.exception("ERROR IN PROCESSOR JOB")
 
    print("Error :", str(e))
 
    sys.exit(1)
 
 
finally:
 
    spark.stop()
 
    logger.info("Spark session stopped")