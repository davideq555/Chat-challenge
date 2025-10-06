FROM python:3.13-slim

# Evitar buffering para logs en tiempo real
ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias del sistema necesarias (si requieren compilación)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar y instalar requirements
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r /app/requirements.txt

# Copiar el código de la aplicación
COPY . /app

# Crear carpeta de uploads con permisos
RUN mkdir -p /app/uploads

# Exponer puerto usado por Uvicorn
EXPOSE 8000

# Comando por defecto para arrancar la app con Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
