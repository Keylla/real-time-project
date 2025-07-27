from flask import Flask, jsonify , request
import docker
import os
import google.generativeai as genai
from pymongo import MongoClient
import json
from datetime import datetime
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração da chave da API do Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Configuração do modelo Gemini
model= genai.GenerativeModel("gemini-1.5-flash")

# Inicialização do aplicativo Flask
app = Flask(__name__)

def connect_to_mongo():
    """
    Conecta ao MongoDB usando as variáveis de ambiente definidas no arquivo .env.
    """
    mongo_uri = os.getenv("MONGO_URI")
    mongo_db = os.getenv("MONGO_DB")
    mongo_collection = os.getenv("MONGO_COLLECTION")
    
    client = MongoClient(mongo_uri)
    db = client[mongo_db]
    collection = db[mongo_collection]
    
    return collection

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

def generate_mongo_query(user_question):
    # Defina o esquema do seu documento para o Gemini
    schema_info = """
    Seu banco de dados MongoDB tem uma coleção chamada 'trips'.
    Cada documento da coleção 'trips' tem o seguinte formato:
    {
        "_id": {"$oid": "string"},
        "partner_id": "string",
        "trip_id": "string",
        "start_time": "string (ISO 8601 date-time, ex: 2025-02-15T17:15:57)",
        "end_time": "string (ISO 8601 date-time, ex: 2025-02-23T11:28:32)",
        "distance_km": {"$numberDouble": "double"},
        "city": "string"
    }
    """
    # Instrua o Gemini a gerar uma query PyMongo
    prompt = f"""
    Sua única função é gerar um dicionário de filtro JSON válido para uma query PyMongo `find()`.
    A coleção é 'trips' e tem os seguintes campos:
    - start_time: string (ISO 8601, "YYYY-MM-DDTHH:MM:SS")
    - end_time: string (ISO 8601, "YYYY-MM-DDTHH:MM:SS")
    - distance_km: double
    - city: string

    Para perguntas com datas, use $gte e $lt com strings ISO 8601. Exemplo: fevereiro de 2025 é "{{"$gte": "2025-02-01T00:00:00", "$lt": "2025-03-01T00:00:00"}}".
    Para distâncias, use operadores como $gt, $lt, etc., com valores double (ex: 10.0).

    Gere APENAS o dicionário JSON do filtro, sem qualquer texto adicional, explicações ou blocos de código (```json```).
    Se não puder gerar uma query razoável, retorne um JSON vazio como {{"error": "invalid query"}}.

    ---
    Exemplos:

    Pergunta: "viagens de North Tony"
    Resposta: {{"city": "North Tony"}}

    Pergunta: "viagens em North Tony que começaram em fevereiro de 2025"
    Resposta: {{"city": "North Tony", "start_time": {{"$gte": "2025-02-01T00:00:00", "$lt": "2025-03-01T00:00:00"}}}}

    Pergunta: "viagens com distância maior que 10 km"
    Resposta: {{"distance_km": {{"$gt": 10.0}}}}

    Pergunta: "viagens em North Tony com distância maior que 10 km que começaram em fevereiro de 2025"
    Resposta: {{"city": "North Tony", "distance_km": {{"$gt": 10.0}}, "start_time": {{"$gte": "2025-02-01T00:00:00", "$lt": "2025-03-01T00:00:00"}}}}

    ---
    Pergunta do usuário: "{user_question}"
    Resposta:
    """
    response = model.generate_content(prompt)
    query_json_str = response.text.strip()
    if query_json_str.startswith("```json"):
        # Remove o bloco de código JSON se estiver presente
        query_json_str = query_json_str.replace("```json", "").replace("```", "").strip()
    if query_json_str.startswith("{") and query_json_str.endswith("}"):
        # Verifica se a resposta é um JSON válido
        try:
            json.loads(query_json_str)
        except json.JSONDecodeError:
            return '{"error": "invalid query"}'
    return query_json_str

def get_trips_by_query(mongo_query: dict) -> list[dict]:
    """
    Executa uma query no MongoDB e retorna os resultados.
    """
    try:
        # Usamos .find() com a query gerada.
        # Limitamos os resultados para evitar sobrecarga em caso de queries muito amplas.
        # Adapte o limite conforme sua necessidade.
        results_cursor = trips_collection.find(mongo_query).limit(20)
        results = []
        for doc in results_cursor:
            # Converte ObjectId para string para serialização JSON
            doc['_id'] = str(doc['_id'])
            # Opcional: Converter dates para string se não forem já ao buscar
            # if isinstance(doc.get('start_time'), datetime):
            #    doc['start_time'] = doc['start_time'].isoformat()
            results.append(doc)
        return results
    except Exception as e:
        print(f"Erro ao executar query no MongoDB: {e}")
        return []

# Conecta ao MongoDB e cria índices necessários
trips_collection = connect_to_mongo()
trips_collection.create_index("city")
trips_collection.create_index([("start_time", 1)])
trips_collection.create_index([("end_time", 1)])

@app.route("/ask", methods=["POST"])
def ask_gemini():
    data = request.json
    user_question = data.get("question")

    if not user_question:
        return jsonify({"error": "Por favor, forneça uma pergunta."}), 400

    try:
        # 1. Chamar Gemini para gerar a query MongoDB
        #    Chamamos generate_mongo_query
        mongo_query_json_str = generate_mongo_query(user_question)

        if not mongo_query_json_str:
            return jsonify({"answer": "Desculpe, não consegui gerar uma query válida para sua pergunta. Por favor, tente reformular."}), 200

        # Converte a string JSON da query de volta para um dicionário Python
        mongo_query_dict = json.loads(mongo_query_json_str)
        print(f"DEBUG: Query MongoDB a ser executada: {mongo_query_dict}") # Para depuração

        # 2. Executar a query gerada no MongoDB
        #    Chamamos get_trips_by_query
        query_results = get_trips_by_query(mongo_query_dict)

        # 3. Enviar os resultados para o Gemini para gerar uma resposta amigável
        if not query_results:
            final_answer = "Não encontrei dados correspondentes à sua solicitação."
        else:
            # Preparar os resultados para o Gemini
            # Remova o '_id' ou outros campos que não são úteis para o Gemini resumir
            # ou que podem causar problemas de serialização.
            clean_results = [{k: v for k, v in r.items() if k != '_id'} for r in query_results]
            results_for_gemini = json.dumps(clean_results, indent=2, default=str) # `default=str` ajuda com tipos não serializáveis

            summary_prompt = f"""
            A pergunta original do usuário foi: "{user_question}".
            Com base nos seguintes dados de viagens encontrados no banco de dados,
            resuma as informações de forma concisa, amigável e direta, respondendo à pergunta original.
            Se os dados permitirem, forneça insights ou a resposta direta.
            Dados encontrados:
            {results_for_gemini}
            """
            print(f"DEBUG: Prompt para resumo do Gemini:\n{summary_prompt}") # Para depuração

            summary_response = model.generate_content(summary_prompt)
            final_answer = summary_response.text.strip()

        return jsonify({"answer": final_answer})

    except Exception as e:
        print(f"Erro inesperado no endpoint /ask: {e}")
        return jsonify({"error": f"Ocorreu um erro interno. Detalhes: {str(e)}"}), 500


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
