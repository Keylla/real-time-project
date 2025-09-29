import json
import time
import random
from kafka import KafkaProducer
from faker import Faker
import os
import logging

# Criar uma instância do Faker
faker = Faker()

# Carregar configurações do arquivo
kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
kafka_topic = os.getenv("KAFKA_TOPIC")

logging.basicConfig(level=logging.INFO)
logging.info("Producer iniciado...")
logging.info(f"Kafka Servers: {kafka_servers}")
logging.info(f"Kafka Topic: {kafka_topic}")

if not kafka_servers:
    raise ValueError("Kafka bootstrap_servers não definido no .env")

if not kafka_topic:
    raise ValueError("Kafka topic não definido no .env")

producer = KafkaProducer(
    bootstrap_servers=kafka_servers,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def generate_trip():
    return {
        "partner_id": faker.uuid4(),
        "trip_id": faker.uuid4(),
        "start_time": faker.date_time_this_year().isoformat(),
        "end_time": faker.date_time_this_year().isoformat(),
        "distance_km": round(random.uniform(1, 100), 2),
        "city": faker.city()
    }

import time

# --- Variável para o limite de registros ---
MAX_RECORDS = 250
# ------------------------------------------

counter = 0

# O loop continua enquanto o contador for menor que o limite
while counter < MAX_RECORDS:
    trip = generate_trip()
    
    # Envia a mensagem para o Kafka
    producer.send(kafka_topic, value=trip)
    
    # Imprime e incrementa o contador
    print(f"Sent trip {counter + 1}/{MAX_RECORDS}: {trip}")
    counter += 1
    
    # Pausa entre as mensagens
    time.sleep(2)

# Mensagem de finalização após o loop
print(f"--- FIM: 250 registros de viagem gerados e enviados para o Kafka. ---")
