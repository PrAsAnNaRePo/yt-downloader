# FROM ubuntu:latest
FROM python:3.10-slim-bullseye

RUN apt-get update && \
    apt-get install -y libcairo2-dev pkg-config build-essential ffmpeg libsm6 libxext6 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN python3.10 -m pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8503

CMD ["streamlit", "run", "app.py", "--server.port=8503", "--server.address=0.0.0.0"]