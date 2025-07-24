import streamlit as st
import plotly.express as px
import pandas as pd
from pymongo import MongoClient
import time
import os
import requests

# Carregar configurações do arquivo
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

# Função para conectar ao MongoDB
def get_data():    
    mongo = MongoClient(mongo_uri)
    db = mongo[mongo_db]
    collection = db[mongo_collection]
    data = list(collection.find())
    df = pd.DataFrame(data)
    if df.empty:
        st.warning("Nenhum dado encontrado na coleção.")
        return pd.DataFrame()  # Retorna um DataFrame vazio se não houver dados
    if '_id' in df.columns:
        df.drop(columns=['_id'], inplace=True)
    return df

# Layout Streamlit
st.set_page_config(page_title="Dashboard de Viagens", layout="wide")
st.title("🚗 Painel de Monitoramento de Viagens")

runningProducer = st.toggle("Executar Producer")
statusProducer = st.empty()
if runningProducer:    
    requests.post("http://api:5001/producer/start")
    statusProducer.success("🟢 Producer está em execução.")
else:
    statusProducer.warning("⏳ Parando Producer...")
    requests.post("http://api:5001/producer/stop")
    statusProducer.warning("🔴 Producer Parado...")


runningConsumer = st.toggle("Executar Consumer")
statusConsumer = st.empty()
if runningConsumer:
    requests.post("http://api:5001/consumer/start")
    statusConsumer.success("🟢 Consumer está em execução.")
    
else:
    statusConsumer.warning("⏳ Parando Consumer...")
    requests.post("http://api:5001/consumer/stop")
    statusConsumer.warning("🔴 Consumer Parado...")

# Carregar dados
st.subheader("📊 Dados Recebidos")
auto_refresh = st.toggle("Atualização automática", value=False)

if auto_refresh:
    placeholder = st.empty()
    while True:
        try:
            df = get_data()
            with placeholder.container():
                st.dataframe(df)

                if "distance_km" in df.columns:
                    df["distance_km"] = df["distance_km"].astype(float)
                    fig = px.histogram(df, x="distance_km", nbins=20, title="Distribuição de Distâncias (km)")
                    st.plotly_chart(fig)
            time.sleep(5)  # atualiza a cada 5 segundos
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            break
else:
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