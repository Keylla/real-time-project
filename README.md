# 🚗 Real-Time Travel Monitoring System

Projeto acadêmico para simular um sistema de monitoramento de viagens em tempo real utilizando microserviços, Kafka, MongoDB, Flask e Streamlit.

## 📦 Tecnologias Utilizadas

- Python 3.10
- Apache Kafka
- MongoDB
- Docker & Docker Compose
- Streamlit (dashboard)
- Flask (API para controle dos serviços)

## 🗂️ Estrutura do Projeto

```
real-time-project/
│
├── .env                    # Variáveis de ambiente
├── config.yaml             # Configuração central (deprecado se .env estiver ativo)
├── docker-compose.yml      # Orquestração dos serviços
│
├── producer/               # Serviço produtor de mensagens Kafka
│   ├── producer.py
│   ├── Dockerfile
│
├── consumer/               # Serviço consumidor e armazenador no MongoDB
│   ├── consumer.py
│   ├── Dockerfile
│
├── api/                    # API Flask para controle dos serviços
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│
├── dashboard/              # Interface web com Streamlit
│   ├── app.py
│   ├── Dockerfile
│
└── requirements.txt        # Dependências globais
```

## 🚀 Executando o Projeto

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/Keylla/real-time-project.git
   cd real-time-project
   ```

2. **Configure as variáveis de ambiente:**
   Crie um arquivo `.env` na raiz com o conteúdo:
   ```env
   KAFKA_SERVER=kafka:9092
   MONGO_URI=mongodb://mongo:27017
   CONFIG_PATH=/app/config.yaml
   ```

3. **Suba os serviços com Docker Compose:**
   ```bash
   docker-compose up --build
   ```

4. **Acesse a aplicação:**
   - **Dashboard (Streamlit):** http://localhost:8501
   - **API Flask:** http://localhost:5000

## 🛠️ Funcionalidades

- Simulação de viagens com dados fictícios
- Produção de eventos em tempo real com Kafka
- Armazenamento de dados em MongoDB
- Visualização em tempo real no dashboard Streamlit
- API Flask para start/stop de serviços via UI

## 📊 Dashboard

- Atualização manual ou automática
- Visualização de dados recebidos
- Gráfico de distribuição de distâncias

## ✅ Comandos úteis

- **Build do projeto limpando cache:**
  ```bash
  docker-compose build --no-cache
  ```

- **Comando para subir container individualmente:**
  ```bash
  docker-compose up producer
  ```

## 📤 Publicação no Docker Hub

1. **Login no Docker Hub:**
   ```bash
   docker login
   ```

2. **Criação da imagem:**
   ```bash
   docker build -t seu_usuario/nome_da_imagem .
   ```

3. **Push para o Docker Hub:**
   ```bash
   docker push seu_usuario/nome_da_imagem
   ```

## 🧪 Status

✅ Em desenvolvimento com arquitetura funcional e componentes integrados.
