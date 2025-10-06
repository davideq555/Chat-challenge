# Ejecutar el proyecto con Docker Compose

Estos archivos permiten levantar el proyecto completo (frontend, backend, PostgreSQL y Redis) en otra máquina.

Requisitos previos:

- Docker
- Docker Compose (v2 o v1.29+)

Pasos rápidos:

1. Clonar el repositorio:

```bash
git clone <repo-url>
cd Chat-challenge
```

2. Copiar variables de entorno (ejemplo):

```bash
cp backend/.env.example backend/.env
```

3. Construir y levantar los servicios:

```bash
docker-compose up --build
```

Servicios expuestos:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000 (docs en /docs)
- Postgres: 5432
- Redis: 6379

Notas importantes:

- El backend espera `DATABASE_URL` y variables de Redis en el entorno. Puedes editar `backend/.env` o pasar variables por `docker-compose.override.yml`.
- Si necesitas ejecutar migraciones con Alembic:

```bash
docker-compose run --rm backend alembic upgrade head
```

- Los archivos subidos se montan en `./backend/uploads`.

Problemas comunes:

- Si el backend falla por `DATABASE_URL` no encontrada, asegúrate de haber creado `backend/.env` o de haber pasado la variable en `docker-compose.yml`.
- Si tienes errores con paquetes nativos al instalar dependencias puedes necesitar agregar paquetes del sistema; el `Dockerfile` del backend instala `build-essential` y `libpq-dev` que suelen cubrirlo.
