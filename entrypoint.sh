#!/bin/bash
set -e

# Inicializa DB do Airflow
airflow db init

# Cria usuário admin somente se não existir
if ! airflow users list | grep -q "airflow"; then
  echo ">>> Criando usuário admin..."
  airflow users create \
    --username airflow \
    --firstname Airflow \
    --lastname Admin \
    --role Admin \
    --password airflow \
    --email admin@example.com
else
  echo ">>> Usuário admin já existe, pulando criação."
fi

# Executa o comando original do container (webserver, scheduler, etc.)
exec "$@"