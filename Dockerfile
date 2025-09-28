# Usa uma imagem base oficial do Python
FROM python:3.10-slim

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de dependências
COPY pyproject.toml .

COPY README.md .

RUN pip install .

# Faz o Python reconhecer /app como raiz do projeto
ENV PYTHONPATH=/app

# Copia todo o restante do código
COPY . /app