# ╔══════════════════════════════════════════════════════════╗
# ║  FALKORA Backend — Dockerfile con Essentia               ║
# ║                                                          ║
# ║  Essentia no tiene wheel para Windows, por eso corremos   ║
# ║  en un contenedor Linux donde se instala sin problemas.   ║
# ╚══════════════════════════════════════════════════════════╝

FROM python:3.11-slim

# Dependencias de sistema para Essentia y librosa
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    ffmpeg \
    libfftw3-dev \
    libyaml-dev \
    libtag1-dev \
    libsamplerate0-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Essentia (solo funciona en Linux — por eso Docker)
RUN pip install --no-cache-dir essentia

# Copiar código
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
