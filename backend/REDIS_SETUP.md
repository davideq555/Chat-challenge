# 🔴 Redis - Fase 1 Implementada

## ✅ ¿Qué se ha implementado?

### 1. **Redis Client** (`app/redis_client.py`)
Cliente Redis con operaciones básicas:
- ✅ SET/GET (strings y JSON)
- ✅ LISTS (lpush, rpush, lrange, ltrim)
- ✅ SETS (sadd, srem, smembers)
- ✅ PUB/SUB (publish, subscribe)
- ✅ Expiración (expire, ttl)
- ✅ Utilidades (ping, delete, exists)

### 2. **Message Cache Service** (`app/services/message_cache.py`)
Servicio de caché para mensajes:
- ✅ Cachear nuevos mensajes
- ✅ Obtener mensajes del caché
- ✅ Invalidar caché por sala
- ✅ Actualizar caché desde DB
- ✅ Estadísticas del caché

### 3. **Integración en API**
- ✅ Caché en `POST /messages/` (guardar nuevo mensaje)
- ✅ Caché en `GET /messages/room/{room_id}/latest` (obtener mensajes)
- ✅ Healthcheck en `GET /health` (verificar Redis + PostgreSQL)
- ✅ Stats en `GET /cache/stats`

---

## 🚀 Instalación y Configuración

### **1. Instalar Redis**

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### macOS
```bash
brew install redis
brew services start redis
```

#### Docker
```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

### **2. Verificar instalación**
```bash
redis-cli ping
# Debe responder: PONG
```

### **3. Configurar en .env**
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Dejar vacío si no tienes contraseña
```

---

## 🧪 Probar Redis

### **Opción 1: Script de prueba**
```bash
cd backend
python test_redis.py
```

Esto probará:
- ✅ Conexión a Redis
- ✅ Operaciones básicas (SET/GET, LISTS, etc.)
- ✅ Caché de mensajes
- ✅ Estadísticas

### **Opción 2: Endpoints de la API**

1. **Iniciar el servidor**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

2. **Probar healthcheck**
```bash
curl http://localhost:8000/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "services": {
    "api": "ok",
    "database": "ok",
    "redis": "ok"
  }
}
```

3. **Ver estadísticas del caché**
```bash
curl http://localhost:8000/cache/stats
```

Respuesta esperada:
```json
{
  "redis_connected": true,
  "ttl": 3600,
  "max_messages_per_room": 50
}
```

---

## 📊 Cómo funciona el caché

### **Flujo al crear un mensaje:**
```
1. Cliente → POST /messages/
2. Backend guarda en PostgreSQL
3. Backend cachea en Redis (últimos 50 mensajes)
4. Responde al cliente
```

### **Flujo al obtener mensajes:**
```
1. Cliente → GET /messages/room/{room_id}/latest
2. Backend verifica caché Redis
   ├─ ✅ Si hay caché → Retorna desde Redis (rápido)
   └─ ❌ Si no hay caché → Consulta PostgreSQL + Actualiza Redis
3. Responde al cliente
```

### **Ventajas:**
- 🚀 **10-100x más rápido** que consultar la DB
- 💰 **Reduce carga** en PostgreSQL
- 🔄 **Auto-expiración** (TTL de 1 hora)
- 📦 **Límite de 50 mensajes** por sala

---

## 🔑 Claves Redis usadas

```
messages:room:{room_id}  # Lista de últimos mensajes por sala
```

Ejemplo:
```
messages:room:1  # Mensajes de la sala 1
messages:room:2  # Mensajes de la sala 2
```

---

## 🛠️ Comandos útiles

### **Ver todas las claves en Redis**
```bash
redis-cli KEYS "*"
```

### **Ver mensajes de una sala**
```bash
redis-cli LRANGE messages:room:1 0 -1
```

### **Limpiar toda la base de datos (desarrollo)**
```bash
redis-cli FLUSHDB
```

### **Ver info de Redis**
```bash
redis-cli INFO
```

### **Monitorear en tiempo real**
```bash
redis-cli MONITOR
```

---

## ⚠️ Troubleshooting

### **Error: Redis connection refused**
```
❌ Error conectando a Redis: [Errno 111] Connection refused
```

**Solución:**
1. Verifica que Redis esté ejecutándose: `redis-cli ping`
2. Si no está corriendo: `sudo systemctl start redis-server`
3. Verifica puerto en `.env`: `REDIS_PORT=6379`

### **Error: ModuleNotFoundError: No module named 'redis'**
```
ModuleNotFoundError: No module named 'redis'
```

**Solución:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### **Redis funciona pero el caché no**
1. Verifica logs: `uvicorn app.main:app --reload --log-level debug`
2. Verifica healthcheck: `curl http://localhost:8000/health`
3. Ejecuta script de prueba: `python test_redis.py`

---

## 📈 Próximos pasos (Fase 2 y 3)

- [ ] **WebSocket Manager** - Gestión de conexiones en tiempo real
- [ ] **Redis Pub/Sub** - Broadcast distribuido entre servidores
- [ ] **Typing indicators** - Indicadores de "escribiendo..."
- [ ] **User presence** - Estado online/offline con Redis Sets
- [ ] **Rate limiting** - Limitar requests con Redis

---

## 📚 Recursos

- [Documentación Redis](https://redis.io/docs/)
- [redis-py (cliente Python)](https://redis-py.readthedocs.io/)
- [Redis Commands](https://redis.io/commands/)

---

**Estado actual:** ✅ **Fase 1 completa** - Redis configurado y funcionando con caché de mensajes
