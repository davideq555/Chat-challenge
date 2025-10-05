from typing import List, Optional
from datetime import datetime
import logging
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

class MessageCache:
    """Servicio de caché para mensajes usando Redis"""

    CACHE_TTL = 3600  # 1 hora
    MAX_CACHED_MESSAGES = 50  # Últimos 50 mensajes por sala

    @staticmethod
    def _get_room_key(room_id: int) -> str:
        """Generar clave Redis para mensajes de una sala"""
        return f"messages:room:{room_id}"

    @staticmethod
    def cache_message(room_id: int, message_data: dict) -> bool:
        """
        Agregar mensaje al caché de una sala (solo si el cache ya existe)

        Args:
            room_id: ID de la sala
            message_data: Diccionario con datos del mensaje

        Returns:
            True si se cacheó correctamente
        """
        try:
            key = MessageCache._get_room_key(room_id)

            # Solo agregar si el cache ya existe (fue poblado por DB)
            # Esto evita crear caches parciales con 1-2 mensajes
            if not redis_client.exists(key):
                logger.info(f"⏭️ Cache no existe para sala {room_id}, mensaje no cacheado (se poblará en próxima consulta)")
                return False

            # Agregar mensaje al inicio de la lista
            redis_client.lpush(key, message_data)

            # Mantener solo los últimos MAX_CACHED_MESSAGES
            redis_client.ltrim(key, 0, MessageCache.MAX_CACHED_MESSAGES - 1)

            # Refrescar TTL
            redis_client.expire(key, MessageCache.CACHE_TTL)

            logger.info(f"✅ Mensaje cacheado en sala {room_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error cacheando mensaje en sala {room_id}: {e}")
            return False

    @staticmethod
    def get_cached_messages(room_id: int, limit: int = 50) -> Optional[List[dict]]:
        """
        Obtener mensajes cacheados de una sala

        Args:
            room_id: ID de la sala
            limit: Número máximo de mensajes a retornar

        Returns:
            Lista de mensajes o None si no hay caché
        """
        try:
            key = MessageCache._get_room_key(room_id)

            # Verificar si existe el caché
            if not redis_client.exists(key):
                logger.info(f"📭 No hay caché para sala {room_id}")
                return None

            # Obtener mensajes (del más reciente al más antiguo)
            messages = redis_client.lrange(key, 0, limit - 1, as_json=True)

            logger.info(f"✅ {len(messages)} mensajes obtenidos del caché de sala {room_id}")
            return messages
        except Exception as e:
            logger.error(f"❌ Error obteniendo caché de sala {room_id}: {e}")
            return None

    @staticmethod
    def invalidate_room_cache(room_id: int) -> bool:
        """
        Invalidar caché de una sala

        Args:
            room_id: ID de la sala

        Returns:
            True si se invalidó correctamente
        """
        try:
            key = MessageCache._get_room_key(room_id)
            deleted = redis_client.delete(key)
            logger.info(f"🗑️ Caché de sala {room_id} invalidado")
            return deleted > 0
        except Exception as e:
            logger.error(f"❌ Error invalidando caché de sala {room_id}: {e}")
            return False

    @staticmethod
    def update_cache_with_db_messages(room_id: int, messages: List[dict]) -> bool:
        """
        Actualizar caché con mensajes de la base de datos

        Args:
            room_id: ID de la sala
            messages: Lista de mensajes (del más reciente al más antiguo)

        Returns:
            True si se actualizó correctamente
        """
        try:
            key = MessageCache._get_room_key(room_id)

            # Eliminar caché existente
            redis_client.delete(key)

            # Agregar mensajes (en orden inverso para que queden del más reciente al más antiguo)
            if messages:
                for message in reversed(messages[:MessageCache.MAX_CACHED_MESSAGES]):
                    redis_client.rpush(key, message)

                # Establecer TTL
                redis_client.expire(key, MessageCache.CACHE_TTL)

                logger.info(f"✅ Caché de sala {room_id} actualizado con {len(messages)} mensajes")
            return True
        except Exception as e:
            logger.error(f"❌ Error actualizando caché de sala {room_id}: {e}")
            return False

    @staticmethod
    def get_cache_stats() -> dict:
        """
        Obtener estadísticas del caché

        Returns:
            Diccionario con estadísticas
        """
        try:
            # Esto es un ejemplo básico, podrías expandirlo
            return {
                "redis_connected": redis_client.ping(),
                "ttl": MessageCache.CACHE_TTL,
                "max_messages_per_room": MessageCache.MAX_CACHED_MESSAGES
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo stats del caché: {e}")
            return {"error": str(e)}


# Instancia global
message_cache = MessageCache()
