FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
# voice_studio plugin üçün ffmpeg + ffprobe əlavə edildi
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev ffmpeg && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 10000
CMD ["python", "main.py"]
