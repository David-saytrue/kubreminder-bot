# Используем официальный образ Python 3.13 (slim — минимальный размер)
FROM python:3.13-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем файлы бота в контейнер
COPY bot.py .

# Создаем том для хранения данных (если нужно сохранять файлы)
VOLUME ["/app/data"]

# Команда запуска бота
CMD ["python", "bot.py"]
