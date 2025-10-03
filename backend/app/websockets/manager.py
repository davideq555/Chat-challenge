from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
from datetime import datetime

from app.websockets.events import EventType, create_event

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Gestor de conexiones WebSocket

    Mantiene un diccionario de conexiones activas organizadas por sala:
    {
        room_id: {
            websocket_id: {
                "websocket": WebSocket,
                "user_id": int,
                "username": str
            }
        }
    }
    """

    def __init__(self):
        # Conexiones activas: {room_id: {connection_id: {websocket, user_id, username}}}
        self.active_connections: Dict[int, Dict[str, dict]] = {}
        # Contador para IDs únicos de conexión
        self._connection_counter = 0

    def _generate_connection_id(self) -> str:
        """Generar ID único para una conexión"""
        self._connection_counter += 1
        return f"conn_{self._connection_counter}_{datetime.now().timestamp()}"

    async def connect(
        self,
        websocket: WebSocket,
        room_id: int,
        user_id: int,
        username: str
    ) -> str:
        """
        Conectar un cliente a una sala

        Args:
            websocket: Objeto WebSocket
            room_id: ID de la sala
            user_id: ID del usuario
            username: Nombre del usuario

        Returns:
            ID de conexión único
        """
        await websocket.accept()

        # Generar ID único para esta conexión
        connection_id = self._generate_connection_id()

        # Inicializar sala si no existe
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}

        # Guardar conexión
        self.active_connections[room_id][connection_id] = {
            "websocket": websocket,
            "user_id": user_id,
            "username": username
        }

        logger.info(
            f"✅ Usuario {username} (ID: {user_id}) conectado a sala {room_id}. "
            f"Conexiones activas en sala: {len(self.active_connections[room_id])}"
        )

        # Notificar a la sala que un usuario se unió
        await self.broadcast(
            room_id,
            create_event(
                EventType.USER_JOINED,
                user_id=user_id,
                username=username,
                message=f"{username} se unió a la sala"
            ),
            exclude_connection_id=connection_id  # No enviar al que acaba de conectarse
        )

        # Enviar confirmación de conexión al usuario
        await self.send_personal_message(
            create_event(
                EventType.CONNECTED,
                room_id=room_id,
                message="Conectado exitosamente",
                active_users=self.get_room_users(room_id)
            ),
            websocket
        )

        return connection_id

    async def disconnect(self, room_id: int, connection_id: str):
        """
        Desconectar un cliente de una sala

        Args:
            room_id: ID de la sala
            connection_id: ID de la conexión
        """
        if room_id not in self.active_connections:
            return

        if connection_id not in self.active_connections[room_id]:
            return

        # Obtener info del usuario antes de eliminar
        connection_info = self.active_connections[room_id][connection_id]
        user_id = connection_info["user_id"]
        username = connection_info["username"]

        # Eliminar conexión
        del self.active_connections[room_id][connection_id]

        # Si la sala quedó vacía, eliminarla
        if not self.active_connections[room_id]:
            del self.active_connections[room_id]
            logger.info(f"🗑️ Sala {room_id} eliminada (sin usuarios)")
        else:
            # Notificar a la sala que el usuario se fue
            await self.broadcast(
                room_id,
                create_event(
                    EventType.USER_LEFT,
                    user_id=user_id,
                    username=username,
                    message=f"{username} salió de la sala"
                )
            )

        logger.info(
            f"🚪 Usuario {username} (ID: {user_id}) desconectado de sala {room_id}"
        )

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Enviar mensaje a un cliente específico

        Args:
            message: Mensaje a enviar (diccionario)
            websocket: WebSocket del cliente
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje personal: {e}")

    async def broadcast(
        self,
        room_id: int,
        message: dict,
        exclude_connection_id: str = None
    ):
        """
        Enviar mensaje a todos los clientes de una sala

        Args:
            room_id: ID de la sala
            message: Mensaje a enviar (diccionario)
            exclude_connection_id: ID de conexión a excluir (opcional)
        """
        if room_id not in self.active_connections:
            logger.warning(f"⚠️ Intento de broadcast a sala inexistente: {room_id}")
            return

        # Obtener lista de conexiones
        connections = self.active_connections[room_id].copy()

        # Enviar a cada conexión
        disconnected = []
        for conn_id, conn_info in connections.items():
            # Excluir conexión si se especificó
            if exclude_connection_id and conn_id == exclude_connection_id:
                continue

            try:
                await conn_info["websocket"].send_json(message)
            except WebSocketDisconnect:
                logger.warning(f"⚠️ WebSocket desconectado durante broadcast: {conn_id}")
                disconnected.append(conn_id)
            except Exception as e:
                logger.error(f"❌ Error enviando mensaje a {conn_id}: {e}")
                disconnected.append(conn_id)

        # Limpiar conexiones desconectadas
        for conn_id in disconnected:
            await self.disconnect(room_id, conn_id)

        logger.info(
            f"📢 Broadcast a sala {room_id}: {len(connections) - len(disconnected)} destinatarios"
        )

    def get_room_users(self, room_id: int) -> List[dict]:
        """
        Obtener lista de usuarios en una sala

        Args:
            room_id: ID de la sala

        Returns:
            Lista de diccionarios con user_id y username
        """
        if room_id not in self.active_connections:
            return []

        users = []
        seen_user_ids = set()

        for conn_info in self.active_connections[room_id].values():
            user_id = conn_info["user_id"]
            # Evitar duplicados (un usuario puede tener múltiples conexiones)
            if user_id not in seen_user_ids:
                users.append({
                    "user_id": user_id,
                    "username": conn_info["username"]
                })
                seen_user_ids.add(user_id)

        return users

    def get_room_connection_count(self, room_id: int) -> int:
        """
        Obtener número de conexiones activas en una sala

        Args:
            room_id: ID de la sala

        Returns:
            Número de conexiones
        """
        if room_id not in self.active_connections:
            return 0
        return len(self.active_connections[room_id])

    def get_total_connections(self) -> int:
        """
        Obtener número total de conexiones activas

        Returns:
            Número total de conexiones
        """
        total = 0
        for room_connections in self.active_connections.values():
            total += len(room_connections)
        return total

    def get_stats(self) -> dict:
        """
        Obtener estadísticas de conexiones

        Returns:
            Diccionario con estadísticas
        """
        return {
            "total_connections": self.get_total_connections(),
            "total_rooms": len(self.active_connections),
            "rooms": {
                room_id: {
                    "connections": len(connections),
                    "users": len(self.get_room_users(room_id))
                }
                for room_id, connections in self.active_connections.items()
            }
        }


# Instancia global del manager
manager = ConnectionManager()
