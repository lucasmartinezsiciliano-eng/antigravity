FROM nvcr.io/nvidia/pytorch:25.01-py3

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    CENTRUM_STUDIO_DATA_DIR=/srv/centrum-studio

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libgl1 \
    libglib2.0-0 \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/centrum-studio

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY pyproject.toml ./
COPY centrum_studio ./centrum_studio
COPY souls ./souls
COPY luts ./luts
COPY scripts ./scripts

RUN pip install -e .

RUN mkdir -p /srv/centrum-studio/renders \
             /srv/centrum-studio/souls \
             /srv/centrum-studio/music \
             /srv/centrum-studio/luts \
             /srv/centrum-studio/cache \
    && cp -r /opt/centrum-studio/souls/* /srv/centrum-studio/souls/ 2>/dev/null || true \
    && cp -r /opt/centrum-studio/luts/* /srv/centrum-studio/luts/ 2>/dev/null || true \
    && echo "agents" > /srv/centrum-studio/gpu_mode

EXPOSE 8788

CMD ["bash", "/opt/centrum-studio/scripts/start.sh"]
