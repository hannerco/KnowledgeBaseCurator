FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema (curl para el healthcheck del contenedor, si se necesita)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python primero (aprovecha caché de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-descargar el modelo de embeddings para evitar cold-start en runtime
# Se descarga a la caché de HuggingFace dentro de la imagen
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copiar el código fuente
COPY . .

# --reload permite hot-reload al editar código con el volumen montado
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
