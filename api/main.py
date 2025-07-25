from flask import Flask, jsonify, request
import subprocess
import docker

app = Flask(__name__)

def get_container_id_by_partial_name(partial_name: str) -> docker.models.containers.Container | None:
  """
  Retorna o objeto Container Docker cuja parte do nome corresponde ao 'partial_name' fornecido.

  Args:
    partial_name (str): Uma parte do nome do container para buscar.

  Returns:
    docker.models.containers.Container | None: O objeto Container encontrado ou None se nenhum container for encontrado
          com a parte do nome especificada. Se múltiplos containers corresponderem,
          retorna o primeiro objeto Container encontrado.
  """
  client = docker.from_env()
  
  try:
    # Lista todos os containers (incluindo os parados)
    containers = client.containers.list(all=True) 
    
    for container in containers:
      # Verifica se a parte do nome está no nome completo do container
      if partial_name in container.name:
        return container
    
    return None # Nenhum container encontrado
    
  except docker.errors.APIError as e:
    print(f"Erro na comunicação com o daemon Docker: {e}")
    return None
  except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")
    return None
  
def start_docker_container_by_partial_name(partial_name: str) -> bool:
  """
  Inicia um container Docker buscando por parte do nome.

  Args:
    partial_name (str): Uma parte do nome do container para buscar e iniciar.

  Returns:
    bool: True se o container foi encontrado e iniciado com sucesso, False caso contrário.
  """
  print(f"Buscando container com '{partial_name}' no nome...")
  container = get_container_id_by_partial_name(partial_name)

  if container:
    print(f"Container '{container.name}' (ID: {container.id}) encontrado.")
    if container.status == 'running':
      print(f"Container '{container.name}' já está em execução.")
      return True
    else:
      try:
        print(f"Iniciando container '{container.name}'...")
        container.start()
        print(f"Container '{container.name}' (ID: {container.id}) iniciado com sucesso.")
        return True
      except docker.errors.APIError as e:
        print(f"Erro ao iniciar o container '{container.name}': {e}")
        return False
      except Exception as e:
        print(f"Ocorreu um erro inesperado ao iniciar o container: {e}")
        return False
  else:
    print(f"Nenhum container encontrado com '{partial_name}' no nome para iniciar.")
    return False

def stop_docker_container_by_partial_name(partial_name: str) -> bool:
  """
  Para um container Docker buscando por parte do nome.

  Args:
    partial_name (str): Uma parte do nome do container para buscar e parar.

  Returns:
    bool: True se o container foi encontrado e parado com sucesso, False caso contrário.
  """
  print(f"Buscando container com '{partial_name}' no nome...")
  container = get_container_id_by_partial_name(partial_name)

  if container:
    print(f"Container '{container.name}' (ID: {container.id}) encontrado.")
    if container.status == 'exited':
      print(f"Container '{container.name}' já está parado.")
      return True
    else:
      try:
        print(f"Parando container '{container.name}'...")
        container.stop()
        print(f"Container '{container.name}' (ID: {container.id}) parado com sucesso.")
        return True
      except docker.errors.APIError as e:
        print(f"Erro ao parar o container '{container.name}': {e}")
        return False
      except Exception as e:
        print(f"Ocorreu um erro inesperado ao parar o container: {e}")
        return False
  else:
    print(f"Nenhum container encontrado com '{partial_name}' no nome para parar.")
    return False
  

@app.route("/producer/start", methods=["POST"])
def start_producer():
    start_docker_container_by_partial_name("producer")
    return jsonify({"message": "Producer iniciado"}), 200

@app.route("/producer/stop", methods=["POST"])
def stop_producer():
    stop_docker_container_by_partial_name("producer")
    return jsonify({"message": "Producer parado"}), 200

@app.route("/consumer/start", methods=["POST"])
def start_consumer():
    start_docker_container_by_partial_name("consumer")
    return jsonify({"message": "Consumer iniciado"}), 200

@app.route("/consumer/stop", methods=["POST"])
def stop_consumer():
    stop_docker_container_by_partial_name("consumer")
    return jsonify({"message": "Consumer parado"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
