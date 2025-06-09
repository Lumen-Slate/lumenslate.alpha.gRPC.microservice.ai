FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "exec uvicorn main:api --host 0.0.0.0 --port ${PORT:-5000}"]