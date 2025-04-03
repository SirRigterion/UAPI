FROM python:3.12.6-slim-bookworm

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Создаем симлинк для uploads
RUN mkdir -p /data/uploads && ln -s /data/uploads /app/uploads
RUN apt-get update && apt-get install -y python3-distutils
# Запуск FastAPI + миграции
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]