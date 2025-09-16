import json
import yaml
from kafka import KafkaConsumer
from pymongo import MongoClient
import os

# Carregar configurações do arquivo
kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
kafka_topic = os.getenv("KAFKA_TOPIC")
mongo_uri = os.getenv("MONGO_URI")
mongo_db = os.getenv("MONGO_DB")
mongo_collection = os.getenv("MONGO_COLLECTION")

if not kafka_servers:
    raise ValueError("Kafka bootstrap_servers não definido no .env")

if not kafka_topic:
    raise ValueError("Kafka topic não definido no .env")

if not mongo_uri:
    raise ValueError("MongoDB URI não definido no .env")

if not mongo_db:
    raise ValueError("MongoDB database não definido no .env")

if not mongo_collection:
    raise ValueError("MongoDB collection não definida no .env")

# Inicializa o consumidor Kafka
consumer = KafkaConsumer(
    kafka_topic,
    bootstrap_servers=kafka_servers,
    auto_offset_reset="earliest",
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)

# Conecta ao MongoDB Atlas
mongo = MongoClient(mongo_uri)
db = mongo[mongo_db]
collection = db[mongo_collection]

# Processa as mensagens
for message in consumer:
    trip = message.value
    collection.insert_one(trip)
    print(f"Armazenado: {trip}")
