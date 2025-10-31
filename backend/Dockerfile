FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app code
COPY ./app /app

# ensure ffmpeg present in the environment (you can also install FFmpeg in the host and mount)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1