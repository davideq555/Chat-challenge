import redis
import json
import os
from typing import Optional, Any, List
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

class RedisClient:
    """Cliente Redis para caché y Pub/Sub"""

    def __init__(self):
        """Inicializar conexión a Redis"""
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self.password = os.getenv("REDIS_PASSWORD", None)

        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password if self.password else None,
                decode_responses=True,  # Decodificar respuestas como strings
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Probar conexión
            self.client.ping()
            logger.info(f"✅ Conectado a Redis en {self.host}:{self.port}")
        except redis.ConnectionError as e:
            logger.error(f"❌ Error conectando a Redis: {e}")
            raise

    # ==================== OPERACIONES BÁSICAS ====================

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Guardar valor en Redis

        Args:
            key: Clave
            value: Valor (se serializa a JSON si es dict/list)
            ttl: Tiempo de vida en segundos (None = sin expiración)

        Returns:
            True si se guardó correctamente
        """
        try:
            # Serializar a JSON si es dict o list
            if isinstance(value, (dict, list)):
                value = json.dumps(value)

            if ttl:
                return self.client.setex(key, ttl, value)
            else:
                return self.client.set(key, value)
        except Exception as e:
            logger.error(f"Error en set({key}): {e}")
            return False

    def get(self, key: str, as_json: bool = False) -> Optional[Any]:
        """
        Obtener valor de Redis

        Args:
            key: Clave
            as_json: Si True, deserializa como JSON

        Returns:
            Valor o None si no existe
        """
        try:
            value = self.client.get(key)
            if value is None:
                return None

            if as_json:
                return json.loads(value)
            return value
        except Exception as e:
            logger.error(f"Error en get({key}): {e}")
            return None

    def delete(self, *keys: str) -> int:
        """
        Eliminar una o más claves

        Returns:
            Número de claves eliminadas
        """
        try:
            return self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Error en delete({keys}): {e}")
            return 0

    def exists(self, *keys: str) -> int:
        """
        Verificar si una o más claves existen

        Returns:
            Número de claves que existen
        """
        try:
            return self.client.exists(*keys)
        except Exception as e:
            logger.error(f"Error en exists({keys}): {e}")
            return 0

    def expire(self, key: str, seconds: int) -> bool:
        """
        Establecer tiempo de expiración para una clave

        Returns:
            True si se estableció correctamente
        """
        try:
            return self.client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Error en expire({key}): {e}")
            return False

    def ttl(self, key: str) -> int:
        """
        Obtener tiempo de vida restante de una clave

        Returns:
            Segundos restantes (-1 si no tiene TTL, -2 si no existe)
        """
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Error en ttl({key}): {e}")
            return -2

    # ==================== OPERACIONES DE LISTAS ====================

    def lpush(self, key: str, *values: Any) -> int:
        """
        Agregar valores al inicio de una lista

        Returns:
            Longitud de la lista después de la operación
        """
        try:
            # Serializar valores si son dict/list
            serialized = [
                json.dumps(v) if isinstance(v, (dict, list)) else v
                for v in values
            ]
            return self.client.lpush(key, *serialized)
        except Exception as e:
            logger.error(f"Error en lpush({key}): {e}")
            return 0

    def rpush(self, key: str, *values: Any) -> int:
        """
        Agregar valores al final de una lista

        Returns:
            Longitud de la lista después de la operación
        """
        try:
            serialized = [
                json.dumps(v) if isinstance(v, (dict, list)) else v
                for v in values
            ]
            return self.client.rpush(key, *serialized)
        except Exception as e:
            logger.error(f"Error en rpush({key}): {e}")
            return 0

    def lrange(self, key: str, start: int = 0, end: int = -1, as_json: bool = False) -> List[Any]:
        """
        Obtener elementos de una lista

        Args:
            key: Clave de la lista
            start: Índice inicial (0 = primer elemento)
            end: Índice final (-1 = último elemento)
            as_json: Si True, deserializa cada elemento como JSON

        Returns:
            Lista de elementos
        """
        try:
            values = self.client.lrange(key, start, end)
            if as_json:
                return [json.loads(v) for v in values]
            return values
        except Exception as e:
            logger.error(f"Error en lrange({key}): {e}")
            return []

    def ltrim(self, key: str, start: int, end: int) -> bool:
        """
        Recortar lista para mantener solo elementos en el rango

        Returns:
            True si se recortó correctamente
        """
        try:
            return self.client.ltrim(key, start, end)
        except Exception as e:
            logger.error(f"Error en ltrim({key}): {e}")
            return False

    def llen(self, key: str) -> int:
        """
        Obtener longitud de una lista

        Returns:
            Longitud de la lista
        """
        try:
            return self.client.llen(key)
        except Exception as e:
            logger.error(f"Error en llen({key}): {e}")
            return 0

    # ==================== OPERACIONES DE SETS ====================

    def sadd(self, key: str, *members: Any) -> int:
        """
        Agregar miembros a un set

        Returns:
            Número de miembros agregados (sin contar duplicados)
        """
        try:
            return self.client.sadd(key, *members)
        except Exception as e:
            logger.error(f"Error en sadd({key}): {e}")
            return 0

    def srem(self, key: str, *members: Any) -> int:
        """
        Eliminar miembros de un set

        Returns:
            Número de miembros eliminados
        """
        try:
            return self.client.srem(key, *members)
        except Exception as e:
            logger.error(f"Error en srem({key}): {e}")
            return 0

    def smembers(self, key: str) -> set:
        """
        Obtener todos los miembros de un set

        Returns:
            Set con todos los miembros
        """
        try:
            return self.client.smembers(key)
        except Exception as e:
            logger.error(f"Error en smembers({key}): {e}")
            return set()

    def sismember(self, key: str, member: Any) -> bool:
        """
        Verificar si un miembro está en el set

        Returns:
            True si el miembro está en el set
        """
        try:
            return self.client.sismember(key, member)
        except Exception as e:
            logger.error(f"Error en sismember({key}): {e}")
            return False

    def scard(self, key: str) -> int:
        """
        Obtener número de miembros en un set

        Returns:
            Número de miembros
        """
        try:
            return self.client.scard(key)
        except Exception as e:
            logger.error(f"Error en scard({key}): {e}")
            return 0

    # ==================== PUB/SUB (para WebSockets) ====================

    def publish(self, channel: str, message: Any) -> int:
        """
        Publicar mensaje en un canal

        Args:
            channel: Nombre del canal
            message: Mensaje (se serializa a JSON si es dict/list)

        Returns:
            Número de suscriptores que recibieron el mensaje
        """
        try:
            if isinstance(message, (dict, list)):
                message = json.dumps(message)
            return self.client.publish(channel, message)
        except Exception as e:
            logger.error(f"Error en publish({channel}): {e}")
            return 0

    def subscribe(self, *channels: str):
        """
        Suscribirse a uno o más canales

        Returns:
            PubSub object
        """
        try:
            pubsub = self.client.pubsub()
            pubsub.subscribe(*channels)
            return pubsub
        except Exception as e:
            logger.error(f"Error en subscribe({channels}): {e}")
            return None

    # ==================== UTILIDADES ====================

    def ping(self) -> bool:
        """
        Verificar conexión a Redis

        Returns:
            True si está conectado
        """
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Error en ping: {e}")
            return False

    def flushdb(self) -> bool:
        """
        ELIMINAR TODA LA BASE DE DATOS (usar solo en desarrollo)

        Returns:
            True si se limpió correctamente
        """
        try:
            return self.client.flushdb()
        except Exception as e:
            logger.error(f"Error en flushdb: {e}")
            return False

    def close(self):
        """Cerrar conexión a Redis"""
        try:
            self.client.close()
            logger.info("🔌 Conexión a Redis cerrada")
        except Exception as e:
            logger.error(f"Error cerrando conexión: {e}")


# Instancia global de Redis
redis_client = RedisClient()
