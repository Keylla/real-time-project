import json
import yaml
from kafka import KafkaConsumer
from pymongo import MongoClient

# Carregar configurações do arquivo YAML
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Verifica se o arquivo de configuração foi carregado corretamente
if not config:
    raise ValueError("Erro ao carregar o arquivo de configuração config.yaml")

print("Keys encontradas no arquivo de configuração:", config.keys())

# Verifica se as chaves necessárias estão presentes
required_keys = ["kafka", "mongo"]
for key in required_keys:
    if key not in config:
        raise KeyError(f"Chave '{key}' não encontrada no arquivo de configuração config.yaml")
    
print("Configuração kafka: ", config.get("kafka"))
print("Configuração mongo: ", config.get("mongo"))

# Extração segura das variáveis
kafka_config = config.get("kafka", {})
mongo_config = config.get("mongo", {})

# Validação básica (opcional, mas recomendável)
if not kafka_config.get("bootstrap_servers"):
    raise ValueError("Kafka bootstrap_servers não definido no config.yaml")

if not mongo_config.get("mongo_uri"):
    raise ValueError("MongoDB URI não definido no config.yaml")

# Inicializa o consumidor Kafka
consumer = KafkaConsumer(
    kafka_config.get("topic", "trips"),
    bootstrap_servers=kafka_config.get("bootstrap_servers"),
    auto_offset_reset="earliest",
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)

# Conecta ao MongoDB Atlas
mongo = MongoClient(mongo_config["mongo_uri"])
db = mongo[mongo_config.get("mongo_db", "tripsdb")]
collection = db[mongo_config.get("mongo_collection", "trips")]

# Processa as mensagens
for message in consumer:
    trip = message.value
    collection.insert_one(trip)
    print(f"Armazenado: {trip}")
