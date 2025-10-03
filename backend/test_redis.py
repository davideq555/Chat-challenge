#!/usr/bin/env python3
"""
Script para probar la conexión a Redis
Ejecutar: python test_redis.py
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.redis_client import redis_client
from app.services.message_cache import message_cache

def test_redis_connection():
    """Probar conexión básica a Redis"""
    print("🔌 Probando conexión a Redis...")

    try:
        # Ping
        if redis_client.ping():
            print("✅ Redis está conectado correctamente")
        else:
            print("❌ Redis no respondió al ping")
            return False
    except Exception as e:
        print(f"❌ Error conectando a Redis: {e}")
        return False

    return True

def test_basic_operations():
    """Probar operaciones básicas"""
    print("\n📝 Probando operaciones básicas...")

    try:
        # SET y GET
        redis_client.set("test:key", "test_value")
        value = redis_client.get("test:key")
        assert value == "test_value", "Error en set/get"
        print("✅ SET/GET funciona")

        # SET con JSON
        test_data = {"id": 1, "name": "Test"}
        redis_client.set("test:json", test_data)
        retrieved = redis_client.get("test:json", as_json=True)
        assert retrieved == test_data, "Error en set/get JSON"
        print("✅ SET/GET con JSON funciona")

        # DELETE
        redis_client.delete("test:key", "test:json")
        assert redis_client.get("test:key") is None, "Error en delete"
        print("✅ DELETE funciona")

        # LISTAS
        redis_client.lpush("test:list", {"msg": "1"}, {"msg": "2"})
        items = redis_client.lrange("test:list", 0, -1, as_json=True)
        assert len(items) == 2, "Error en lpush/lrange"
        print("✅ LPUSH/LRANGE funciona")

        # Limpiar
        redis_client.delete("test:list")

    except Exception as e:
        print(f"❌ Error en operaciones básicas: {e}")
        return False

    return True

def test_message_cache():
    """Probar caché de mensajes"""
    print("\n💬 Probando caché de mensajes...")

    try:
        room_id = 999  # Sala de prueba

        # Cachear un mensaje
        message_data = {
            "id": 1,
            "room_id": room_id,
            "user_id": 1,
            "content": "Mensaje de prueba",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": None,
            "is_deleted": False
        }

        success = message_cache.cache_message(room_id, message_data)
        assert success, "Error cacheando mensaje"
        print("✅ Mensaje cacheado correctamente")

        # Obtener mensajes del caché
        cached = message_cache.get_cached_messages(room_id)
        assert cached is not None, "No se pudo obtener caché"
        assert len(cached) == 1, "Número incorrecto de mensajes"
        assert cached[0]["content"] == "Mensaje de prueba", "Contenido incorrecto"
        print("✅ Mensajes obtenidos del caché correctamente")

        # Invalidar caché
        message_cache.invalidate_room_cache(room_id)
        cached = message_cache.get_cached_messages(room_id)
        assert cached is None, "Caché no se invalidó"
        print("✅ Invalidación de caché funciona")

    except Exception as e:
        print(f"❌ Error en caché de mensajes: {e}")
        return False

    return True

def test_cache_stats():
    """Probar estadísticas del caché"""
    print("\n📊 Probando estadísticas...")

    try:
        stats = message_cache.get_cache_stats()
        assert "redis_connected" in stats, "Stats inválidas"
        assert stats["redis_connected"], "Redis no conectado según stats"
        print(f"✅ Stats obtenidas: {stats}")
    except Exception as e:
        print(f"❌ Error obteniendo stats: {e}")
        return False

    return True

def main():
    """Ejecutar todas las pruebas"""
    print("=" * 60)
    print("🧪 PRUEBAS DE REDIS - FASE 1")
    print("=" * 60)

    tests = [
        ("Conexión a Redis", test_redis_connection),
        ("Operaciones básicas", test_basic_operations),
        ("Caché de mensajes", test_message_cache),
        ("Estadísticas", test_cache_stats)
    ]

    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))

    # Resumen
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBAS")
    print("=" * 60)

    for name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status} - {name}")

    # Resultado final
    all_passed = all(result for _, result in results)
    print("=" * 60)
    if all_passed:
        print("🎉 TODAS LAS PRUEBAS PASARON")
        print("\n✅ Redis está configurado correctamente y listo para usar!")
        return 0
    else:
        print("⚠️  ALGUNAS PRUEBAS FALLARON")
        print("\n❌ Revisa la configuración de Redis en .env")
        print("   Asegúrate de que Redis esté ejecutándose:")
        print("   - Linux/Mac: redis-server")
        print("   - Docker: docker run -d -p 6379:6379 redis")
        return 1

if __name__ == "__main__":
    sys.exit(main())
