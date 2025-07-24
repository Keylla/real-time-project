FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y docker.io
CMD ["python", "main.py"]
EXPOSE 5000