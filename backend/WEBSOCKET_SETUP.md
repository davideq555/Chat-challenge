# 🌐 WebSocket - Fase 2 Implementada

## ✅ ¿Qué se ha implementado?

### 1. **WebSocket Events** (`app/websockets/events.py`)
Tipos de eventos soportados:
- ✅ `message` - Enviar/recibir mensajes
- ✅ `message_sent` - Confirmación de mensaje enviado
- ✅ `user_joined` - Usuario se unió a la sala
- ✅ `user_left` - Usuario salió de la sala
- ✅ `typing` - Usuario está escribiendo
- ✅ `connected` - Confirmación de conexión
- ✅ `error` - Errores del servidor
- ✅ `ping/pong` - Verificar conexión

### 2. **Connection Manager** (`app/websockets/manager.py`)
Gestión de conexiones WebSocket:
- ✅ Conectar/desconectar usuarios por sala
- ✅ Broadcast a toda la sala
- ✅ Mensajes personales
- ✅ Lista de usuarios activos
- ✅ Estadísticas de conexiones
- ✅ Manejo automático de desconexiones

### 3. **WebSocket Router** (`app/routers/websocket.py`)
Endpoints:
- ✅ `ws://localhost:8000/ws/{room_id}` - Conexión WebSocket
- ✅ `GET /ws/stats` - Estadísticas de conexiones

### 4. **Cliente de Prueba** (`test_websocket.py`)
Script interactivo para probar WebSockets:
- ✅ Conectar a una sala
- ✅ Enviar mensajes
- ✅ Ver mensajes en tiempo real
- ✅ Comandos especiales (/ping, /typing, /stats)

---

## 🚀 Cómo usar WebSockets

### **1. Iniciar el servidor**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### **2. Conectar desde Python**

```python
import asyncio
import websockets
import json

async def test():
    url = "ws://localhost:8000/ws/1?user_id=1&username=Juan"

    async with websockets.connect(url) as ws:
        # Recibir confirmación de conexión
        response = await ws.recv()
        print(f"Conectado: {response}")

        # Enviar mensaje
        await ws.send(json.dumps({
            "type": "message",
            "content": "Hola mundo!"
        }))

        # Recibir respuesta
        response = await ws.recv()
        print(f"Respuesta: {response}")

asyncio.run(test())
```

### **3. Conectar desde JavaScript**

```javascript
// Conectar a WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/1?user_id=1&username=Juan');

// Escuchar conexión
ws.onopen = () => {
    console.log('✅ Conectado');
};

// Escuchar mensajes
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('📨 Evento:', data.type, data.data);

    if (data.type === 'message') {
        console.log(`💬 ${data.data.username}: ${data.data.content}`);
    }
};

// Enviar mensaje
function sendMessage(content) {
    ws.send(JSON.stringify({
        type: 'message',
        content: content
    }));
}

// Indicar que está escribiendo
function sendTyping(isTyping) {
    ws.send(JSON.stringify({
        type: 'typing',
        is_typing: isTyping
    }));
}

// Uso:
sendMessage('Hola a todos!');
sendTyping(true);  // Empezar a escribir
sendTyping(false); // Dejar de escribir
```

---

## 🧪 Probar WebSockets

### **Opción 1: Cliente de prueba (Python)**

```bash
cd backend
python test_websocket.py
```

Abre **2 o más terminales** con el script para simular varios usuarios:

**Terminal 1:**
```bash
USER_ID=1 USERNAME="Alice" python test_websocket.py
```

**Terminal 2:**
```bash
USER_ID=2 USERNAME="Bob" python test_websocket.py
```

Escribe mensajes en una terminal y verás cómo aparecen en la otra en tiempo real!

### **Opción 2: Extensión de navegador**

1. Instala extensión "WebSocket Test Client" en Chrome/Firefox
2. Conecta a: `ws://localhost:8000/ws/1?user_id=1&username=Juan`
3. Envía mensajes en formato JSON:
   ```json
   {"type": "message", "content": "Hola!"}
   ```

### **Opción 3: cURL/websocat**

```bash
# Instalar websocat
brew install websocat  # macOS
# o descargar desde https://github.com/vi/websocat

# Conectar
websocat "ws://localhost:8000/ws/1?user_id=1&username=Test"

# Escribir mensajes
{"type": "message", "content": "Hola!"}
```

---

## 📊 Flujo de mensajes

### **Enviar un mensaje:**

```
1. Cliente → {"type": "message", "content": "Hola"}
2. Servidor guarda en PostgreSQL
3. Servidor cachea en Redis
4. Servidor → Cliente: {"type": "message_sent", "message_id": 123}
5. Servidor → Todos en sala: {"type": "message", "data": {...}}
```

