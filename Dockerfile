FROM python:3.12-slim

LABEL authors="antonkonyk@gmail.com"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# OS deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates tzdata curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY app/ app/

# Default CMD overridden by docker-compose per service
CMD ["python", "-c", "print('Image built; use docker-compose')"]
