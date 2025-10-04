"""
Servicio para manejar estado online de usuarios en Redis
"""

import logging
from typing import List, Set
from app.redis_client import redis_client

logger = logging.getLogger(__name__)


class UserOnlineService:
    """Servicio para gestionar usuarios online en Redis"""

    ONLINE_USERS_KEY = "users:online"  # Set con IDs de usuarios online
    USER_CONNECTIONS_PREFIX = "user:connections:"  # Hash con conexiones por usuario

    def set_user_online(self, user_id: int) -> bool:
        """
        Marcar usuario como online

        Args:
            user_id: ID del usuario

        Returns:
            True si se marcó correctamente
        """
        try:
            redis_client.sadd(self.ONLINE_USERS_KEY, str(user_id))
            logger.info(f"✅ Usuario {user_id} marcado como online")
            return True
        except Exception as e:
            logger.error(f"❌ Error marcando usuario {user_id} como online: {e}")
            return False

    def set_user_offline(self, user_id: int) -> bool:
        """
        Marcar usuario como offline

        Args:
            user_id: ID del usuario

        Returns:
            True si se marcó correctamente
        """
        try:
            redis_client.srem(self.ONLINE_USERS_KEY, str(user_id))
            logger.info(f"✅ Usuario {user_id} marcado como offline")
            return True
        except Exception as e:
            logger.error(f"❌ Error marcando usuario {user_id} como offline: {e}")
            return False

    def is_user_online(self, user_id: int) -> bool:
        """
        Verificar si un usuario está online

        Args:
            user_id: ID del usuario

        Returns:
            True si está online
        """
        try:
            return redis_client.sismember(self.ONLINE_USERS_KEY, str(user_id))
        except Exception as e:
            logger.error(f"❌ Error verificando si usuario {user_id} está online: {e}")
            return False

    def get_online_users(self) -> Set[str]:
        """
        Obtener todos los usuarios online

        Returns:
            Set con IDs de usuarios online
        """
        try:
            return redis_client.smembers(self.ONLINE_USERS_KEY)
        except Exception as e:
            logger.error(f"❌ Error obteniendo usuarios online: {e}")
            return set()

    def get_online_count(self) -> int:
        """
        Obtener cantidad de usuarios online

        Returns:
            Número de usuarios online
        """
        try:
            return redis_client.scard(self.ONLINE_USERS_KEY)
        except Exception as e:
            logger.error(f"❌ Error obteniendo cantidad de usuarios online: {e}")
            return 0

    def add_user_connection(self, user_id: int, connection_id: str) -> int:
        """
        Agregar una conexión para un usuario (permite múltiples dispositivos)

        Args:
            user_id: ID del usuario
            connection_id: ID único de la conexión

        Returns:
            Número total de conexiones del usuario
        """
        try:
            key = f"{self.USER_CONNECTIONS_PREFIX}{user_id}"
            result = redis_client.sadd(key, connection_id)

            # Marcar usuario como online si es su primera conexión
            self.set_user_online(user_id)

            logger.info(f"✅ Conexión {connection_id} agregada para usuario {user_id}")
            return redis_client.scard(key)
        except Exception as e:
            logger.error(f"❌ Error agregando conexión para usuario {user_id}: {e}")
            return 0

    def remove_user_connection(self, user_id: int, connection_id: str) -> int:
        """
        Eliminar una conexión de un usuario

        Args:
            user_id: ID del usuario
            connection_id: ID único de la conexión

        Returns:
            Número de conexiones restantes del usuario
        """
        try:
            key = f"{self.USER_CONNECTIONS_PREFIX}{user_id}"
            redis_client.srem(key, connection_id)

            # Obtener conexiones restantes
            remaining = redis_client.scard(key)

            # Si no quedan conexiones, marcar como offline
            if remaining == 0:
                self.set_user_offline(user_id)
                redis_client.delete(key)  # Limpiar key vacía

            logger.info(f"✅ Conexión {connection_id} eliminada para usuario {user_id} ({remaining} restantes)")
            return remaining
        except Exception as e:
            logger.error(f"❌ Error eliminando conexión para usuario {user_id}: {e}")
            return 0

    def get_user_connections_count(self, user_id: int) -> int:
        """
        Obtener cantidad de conexiones activas de un usuario

        Args:
            user_id: ID del usuario

        Returns:
            Número de conexiones activas
        """
        try:
            key = f"{self.USER_CONNECTIONS_PREFIX}{user_id}"
            return redis_client.scard(key)
        except Exception as e:
            logger.error(f"❌ Error obteniendo conexiones de usuario {user_id}: {e}")
            return 0


# Instancia global
user_online_service = UserOnlineService()
