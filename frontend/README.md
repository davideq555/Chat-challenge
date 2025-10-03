# Chat Frontend

Este directorio contendrá la aplicación frontend del sistema de chat.

## Tecnologías

- **Next.js** - Framework React para aplicaciones web
- **TypeScript** - Para type safety
- **WebSockets** - Para comunicación en tiempo real con el backend

## Estado Actual

🚧 **En desarrollo** - Próximamente estará disponible la implementación del frontend.

## Funcionalidades Planificadas

- Interfaz de usuario para chat en tiempo real
- Autenticación de usuarios
- Salas de chat 1 a 1 y grupales
- Envío y recepción de mensajes
- Soporte para adjuntos (imágenes, archivos, etc.)
- Indicadores de estado online/offline
- Notificaciones en tiempo real

## API Backend

El frontend consumirá la API REST y WebSocket del backend ubicado en `/backend`.

### Endpoints Base
- API REST: `http://localhost:8000`
- WebSocket: `ws://localhost:8000/ws`

Para más detalles sobre los endpoints disponibles, consulta la documentación del backend o visita `http://localhost:8000/docs` cuando el servidor esté corriendo.
