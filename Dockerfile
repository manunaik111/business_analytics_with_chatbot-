# Dockerfile
FROM python:3.11-slim

# Install system deps needed by some packages (spacy, reportlab, gTTS)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_sm

# Copy app source
COPY . .

# Render injects $PORT at runtime
CMD uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}
