import json
import time
import random
from kafka import KafkaProducer
from faker import Faker
import os
import logging
from dotenv import load_dotenv
import time
import datetime

# Carregar variáveis de ambiente do arquivo .env

load_dotenv()

# Criar uma instância do Faker
faker = Faker('pt_BR') # Usando pt_BR para cidades e ruas brasileiras

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
    # 1. Geração de Start e End Time em Ordem
    # Gera um timestamp inicial aleatório dentro do ano atual
    start_dt = faker.date_time_this_year()
    
    # Gera o timestamp final, garantindo que seja após o start_dt (de 1 a 6 horas depois)
    end_dt = start_dt + datetime.timedelta(hours=random.randint(1, 6), minutes=random.randint(1, 59))
    
    # 2. Geração da Coerência Geográfica
    # Usa um gerador de localização que produz lat/long e endereço
    latitude = faker.latitude()
    longitude = faker.longitude()
    
    # O Faker BR não tem 'neighborhood' nativo, então simulamos com partes do endereço
    city_name = faker.city()
    street_name = faker.street_name()
    
    # Simula um bairro simples para manter a coerência
    neighborhood_name = f"{city_name} - Bairro {faker.last_name()}"

    return {
        "timestamp": datetime.datetime.now().isoformat(), # Timestamp da geração do registro
        "partner_id": faker.uuid4(),
        "trip_id": faker.uuid4(),
        
        # Campos Temporais
        "start_time": start_dt.isoformat(),
        "end_time": end_dt.isoformat(),
        
        # Campos Geográficos
        "latitude": float(latitude),
        "longitude": float(longitude),
        "city": city_name,
        "neighborhood": neighborhood_name,
        "street": street_name,
        
        # Outros Campos
        "distance_km": round(random.uniform(1, 100), 2),
        "price": round(random.uniform(5, 500), 2),
    }

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

# Mensagem de finalização após o loop
print(f"--- FIM: 250 registros de viagem gerados e enviados para o Kafka. ---")
