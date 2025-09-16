import json
import time
import random
from kafka import KafkaProducer
from faker import Faker
import os

# Criar uma instância do Faker
faker = Faker()

# Carregar configurações do arquivo
kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
kafka_topic = os.getenv("KAFKA_TOPIC")

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

while True:
    trip = generate_trip()
    producer.send(kafka_topic, value=trip)
    print(f"Sent trip: {trip}")
    time.sleep(2)
