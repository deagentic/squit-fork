# Usar imagen base de Python optimizada sin rate limits
FROM python:3.12-slim-bookworm

# Variables de entorno para optimización
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY app/ ./

# Variables de entorno
ENV PYTHONPATH=/app \
    GRPC_VERBOSITY=ERROR \
    GLOG_minloglevel=2

# Puerto por defecto (si se necesita servidor web en el futuro)
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import squit_client; print('OK')" || exit 1

# Comando por defecto (versión limpia sin warnings)
CMD ["python3", "examples/run_clean.py"]