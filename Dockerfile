# ---- Base Image ----
FROM python:3.12-alpine

# ---- Set Environment Variables ----
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ---- Set Work Directory ----
WORKDIR /app

# ---- Install Dependencies ----
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---- Copy Project ----
COPY . .

ENV PORT=8080

CMD ["python3", "-m", "app.grpc_server"]