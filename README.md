# 💬 Chat-challange — Examen Técnico Full Stack

Aplicación de **chat en tiempo real** desarrollada como parte de un examen técnico para el puesto de **Desarrollador Full Stack**.  

El proyecto implementa autenticación, gestión de contactos, mensajería persistente con **FastAPI + PostgreSQL + Redis**, y una interfaz moderna en **Next.js**.  
Adicionalmente se agregan **envío de archivos**, **buenas prácticas de seguridad** y **optimización de consultas**.  
La ejecución está orquestada mediante **Docker Compose** para simplificar la puesta en marcha.

---

## 🚀 Tecnologías principales
- **Frontend:** [Next.js](https://nextjs.org/) + React + TailwindCSS
- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.13)
- **Base de datos:** PostgreSQL
- **Cache / PubSub:** Redis
- **ORM:** SQLAlchemy + Alembic (migraciones)
- **Autenticación:** JWT (OAuth2 Password Flow)
- **Contenedores:** Docker + Docker Compose


## 🛠️ Configuración y ejecución

# Chat-challenge — Inicio rápido

Una aplicación de chat en tiempo real con frontend en Next.js y backend en FastAPI. Esta guía corta explica cómo inicializar el proyecto y las características principales.

Requisitos básicos
- Docker y Docker Compose
- Node 18+ / pnpm (solo para desarrollo local si no usas Docker)
- Python 3.13 (solo para desarrollo local si no usas Docker)

1) Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/chatapp.git
cd chatapp
```

2) Variables de entorno

Rellenar los ejemplos en `backend/.env.example` y `frontend/.env.local.example` si vas a ejecutar localmente sin Docker. No es obligatorio si usas Docker Compose (el compose define valores por defecto).

3) Levantar todo con Docker (forma recomendada)

```bash
docker-compose up --build
```

Servicios que se levantan
- Backend (FastAPI) → http://localhost:8000
- Frontend (Next.js) → http://localhost:3000
- PostgreSQL → localhost:5432
- Redis → localhost:6379

4) Ejecutar en desarrollo sin Docker (opcional)

- Backend
  - Ir a `backend/` y crear un virtualenv
  - Instalar dependencias: `pip install -r requirements.txt`
  - Configurar `backend/.env` basado en `backend/.env.example`
  - Ejecutar: `uvicorn app.main:app --reload --port 8000`

- Frontend
  - Ir a `frontend/`
  - Instalar dependencias: `pnpm install`
  - Copiar `frontend/.env.local.example` a `.env.local` y ajustar si es necesario
  - Ejecutar: `pnpm dev`

Características principales (resumen)
- Registro e inicio de sesión con JWT
- Gestión de contactos (agregar/eliminar/listar)
- Chat en tiempo real con WebSockets y persistencia en PostgreSQL
- Soporte de subida de archivos y manejo básico de adjuntos
- Redis para cache y Pub/Sub

Tests rápidos
- Backend: `cd backend && pytest -v`

Notas
- Para una instalación rápida, usa Docker Compose; si necesitas desarrollo iterativo, ejecuta servicios localmente.
- Si algo falla en el arranque con Docker, revisa los logs: `docker-compose logs -f` y asegúrate de que las variables de entorno necesarias estén presentes.

Licencia: MIT

Autor: David Aramayo

