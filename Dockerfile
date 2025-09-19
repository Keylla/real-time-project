# Usa uma imagem base oficial do Python
FROM python:3.10-slim

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia apenas o arquivo de requisitos primeiro
COPY requirements.txt .

# Faz o Python reconhecer /app como raiz do projeto
ENV PYTHONPATH=/app

# Instala as dependências. O cache é usado se o requirements.txt não mudar
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o restante do código
COPY . /app