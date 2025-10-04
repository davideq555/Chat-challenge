from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener DATABASE_URL del .env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment variables")

# Configurar echo desde variable de entorno (por defecto False)
DB_ECHO = os.getenv("DB_ECHO", "false").lower() == "true"

# Crear engine de SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    echo=DB_ECHO,  # Mostrar queries SQL solo si DB_ECHO=true en .env
    pool_pre_ping=True  # Verifica conexiones antes de usarlas
)

# Crear SessionLocal factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency para obtener sesión de base de datos
def get_db() -> Generator[Session, None, None]:
    """
    Dependency que proporciona una sesión de base de datos.
    Se usa en los endpoints con Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
