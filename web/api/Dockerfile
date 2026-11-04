FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# PORT vem do ambiente (o Render define a sua); sem ela, 8000. O compose
# sobrescreve este comando para ligar o --reload no desenvolvimento.
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
