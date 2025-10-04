import pendulum
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
import os

DOCKER_NETWORK = "real-time-project_default"  # rede criada pelo docker-compose
APP_IMAGE_PRODUCER = "real-time-project-producer:latest" # imagem do producer
APP_IMAGE_CONSUMER = "real-time-project-consumer:latest" # imagem do consumer
APP_IMAGE_ETL = "real-time-project-etl:latest" # imagem do etl

default_args = {
    "owner": "airflow",
    "start_date": pendulum.datetime(2025, 1, 1, tz="UTC"),
    "retries": 1,
}

# 🔑 Centraliza todas as variáveis em um dict
ENV_VARS = {
    "KAFKA_BROKER": os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
    "TOPIC_NAME": os.getenv("KAFKA_TOPIC"),
    "POSTGRES_HOST": os.getenv("POSTGRES_HOST"),
    "POSTGRES_PORT": os.getenv("POSTGRES_PORT"),
    "POSTGRES_USER": os.getenv("POSTGRES_USER"),
    "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD"),
    "POSTGRES_DB": os.getenv("POSTGRES_DB"),
}

with DAG(
    dag_id="real_time_pipeline",
    default_args=default_args,
    schedule_interval=None,  # só roda manual ou quando você disparar
    catchup=False,
    tags=["real-time"],
    
) as dag:

    # Producer
    start_producer = DockerOperator(
        task_id="start_producer",
        image=APP_IMAGE_PRODUCER,   # 👈 usa a imagem específica
        command="python src/producer.py",
        auto_remove=True,
        docker_url="unix://var/run/docker.sock",
        network_mode=DOCKER_NETWORK,
        environment=ENV_VARS,  # 👈 usa o dict de variáveis
    )

    # Consumer
    process_consumer = DockerOperator(
        task_id="process_consumer",
        image=APP_IMAGE_CONSUMER,   # 👈 usa a imagem específica
        command="python src/consumer.py",
        auto_remove=True,
        docker_url="unix://var/run/docker.sock",
        network_mode=DOCKER_NETWORK,
        environment=ENV_VARS,  # 👈 usa o dict de variáveis
    )

    # ETL
    process_etl = DockerOperator(
        task_id="process_etl",
        image=APP_IMAGE_ETL,   # 👈 usa a imagem específica
        command="spark-submit /app/etl_trips.py",
        auto_remove=True,
        docker_url="unix://var/run/docker.sock",
        network_mode=DOCKER_NETWORK,
        environment=ENV_VARS,
        mount_tmp_dir=False,  # Evita problemas de permissão no /tmp do host
)

    start_producer >> process_consumer >> process_etl