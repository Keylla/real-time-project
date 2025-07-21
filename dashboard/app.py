import streamlit as st
import plotly.express as px
import pandas as pd
from pymongo import MongoClient
import yaml
import os

# Carrega o config.yaml
config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
#config_path = os.getenv("CONFIG_PATH", "config.yaml")

with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

# Verifica se o arquivo de configuração foi carregado corretamente
if not config:
    raise ValueError("Erro ao carregar o arquivo de configuração config.yaml")

# Verifica se as chaves necessárias estão presentes
required_keys = ["kafka", "mongo"]
for key in required_keys:
    if key not in config:
        raise KeyError(f"Chave '{key}' não encontrada no arquivo de configuração config.yaml")
    
# Extração segura das variáveis
kafka_config = config.get("kafka", {})
mongo_config = config.get("mongo", {})

# Validação básica (opcional, mas recomendável)
if not kafka_config.get("bootstrap_servers"):
    raise ValueError("Kafka bootstrap_servers não definido no config.yaml")

if not mongo_config.get("mongo_uri"):
    raise ValueError("MongoDB URI não definido no config.yaml")

# Função para conectar ao MongoDB
def get_data():    
    mongo = MongoClient(mongo_config["mongo_uri"])
    print(f"Conectando ao MongoDB em: {mongo_config['mongo_uri']}")
    db = mongo[mongo_config.get("mongo_db", "tripsdb")]
    print(f"Banco de dados selecionado: {mongo_config.get('mongo_db', 'tripsdb')}")
    collection = db[mongo_config.get("mongo_collection", "trips")]
    print(f"Coleção selecionada: {mongo_config.get('mongo_collection', 'trips')}")
    data = list(collection.find())
    df = pd.DataFrame(data)
    print(f"Dados carregados: {len(df)} registros")
    print(df)
    if '_id' in df.columns:
        df.drop(columns=['_id'], inplace=True)
    return df

# Layout Streamlit
st.set_page_config(page_title="Dashboard de Viagens", layout="wide")
st.title("🚗 Painel de Monitoramento de Viagens")

#col1, col2 = st.columns(2)

runningProducer = st.toggle("Executar Producer")
runningConsumer = st.toggle("Executar Consumer")

#with col1:
if runningProducer:
    st.success("Producer está em execução.")
    os.system("docker-compose start producer")
else:
    st.warning("Parando Producer...")
    os.system("docker-compose stop producer")

if runningConsumer:
    st.success("Consumer está em execução.")
    os.system("docker-compose start consumer")
else:
    st.warning("Parando Consumer...")
    os.system("docker-compose stop consumer")

# Carregar dados
st.subheader("Dados Recebidos")
if st.button("Atualizar dados"):
    try:
        df = get_data()
        st.dataframe(df)

        if "distance_km" in df.columns:
            df["distance_km"] = df["distance_km"].astype(float)
            fig = px.histogram(df, x="distance_km", nbins=20, title="Distribuição de Distâncias (km)")
            st.plotly_chart(fig)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