### **Usuario se une:**

```
1. Cliente conecta a ws://.../ws/1?user_id=1&username=Juan
2. Servidor → Cliente: {"type": "connected", "data": {"active_users": [...]}}
3. Servidor → Otros usuarios: {"type": "user_joined", "data": {"username": "Juan"}}
```

### **Typing indicator:**

```
1. Cliente → {"type": "typing", "is_typing": true}
2. Servidor → Otros usuarios: {"type": "typing", "data": {"username": "Juan", "is_typing": true}}
```

---

## 📨 Tipos de eventos

### **Eventos del cliente → servidor:**

| Tipo | Payload | Descripción |
|------|---------|-------------|
| `message` | `{content: string}` | Enviar mensaje |
| `typing` | `{is_typing: bool}` | Indicar que escribe |
| `ping` | `{}` | Verificar conexión |

### **Eventos del servidor → cliente:**

| Tipo | Payload | Descripción |
|------|---------|-------------|
| `connected` | `{room_id, active_users}` | Confirmación de conexión |
| `message` | `{id, user_id, username, content, created_at}` | Nuevo mensaje |
| `message_sent` | `{message_id, timestamp}` | Confirmación de envío |
| `user_joined` | `{user_id, username}` | Usuario se unió |
| `user_left` | `{user_id, username}` | Usuario se fue |
| `typing` | `{user_id, username, is_typing}` | Alguien escribe |
| `pong` | `{}` | Respuesta a ping |
| `error` | `{message, code}` | Error |

---

## 🔍 Endpoints de administración

### **Ver estadísticas de conexiones**

```bash
curl http://localhost:8000/ws/stats
```

Respuesta:
```json
{
  "total_connections": 5,
  "total_rooms": 2,
  "rooms": {
    "1": {
      "connections": 3,
      "users": 3
    },
    "2": {
      "connections": 2,
      "users": 2
    }
  }
}
```

---

## 🛠️ Características implementadas

### ✅ Gestión de conexiones
- Múltiples usuarios por sala
- Auto-desconexión en caso de error
- Notificación cuando usuarios entran/salen

### ✅ Mensajes en tiempo real
- Broadcast a toda la sala
- Confirmación de envío
- Persistencia en PostgreSQL
- Caché en Redis

### ✅ Typing indicators
- Notificar cuando alguien escribe
- No se envía al mismo usuario

### ✅ Manejo de errores
- Validación de JSON
- Eventos de error descriptivos
- Reconexión automática del cliente

---

## ⚠️ Troubleshooting

### **Error: Connection refused**
```
❌ Error de WebSocket: Cannot connect to host localhost:8000
```

**Solución:**
```bash
# Verificar que el servidor está corriendo
uvicorn app.main:app --reload

# Verificar que está en el puerto correcto
curl http://localhost:8000/health
```

### **Mensajes no se reciben**

1. Verificar que PostgreSQL está corriendo: `GET /health`
2. Ver logs del servidor: `uvicorn app.main:app --reload --log-level debug`
3. Verificar que el room_id existe en la DB

### **Cliente de prueba no funciona**

```bash
# Instalar dependencias
pip install websockets aiohttp

# Ejecutar con debug
python test_websocket.py
```

---

## 📈 Próximos pasos (Fase 3)

La **Fase 3** integrará Redis Pub/Sub con WebSockets para escalabilidad horizontal:

- [ ] **Redis Pub/Sub** - Broadcast distribuido entre servidores
- [ ] **Multiple server instances** - Escalar horizontalmente
- [ ] **Presence tracking** - Estado online/offline persistente
- [ ] **Message history on connect** - Cargar últimos mensajes al conectar
- [ ] **Read receipts** - Confirmación de lectura
- [ ] **Reconnection logic** - Manejo automático de reconexión

---

## 🎯 Ventajas actuales

- ⚡ **Tiempo real** - Mensajes instantáneos sin polling
- 💾 **Persistencia** - Todo se guarda en PostgreSQL
- 🚀 **Performance** - Caché Redis para mensajes recientes
- 👥 **Multi-usuario** - Múltiples usuarios por sala
- 📊 **Monitoreo** - Estadísticas de conexiones en vivo
- 🔄 **Bidireccional** - Cliente y servidor pueden iniciar comunicación

---

## 📚 Recursos

- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [WebSocket Protocol (RFC 6455)](https://tools.ietf.org/html/rfc6455)
- [websockets library (Python)](https://websockets.readthedocs.io/)

---

**Estado actual:** ✅ **Fase 2 completa** - WebSocket funcionando con chat en tiempo real

**Siguiente:** 🔴 **Fase 3** - Redis Pub/Sub para escalabilidad horizontal
