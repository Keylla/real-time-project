from pymongo import MongoClient
import os
from dotenv import load_dotenv
import json

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Função para conectar ao MongoDB
def connect_to_mongo():
    """
    Conecta ao MongoDB usando as variáveis de ambiente definidas no arquivo .env.
    """
    mongo_uri = os.getenv("MONGO_URI")
    mongo_db = os.getenv("MONGO_DB")
    mongo_collection = os.getenv("MONGO_COLLECTION")

    if not mongo_uri or not mongo_db or not mongo_collection:
        raise ValueError("MONGO_URI, MONGO_DB ou MONGO_COLLECTION não definidos no .env")
    
    client = MongoClient(mongo_uri)
    db = client[mongo_db]
    collection = db[mongo_collection]
    
    return collection


def generate_mongo_query(user_question, model) -> str:
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
        # Conecta ao MongoDB e cria índices necessários
        trips_collection = connect_to_mongo()
        trips_collection.create_index("city")
        trips_collection.create_index([("start_time", 1)])
        trips_collection.create_index([("end_time", 1)])

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