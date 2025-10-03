# 💬 Chat-challange — Examen Técnico Full Stack

Aplicación de **chat en tiempo real** desarrollada como parte de un examen técnico para el puesto de **Desarrollador Full Stack**.  

El proyecto implementa autenticación, gestión de contactos, mensajería persistente con **FastAPI + PostgreSQL + Redis**, y una interfaz moderna en **Next.js**.  
Adicionalmente se agregan **envío de archivos**, **buenas prácticas de seguridad** y **optimización de consultas**.  
La ejecución está orquestada mediante **Docker Compose** para simplificar la puesta en marcha.

---

## 🚀 Tecnologías principales
- **Frontend:** [Next.js](https://nextjs.org/) + React + TailwindCSS
- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12)
- **Base de datos:** PostgreSQL
- **Cache / PubSub:** Redis
- **ORM:** SQLAlchemy + Alembic (migraciones)
- **Autenticación:** JWT (OAuth2 Password Flow)
- **Contenedores:** Docker + Docker Compose

---

## 📦 Funcionalidades implementadas

### Mínimas sugeridas
1. ✅ **Autenticación de usuarios** (registro e inicio de sesión con JWT).
2. ✅ **Gestión de contactos** (buscar, agregar, eliminar).
3. ✅ **Chat en tiempo real** con WebSockets y persistencia en PostgreSQL.
4. ✅ **Frontend en Next.js** con manejo de estado y consumo de API REST + WS.


## 🛠️ Configuración y ejecución

### 1. Clonar repositorio
```bash
git clone https://github.com/tu-usuario/chatapp.git
cd chatapp
````

### 2. Variables de entorno

Editar los archivos de entorno en **backend** y **frontend** basados en los `.env.example`.

#### `backend/.env.example`

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/chatapp
REDIS_URL=redis://redis:6379/0
SECRET_KEY=una_clave_muy_secreta
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

#### `frontend/.env.local.example`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 3. Ejecutar con Docker Compose

```bash
docker-compose up --build
```

Esto levantará:

* **Backend FastAPI** en `http://localhost:8000`
* **Frontend Next.js** en `http://localhost:3000`
* **PostgreSQL** en `localhost:5432`
* **Redis** en `localhost:6379`

---

## 📡 Endpoints principales

### REST (FastAPI)

* `POST /auth/register` → registro de usuario
* `POST /auth/login` → login y obtención de JWT
* `GET /contacts/` → lista de contactos
* `POST /contacts/` → agregar contacto
* `DELETE /contacts/{id}` → eliminar contacto
* `GET /messages/{room_id}` → historial de mensajes

### WebSockets

* `ws://localhost:8000/ws/{room_id}?token=<JWT>`

  * Enviar/recibir mensajes en tiempo real
  * Soporta adjuntos (binario/base64)

---

## 🧪 Tests

### Backend

```bash
cd backend
pytest -v
```

### Frontend

```bash
cd frontend
npm run test
```

---

## 🔐 Seguridad

* Contraseñas hasheadas con bcrypt.
* JWT con expiración corta y refresh opcional.
* Validación de usuario en cada request/WS.
* CORS configurado para frontend.
* Uso de parámetros tipados en Pydantic (prevención de inyecciones).

---

## 📈 Optimización

* Redis cache para usuarios online y lista de contactos.
* Redis Pub/Sub para sincronizar mensajes en despliegues con múltiples instancias.

---

## 📝 Licencia

Este proyecto se distribuye bajo licencia **MIT**.

---

## 👨‍💻 Autor

Desarrollado por David Aramayo como parte de un examen técnico para Desarrollador Full Stack.
