FROM python:3.12-slim

# Cài ffmpeg + libopus cho voice
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libopus0 && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Chạy như worker (không cần web port)
CMD ["python", "bot.py"]
