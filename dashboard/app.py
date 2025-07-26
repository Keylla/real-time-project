import streamlit as st
import plotly.express as px
import pandas as pd
from pymongo import MongoClient
import time
import os
import requests


# --- Configurações e Conexão ---
kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
kafka_topic = os.getenv("KAFKA_TOPIC")
mongo_uri = os.getenv("MONGO_URI")
mongo_db = os.getenv("MONGO_DB")
mongo_collection = os.getenv("MONGO_COLLECTION")

if not kafka_servers:
    raise ValueError("Kafka bootstrap_servers não definido no .env")

if not mongo_uri:
    raise ValueError("MongoDB URI não definido no .env")

if not mongo_db:
    raise ValueError("MongoDB database não definido no .env")

if not mongo_collection:
    raise ValueError("MongoDB collection não definida no .env")

# Função para conectar ao MongoDB e buscar dados ordenados
@st.cache_data(ttl=5) # Cacheia os dados por 5 segundos para evitar chamadas excessivas ao DB
def get_data():
    mongo = MongoClient(mongo_uri)
    db = mongo[mongo_db]
    collection = db[mongo_collection]
    
    # Ordena os dados pelo _id de forma decrescente (mais recente primeiro)
    data = list(collection.find().sort('_id', -1)) 
    
    df = pd.DataFrame(data)
    if df.empty:
        st.warning("Nenhum dado encontrado na coleção.")
        return pd.DataFrame()
    if '_id' in df.columns:
        df.drop(columns=['_id'], inplace=True)
    return df

# --- Funções de Callback para os Toggles ---

def toggle_producer_status():
    if st.session_state.running_producer: # Se o toggle foi marcado para "ligar"
        st.session_state.producer_status_message = "⏳ Iniciando Producer..."
        resp = requests.post("http://api:5001/producer/start")
        if resp.status_code == 200:
            st.session_state.producer_status_message = "🟢 Producer está em execução."
        else:
            st.session_state.producer_status_message = f"❌ Erro ao iniciar Producer: {resp.text}"
            st.session_state.running_producer = False # Volta o toggle se houver erro
    else: # Se o toggle foi marcado para "desligar"
        st.session_state.producer_status_message = "⏳ Parando Producer..."
        resp = requests.post("http://api:5001/producer/stop")
        if resp.status_code == 200:
            st.session_state.producer_status_message = "🔴 Producer Parado."
        else:
            st.session_state.producer_status_message = f"❌ Erro ao parar Producer: {resp.text}"
            st.session_state.running_producer = True # Volta o toggle se houver erro

def toggle_consumer_status():
    if st.session_state.running_consumer: # Se o toggle foi marcado para "ligar"
        st.session_state.consumer_status_message = "⏳ Iniciando Consumer..."
        resp = requests.post("http://api:5001/consumer/start")
        if resp.status_code == 200:
            st.session_state.consumer_status_message = "🟢 Consumer está em execução."
        else:
            st.session_state.consumer_status_message = f"❌ Erro ao iniciar Consumer: {resp.text}"
            st.session_state.running_consumer = False # Volta o toggle se houver erro
    else: # Se o toggle foi marcado para "desligar"
        st.session_state.consumer_status_message = "⏳ Parando Consumer..."
        resp = requests.post("http://api:5001/consumer/stop")
        if resp.status_code == 200:
            st.session_state.consumer_status_message = "🔴 Consumer Parado."
        else:
            st.session_state.consumer_status_message = f"❌ Erro ao parar Consumer: {resp.text}"
            st.session_state.running_consumer = True # Volta o toggle se houver erro

# --- Layout Streamlit ---
st.set_page_config(page_title="Dashboard de Viagens", layout="wide")
st.title("🚗 Painel de Monitoramento de Viagens")

# Inicializa o estado da sessão para os toggles e mensagens de status
if 'running_producer' not in st.session_state:
    st.session_state.running_producer = False
    st.session_state.producer_status_message = "🔴 Producer Parado."
if 'running_consumer' not in st.session_state:
    st.session_state.running_consumer = False
    st.session_state.consumer_status_message = "🔴 Consumer Parado."

# Adiciona os toggles com suas chaves de estado e callbacks
st.toggle(
    "Executar Producer",
    key="running_producer",
    on_change=toggle_producer_status
)
st.write(st.session_state.producer_status_message) # Exibe a mensagem de status

st.toggle(
    "Executar Consumer",
    key="running_consumer",
    on_change=toggle_consumer_status
)
st.write(st.session_state.consumer_status_message) # Exibe a mensagem de status

# --- Seção de Análise de Dados ---
st.subheader("📊 Dados Recebidos")
auto_refresh = st.toggle("Atualização automática", value=False, key="auto_refresh_data")

if auto_refresh:
    placeholder = st.empty()
    while st.session_state.auto_refresh_data:
        try:
            df = get_data()
            with placeholder.container():
                st.dataframe(df, use_container_width=True)
                
                if "distance_km" in df.columns and not df.empty: # Verifica se df não está vazio antes de plotar
                    df["distance_km"] = df["distance_km"].astype(float)
                    fig = px.histogram(df, x="distance_km", nbins=20, title="Distribuição de Distâncias (km)")
                    st.plotly_chart(fig, use_container_width=True)
                elif "distance_km" not in df.columns:
                    st.info("Coluna 'distance_km' não encontrada nos dados.")
            time.sleep(5)  # atualiza a cada 5 segundos
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            break # Sai do loop em caso de erro
else:
    if st.button("Atualizar dados", key="manual_refresh_button"):
        try:
            df = get_data()
            st.dataframe(df, use_container_width=True)

            if "distance_km" in df.columns and not df.empty:
                df["distance_km"] = df["distance_km"].astype(float)
                fig = px.histogram(df, x="distance_km", nbins=20, title="Distribuição de Distâncias (km)")
                st.plotly_chart(fig, use_container_width=True)
            elif "distance_km" not in df.columns:
                st.info("Coluna 'distance_km' não encontrada nos dados.")
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")