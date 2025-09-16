from flask import Flask, jsonify , request

import os
import google.generativeai as genai
import json
from dotenv import load_dotenv
from infrastructure.connection import generate_mongo_query, get_trips_by_query
from infrastructure.docker_controller import start_docker_container_by_partial_name, stop_docker_container_by_partial_name

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração da chave da API do Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Configuração do modelo Gemini
model= genai.GenerativeModel(os.getenv("GEMINI_GENERATION_MODEL", "gemini-1.5-flash"))

# Inicialização do aplicativo Flask
app = Flask(__name__)

@app.route("/ask", methods=["POST"])
def ask_gemini():
    data = request.json
    user_question = data.get("question")

    if not user_question:
        return jsonify({"error": "Por favor, forneça uma pergunta."}), 400

    try:
        # 1. Chamar Gemini para gerar a query MongoDB
        #    Chamamos generate_mongo_query
        mongo_query_json_str = generate_mongo_query(user_question, model)

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
