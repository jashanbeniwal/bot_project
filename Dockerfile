FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install ffmpeg & unzip/p7zip
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    p7zip-full \
    unzip \
    wget \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Create runtime dirs
RUN mkdir -p /app/tmp /app/data
ENV TMPDIR=/app/tmp

# Start
CMD ["python", "main.py"]
