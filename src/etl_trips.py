from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, unix_timestamp, round, when, lit, avg, sum as _sum, count
)
import os
import logging
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

# Configurações do MongoDB
mongo_uri = os.getenv("MONGO_URI")
mongo_db = os.getenv("MONGO_DB")
mongo_collection = os.getenv("MONGO_COLLECTION")

logging.basicConfig(level=logging.INFO)
logging.info("Iniciando ETL...")
spark = SparkSession.builder \
    .appName("Trips ETL with Data Cleaning") \
    .config("spark.mongodb.read.connection.uri", mongo_uri) \
    .config("spark.mongodb.write.connection.uri", mongo_uri) \
    .getOrCreate()

# =============================
# BRONZE → PRATA
# =============================

# Lendo do MongoDB (bronze)

logging.info(f"Lendo dados do MongoDB: {mongo_uri}, DB: {mongo_db}, Collection: {mongo_collection}")

bronze_df = spark.read.format("mongodb") \
    .option("uri", os.getenv("MONGO_URI")) \
    .option("database", os.getenv("MONGO_DB")) \
    .option("collection", os.getenv("MONGO_COLLECTION")) \
    .load()

logging.info(f"Total registros lidos da camada bronze: {bronze_df.count()}")

logging.info("Iniciando limpeza e transformação dos dados...")
# Seleção e tratamento
silver_df = bronze_df.select(
    col("_id").alias("id"),
    col("partner_id"),
    col("trip_id"),
    col("latitude"),
    col("longitude"),
    when(col("city").isNull(), lit("Unknown")).otherwise(col("city")).alias("city"),
    col("neighborhood"),
    col("street"),
    col("distance_km"),
    when(col("price") < 0, lit(0)).otherwise(col("price")).alias("price"),
    col("start_time"),
    col("end_time")
).withColumn(
    "duration_min",
    round((unix_timestamp("end_time") - unix_timestamp("start_time")) / 60, 2)
)

# Remove coordenadas inválidas
silver_df = silver_df.filter(
    (col("latitude").between(-90, 90)) &
    (col("longitude").between(-180, 180))
)

logging.info(f"Total registros após limpeza na camada prata: {silver_df.count()}")

# Salva camada prata
silver_df.write.mode("overwrite").parquet("/data/silver/trips")

logging.info("Camada prata salva em /data/silver/trips")

# =============================
# PRATA → GOLD
# =============================

logging.info("Iniciando agregações para camada gold...")

gold_df = silver_df.groupBy("city").agg(
    count("trip_id").alias("total_trips"),
    round(avg("distance_km"), 2).alias("avg_distance_km"),
    round(avg("price"), 2).alias("avg_price"),
    round(_sum("price"), 2).alias("total_revenue")
)

logging.info(f"Total cidades na camada gold: {gold_df.count()}")

gold_df.write.mode("overwrite").parquet("/data/gold/trips_summary")

print("✅ ETL Finalizado com sucesso: Bronze → Prata → Gold")