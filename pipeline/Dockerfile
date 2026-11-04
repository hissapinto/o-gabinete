# Imagem do servico carga do docker-compose.yml: roda o pipeline/carga.py uma
# vez e termina. Build com contexto na raiz do repositorio, por causa do
# requirements.txt de la (ver .dockerignore).
# Mesma versao de Python do web/api/Dockerfile.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline/ pipeline/

# O carga.py importa os modulos vizinhos por nome simples (from coleta import
# ...), entao roda de dentro da pasta. O utils.encontrar_raiz sobe ate achar o
# /app/requirements.txt, e os CSVs ficam em /app/dados/brutos (volume).
WORKDIR /app/pipeline
CMD ["python", "carga.py"]
