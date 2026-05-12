# StyleScan Backend — Production Dockerfile
# Target: Railway / Render / Hetzner VPS (Linux/AMD64)
# Requires: 1GB+ RAM (MediaPipe), 1 vCPU minimum

FROM python:3.11-slim

# System dependencies for MediaPipe + OpenCV headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# setuptools needed for packages that still use setup.py (instagrapi, etc.)
RUN pip install --no-cache-dir setuptools wheel

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create knowledge_base dirs (may not exist in repo)
RUN mkdir -p knowledge_base/trending knowledge_base/barber_references/images

# Download MediaPipe face landmarker model (excluded from .dockerignore — fetch at build time)
RUN mkdir -p models && \
    python -c "import urllib.request; urllib.request.urlretrieve('https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task', 'models/face_landmarker.task')" && \
    echo "face_landmarker.task downloaded: $(du -sh models/face_landmarker.task)"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Python reads PORT from env — avoids shell $PORT expansion issues in Railway
CMD ["python", "-c", "import os,uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=int(os.environ.get('PORT',8000)), workers=2)"]
