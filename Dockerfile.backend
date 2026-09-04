FROM python:3.11-slim

# Install system dependencies including FFmpeg, audio tools, and fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-freefont-ttf \
    fonts-dejavu-core \
    libsm6 \
    libxext6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy source code
COPY backend /app/backend

# Create media storage directory hierarchy
RUN mkdir -p media_storage/assets media_storage/audio media_storage/captions media_storage/rendered media_storage/thumbnails media_storage/temp

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
