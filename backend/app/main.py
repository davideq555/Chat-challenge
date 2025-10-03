from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.routers import users, chat_rooms, messages, attachments
from app.database import get_db
from app.redis_client import redis_client
from app.services.message_cache import message_cache

load_dotenv()

app = FastAPI(title="Chat API", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(users.router)
app.include_router(chat_rooms.router)
app.include_router(messages.router)
app.include_router(attachments.router)

@app.get("/")
async def root():
    return {"message": "Chat API is running"}

@app.get("/health")
async def health(db: Session = Depends(get_db)):
    """
    Healthcheck endpoint que verifica:
    - API está corriendo
    - PostgreSQL está conectado
    - Redis está conectado
    """
    health_status = {
        "status": "healthy",
        "services": {
            "api": "ok",
            "database": "unknown",
            "redis": "unknown"
        }
    }

    # Verificar PostgreSQL
    try:
        db.execute("SELECT 1")
        health_status["services"]["database"] = "ok"
    except Exception as e:
        health_status["services"]["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # Verificar Redis
    try:
        if redis_client.ping():
            health_status["services"]["redis"] = "ok"
        else:
            health_status["services"]["redis"] = "error: no ping response"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    return health_status

@app.get("/cache/stats")
async def cache_stats():
    """Obtener estadísticas del caché Redis"""
    return message_cache.get_cache_stats()
