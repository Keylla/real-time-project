import streamlit as st 
import plotly.express as px
import pandas as pd
import os
import requests
from connection import connect_to_mongo

# --- Configurações e Conexão ---
st.set_page_config(page_title="CityPulse - Inteligência Geoespacial", page_icon="🌆", layout="wide")

# --- Função para buscar dados ---
@st.cache_data(ttl=5)
def get_data():
    collection = connect_to_mongo()
    data = list(collection.find().sort('_id', -1))
    df = pd.DataFrame(data)
    if df.empty:
        return pd.DataFrame()
    if '_id' in df.columns:
        df.drop(columns=['_id'], inplace=True)

    # Conversão de tipos
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
    if 'start_time' in df.columns and 'end_time' in df.columns:
        df['start_time'] = pd.to_datetime(df['start_time'])
        df['end_time'] = pd.to_datetime(df['end_time'])
        df['date'] = df['start_time'].dt.date
        df['hour'] = df['start_time'].dt.hour
        df['duration_min'] = (df['end_time'] - df['start_time']).dt.total_seconds() / 60
    if 'distance_km' in df.columns:
        df['distance_km'] = pd.to_numeric(df['distance_km'], errors='coerce')
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
    return df

# --- Estilo ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #F5F5F5; }
    .css-18e3th9, .css-1v0mbdj { color: #F5F5F5; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🗺️ Painel de Monitoramento")

# --- Abas ---
tab1, tab2, tab3 = st.tabs(["📋 Dados Brutos", "📊 Dashboard Corporativo", "❓ Perguntas"])

# =========================
# TAB 1 - Dados Brutos
# =========================
with tab1:
    st.subheader("📋 Dados Recebidos")
    df = get_data()
    if df.empty:
        st.warning("Nenhum dado disponível.")
    else:
        # Seleciona apenas as colunas desejadas
        cols = [
            "latitude", "longitude", "city", "neighborhood", "street",
            "distance_km", "price", "start_time", "end_time", "duration_min"
        ]
        available_cols = [c for c in cols if c in df.columns]  # garante que não quebre caso falte algo
         # Renomeia colunas para exibição
        rename_map = {
            "latitude": "Latitude",
            "longitude": "Longitude",
            "city": "Cidade",
            "neighborhood": "Bairro",
            "street": "Rua",
            "distance_km": "Distância (km)",
            "price": "Preço (R$)",
            "start_time": "Início da Viagem",
            "end_time": "Fim da Viagem",
            "duration_min": "Duração (min)"
        }

        df_display = df[available_cols].rename(columns=rename_map)

        st.dataframe(df_display, use_container_width=True, height=400)

# =========================
# TAB 2 - Dashboard Corporativo
# =========================
with tab2:
    st.subheader("📊 Dashboard Interativo")

    if df.empty:
        st.warning("Nenhum dado disponível para análise.")
    else:
        # --- Filtros ---
        with st.expander("🔎 Filtros"):
            min_distance, max_distance = st.slider(
                "Faixa de distância (km)",
                min_value=float(df["distance_km"].min()),
                max_value=float(df["distance_km"].max()),
                value=(float(df["distance_km"].min()), float(df["distance_km"].max()))
            )
            start_date, end_date = st.date_input(
                "Período da viagem",
                value=(df['timestamp'].min().date(), df['timestamp'].max().date())
            )

        # Aplicar filtros
        filtered_df = df[
            (df["distance_km"] >= min_distance) &
            (df["distance_km"] <= max_distance)
        ]
        filtered_df = filtered_df[
            (filtered_df['timestamp'].dt.date >= start_date) &
            (filtered_df['timestamp'].dt.date <= end_date)
        ]

        # --- KPIs ---
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🛣️ Total Viagens", len(filtered_df))
        with col2:
            st.metric("📏 Distância Média (km)", round(filtered_df["distance_km"].mean(), 2))
        with col3:
            st.metric("💰 Preço Médio (R$)", round(filtered_df["price"].mean(), 2))
        with col4:
            st.metric("⏱️ Duração Média (min)", round(filtered_df["duration_min"].mean(), 2))

        st.markdown("---")

        # --- Gráficos ---
        col1, col2 = st.columns(2)

        with col1:
            fig_dist = px.histogram(
                filtered_df, x="distance_km", nbins=20,
                title="📊 Distribuição de Distâncias (km)",
                color_discrete_sequence=["#1f77b4"]
            )
            fig_dist.update_layout(paper_bgcolor="#0E1117", plot_bgcolor="#0E1117", font_color="#F5F5F5")
            st.plotly_chart(fig_dist, use_container_width=True)

            fig_price = px.box(
                filtered_df, y="price",
                title="📦 Distribuição de Preços",
                color_discrete_sequence=["#ff7f0e"]
            )
            fig_price.update_layout(paper_bgcolor="#0E1117", plot_bgcolor="#0E1117", font_color="#F5F5F5")
            st.plotly_chart(fig_price, use_container_width=True)

        with col2:
            trips_per_day = filtered_df.groupby('date').size().reset_index(name='trips')
            fig_trend = px.line(trips_per_day, x='date', y='trips', title="📈 Viagens por Dia", markers=True)
            fig_trend.update_layout(paper_bgcolor="#0E1117", plot_bgcolor="#0E1117", font_color="#F5F5F5")
            st.plotly_chart(fig_trend, use_container_width=True)

            trips_per_hour = filtered_df.groupby('hour').size().reset_index(name='trips')
            fig_hour = px.bar(trips_per_hour, x='hour', y='trips', title="⏰ Viagens por Hora", color_discrete_sequence=["#2ca02c"])
            fig_hour.update_layout(paper_bgcolor="#0E1117", plot_bgcolor="#0E1117", font_color="#F5F5F5")
            st.plotly_chart(fig_hour, use_container_width=True)

        st.markdown("---")

        # --- Mapa ---
        if "latitude" in filtered_df.columns and "longitude" in filtered_df.columns:
            fig_map = px.scatter_mapbox(
                filtered_df,
                lat="latitude",
                lon="longitude",
                hover_data=["city", "neighborhood", "street", "distance_km", "price"],
                color="distance_km",
                size="distance_km",
                color_continuous_scale=px.colors.cyclical.IceFire,
                size_max=15,
                zoom=5,
                height=600
            )
            fig_map.update_layout(mapbox_style="open-street-map")
            fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor="#0E1117", font_color="#F5F5F5")
            st.plotly_chart(fig_map, use_container_width=True)

        # --- Resumo por Cidade / Bairro ---
        col1, col2 = st.columns(2)

        with col1:
            trips_by_city = filtered_df.groupby("city").size().reset_index(name="trips")
            fig_city = px.bar(trips_by_city, x="city", y="trips", title="🏙️ Viagens por Cidade", color_discrete_sequence=["#d62728"])
            fig_city.update_layout(paper_bgcolor="#0E1117", plot_bgcolor="#0E1117", font_color="#F5F5F5")
            st.plotly_chart(fig_city, use_container_width=True)

        with col2:
            trips_by_neigh = filtered_df.groupby("neighborhood").size().reset_index(name="trips")
            fig_neigh = px.bar(trips_by_neigh, x="neighborhood", y="trips", title="📍 Viagens por Bairro", color_discrete_sequence=["#9467bd"])
            fig_neigh.update_layout(paper_bgcolor="#0E1117", plot_bgcolor="#0E1117", font_color="#F5F5F5")
            st.plotly_chart(fig_neigh, use_container_width=True)

# =========================
# TAB 3 - Perguntas
# =========================
with tab3:
    st.subheader("❓ Perguntas sobre Viagens")
    with st.expander("💬 Fazer Pergunta"):
        user_question = st.text_input("Digite sua pergunta:", "")
        if st.button("Obter Resposta"):
            if user_question:
                try:
                    response = requests.post("http://api:5001/ask", json={"question": user_question})
                    if response.status_code == 200:
                        st.success(response.json().get("answer"))
                    else:
                        st.error(f"Erro na API: {response.status_code} - {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error("Não foi possível conectar à API.")
            else:
                st.warning("Digite uma pergunta antes de enviar.")
