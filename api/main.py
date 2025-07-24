from flask import Flask, jsonify, request
import subprocess

app = Flask(__name__)

def get_container_name_or_id(service_name):
    try:
        # Obtém o ID do contêiner associado ao serviço
        # O comando 'docker ps -q' retorna apenas os IDs dos contêineres
        result = subprocess.run(
            ["docker", "ps", "-q", service_name],
            capture_output=True,
            text=True,
            check=True
        )
        # O output pode ter uma quebra de linha no final, então strip() é importante
        container_id = result.stdout.strip()
        if not container_id:
            print(f"Nenhum contêiner encontrado para o serviço '{service_name}'.")
            return None
        return container_id
    except subprocess.CalledProcessError as e:
        print(f"Erro ao obter o ID do contêiner para '{service_name}': {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return None
    except FileNotFoundError:
        print("Comando 'docker' não encontrado. Certifique-se de que está instalado e no PATH.")
        return None


@app.route("/producer/start", methods=["POST"])
def start_producer():
    #producer_id = get_container_name_or_id("producer")
    subprocess.Popen(["docker", "start", "producer-1"])
    return jsonify({"message": "Producer iniciado"}), 200

@app.route("/producer/stop", methods=["POST"])
def stop_producer():
    #producer_id = get_container_name_or_id("producer")
    subprocess.Popen(["docker", "stop", "producer-1"])
    return jsonify({"message": "Producer parado"}), 200

@app.route("/consumer/start", methods=["POST"])
def start_consumer():
    #consumer_id = get_container_name_or_id("consumer")
    subprocess.Popen(["docker", "start", "consumer-1"])
    return jsonify({"message": "Consumer iniciado"}), 200

@app.route("/consumer/stop", methods=["POST"])
def stop_consumer():
    #consumer_id = get_container_name_or_id("consumer")
    subprocess.Popen(["docker", "stop", "consumer-1"])
    return jsonify({"message": "Consumer parado"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
