import pendulum
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

APP_IMAGE = "real_time_project_app"   # imagem construida no projeto
DOCKER_NETWORK = "real-time-project_default"  # nome da rede criada pelo docker-compose

default_args = {
    "owner": "airflow",
    "start_date": pendulum.datetime(2025, 1, 1, tz="UTC"),
    "retries": 1,
}

with DAG(
    dag_id="real_time_pipeline",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=["real-time"],
) as dag:

    start_producer = DockerOperator(
        task_id="start_producer",
        image=APP_IMAGE,
        command="python src/real_time_project/producer.py",
        auto_remove=True,
        docker_url="unix://var/run/docker.sock",   # 👈 conecta ao Docker
        network_mode=DOCKER_NETWORK,              # 👈 garante acesso ao Kafka e Postgres
        environment={
            "KAFKA_BROKER": "kafka:9092",
            "TOPIC_NAME": "trips",
            "POSTGRES_HOST": "postgres",
            "POSTGRES_PORT": "5432",
            "POSTGRES_USER": "airflow",
            "POSTGRES_PASSWORD": "airflow",
            "POSTGRES_DB": "airflow",
        },
    )

    process_consumer = DockerOperator(
        task_id="process_consumer",
        image=APP_IMAGE,
        command="python src/real_time_project/consumer.py",
        auto_remove=True,
        docker_url="unix://var/run/docker.sock",
        network_mode=DOCKER_NETWORK,
        environment={
            "KAFKA_BROKER": "kafka:9092",
            "TOPIC_NAME": "trips",
            "POSTGRES_HOST": "postgres",
            "POSTGRES_PORT": "5432",
            "POSTGRES_USER": "airflow",
            "POSTGRES_PASSWORD": "airflow",
            "POSTGRES_DB": "airflow",
        },
    )

    start_producer >> process_consumer