import json
import os
import logging
from kafka import KafkaConsumer, TopicPartition
from dotenv import load_dotenv
from connection import connect_to_mongo

# Carregar variáveis de ambiente do .env
load_dotenv()

kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
kafka_topic = os.getenv("KAFKA_TOPIC")

logging.basicConfig(level=logging.INFO)
logging.info("Consumer iniciado...")
logging.info(f"Kafka Servers: {kafka_servers}")
logging.info(f"Kafka Topic: {kafka_topic}")

if not kafka_servers:
    raise ValueError("Kafka bootstrap_servers não definido no .env")
if not kafka_topic:
    raise ValueError("Kafka topic não definido no .env")

# Inicializa o consumidor
consumer = KafkaConsumer(
    bootstrap_servers=kafka_servers,
    auto_offset_reset="earliest",
    enable_auto_commit=False,
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)

# Conecta apenas na partição 0 (assumindo tópico simples, se tiver mais partições ajusta aqui)
partition = TopicPartition(kafka_topic, 0)
consumer.assign([partition])

# Descobre até onde consumir
end_offset = consumer.end_offsets([partition])[partition]
logging.info(f"Último offset disponível: {end_offset}")

if end_offset == 0:
    logging.info("Nenhuma mensagem para consumir. Finalizando.")
    consumer.close()
    exit(0)

collection = connect_to_mongo()

processed = 0

for message in consumer:
    trip = message.value
    collection.insert_one(trip)
    logging.info(f"Armazenado: {trip}")
    processed += 1

    # Se já consumiu tudo disponível, encerra
    if message.offset + 1 >= end_offset:
        logging.info(f"Todas as mensagens ({processed}) foram consumidas. Finalizando.")
        break

consumer.close()
logging.info("Consumer finalizado com sucesso.")