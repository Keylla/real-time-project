import json
from kafka import KafkaConsumer
import os
from infrastructure import connect_to_mongo
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Carregar configurações do arquivo
kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
kafka_topic = os.getenv("KAFKA_TOPIC")

if not kafka_servers:
    raise ValueError("Kafka bootstrap_servers não definido no .env")

if not kafka_topic:
    raise ValueError("Kafka topic não definido no .env")

# Inicializa o consumidor Kafka
consumer = KafkaConsumer(
    kafka_topic,
    bootstrap_servers=kafka_servers,
    auto_offset_reset="earliest",
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)

# Conecta ao MongoDB Atlas
collection = connect_to_mongo()

if not collection:
    raise ValueError("Falha ao conectar à coleção MongoDB")

# Processa as mensagens
for message in consumer:
    trip = message.value
    collection.insert_one(trip)
    print(f"Armazenado: {trip}")
