FROM python:3.11-slim

# Prevent .pyc files + force logs to flush
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Avoid Debian warnings
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies (FFmpeg + archive tools + compilers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    p7zip-full \
    unzip \
    wget \
    curl \
    build-essential \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only requirements first (improves build caching)
COPY requirements.txt .

# Upgrade pip safely and install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the bot code
COPY . .

# Runtime directories
RUN mkdir -p /app/tmp /app/data
ENV TMPDIR=/app/tmp

# Expose optional port (if webhook used)
EXPOSE 8080

# Run bot
CMD ["python", "main.py"]
