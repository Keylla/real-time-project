# 🚀 Real-Time Project

## 📌 Visão Geral
Este projeto acadêmico simula um sistema de **processamento de dados em tempo real**, com foco na coleta, ingestão, transformação e visualização de informações geoespaciais de diferentes fontes. O objetivo é gerar **mapas de calor e insights** a partir de dados como localização, categoria e volume de eventos, ajudando na identificação de padrões e oportunidades.

Exemplos de conclusões possíveis:
- Detectar aumento de pedidos de **delivery** (mercado, lanches) em uma região e sugerir abertura de estabelecimentos.
- Identificar necessidade de **farmácias** em áreas com alta demanda de medicamentos.
- Reconhecer **eventos** em andamento por meio do aumento repentino de solicitações de viagens.

---

## 🛠️ Arquitetura do Projeto
- **Produção de dados** simulada (API/Producer Kafka).
- **Ingestão e transporte** via **Apache Kafka**.
- **Armazenamento** em **MongoDB**.
- **Painel interativo** em **Streamlit**, permitindo análise visual em tempo real.

---

## 📊 Funcionalidades do Painel
- **Dados Brutos**: Exibição dos principais atributos capturados:
  - Latitude / Longitude
  - Cidade / Bairro / Rua
  - Distância percorrida (km)
  - Preço da viagem (R$)
  - Horário de início e fim
  - Duração (minutos)

- **Visualização Geográfica**:
  - Mapa interativo com pontos e regiões de maior atividade.
  - Geração de mapas de calor.

- **Análises e Insights**:
  - Tendências por cidade ou bairro.
  - Identificação de hotspots.
  - Suporte à tomada de decisão estratégica.

---

## 📦 Estrutura do Repositório
```
real-time-project/
├── dashboard/          # Aplicação Streamlit
├── infra_estrutura/    # Conexão e serviços compartilhados
├── producer/           # Produção de dados para Kafka
├── consumer/           # Consumo e persistência no MongoDB
├── docker-compose.yml  # Orquestração dos serviços
├── config.yaml         # Configurações globais do projeto
└── README.md           # Documentação do projeto
```

---

## ▶️ Executando o Projeto
### 1. Clonar o repositório
```bash
git clone -b keylla_develop_branch https://github.com/Keylla/real-time-project.git
cd real-time-project
```

### 2. Subir os containers Docker
```bash
docker-compose up -d --build
```

### 3. Acessar o painel Streamlit
```bash
docker exec -it streamlit_app streamlit run app.py
```
Ou acessar no navegador: **http://localhost:8501**

---

## 📌 Tecnologias Utilizadas
- **Python** (Producer, Consumer, Dashboard)
- **Apache Kafka** (mensageria)
- **MongoDB** (armazenamento)
- **Streamlit** (visualização)
- **Docker & Docker Compose** (orquestração)

---

## 🧭 Próximos Passos
- Implementar novos tipos de visualização geográfica.
- Criar alertas em tempo real com base em thresholds.
- Expandir para suporte a múltiplas fontes de dados externas.
