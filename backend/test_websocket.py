#!/usr/bin/env python3
"""
Cliente de prueba para WebSocket

Ejecutar:
    python test_websocket.py

Comandos:
    /help              - Mostrar ayuda
    /ping              - Enviar ping al servidor
    /typing            - Enviar evento de typing
    /stats             - Ver estadísticas de conexiones
    /quit o /exit      - Salir
    cualquier texto    - Enviar mensaje
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime

# Configuración
WS_URL = "ws://localhost:8000/ws"
ROOM_ID = 1
USER_ID = 1
USERNAME = "TestUser"

class Colors:
    """Códigos de color para la terminal"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(text, color):
    """Imprimir texto con color"""
    print(f"{color}{text}{Colors.ENDC}")

def print_event(event_type, data):
    """Imprimir evento recibido con formato"""
    timestamp = datetime.now().strftime("%H:%M:%S")

    if event_type == "connected":
        print_colored(f"[{timestamp}] ✅ Conectado a la sala {data.get('room_id')}", Colors.OKGREEN)
        users = data.get('active_users', [])
        if users:
            print_colored(f"  Usuarios en la sala: {', '.join(u['username'] for u in users)}", Colors.OKCYAN)

    elif event_type == "message":
        username = data.get('username', 'Unknown')
        content = data.get('content', '')
        print_colored(f"[{timestamp}] 💬 {username}: {content}", Colors.OKBLUE)

    elif event_type == "message_sent":
        print_colored(f"[{timestamp}] ✓ Mensaje enviado", Colors.OKGREEN)

    elif event_type == "user_joined":
        username = data.get('username', 'Unknown')
        print_colored(f"[{timestamp}] 👋 {username} se unió a la sala", Colors.OKCYAN)

    elif event_type == "user_left":
        username = data.get('username', 'Unknown')
        print_colored(f"[{timestamp}] 👋 {username} salió de la sala", Colors.WARNING)

    elif event_type == "typing":
        username = data.get('username', 'Unknown')
        is_typing = data.get('is_typing', False)
        if is_typing:
            print_colored(f"[{timestamp}] ✏️  {username} está escribiendo...", Colors.OKCYAN)

    elif event_type == "pong":
        print_colored(f"[{timestamp}] 🏓 Pong recibido", Colors.OKGREEN)

    elif event_type == "error":
        message = data.get('message', 'Error desconocido')
        print_colored(f"[{timestamp}] ❌ Error: {message}", Colors.FAIL)

    else:
        print_colored(f"[{timestamp}] 📨 Evento {event_type}: {data}", Colors.ENDC)

async def receive_messages(websocket):
    """Recibir y procesar mensajes del servidor"""
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                event_type = data.get('type')
                event_data = data.get('data', {})

                print_event(event_type, event_data)

            except json.JSONDecodeError:
                print_colored(f"❌ Error decodificando mensaje: {message}", Colors.FAIL)
    except websockets.exceptions.ConnectionClosed:
        print_colored("\n🔌 Conexión cerrada por el servidor", Colors.WARNING)

async def send_messages(websocket):
    """Enviar mensajes al servidor desde la entrada del usuario"""
    print_colored("\n" + "="*60, Colors.HEADER)
    print_colored("💬 CHAT CONECTADO - Escribe mensajes o comandos", Colors.HEADER)
    print_colored("="*60, Colors.HEADER)
    print_colored("Comandos: /help, /ping, /typing, /stats, /quit\n", Colors.OKCYAN)

    try:
        while True:
            # Leer entrada del usuario (de forma asíncrona)
            line = await asyncio.get_event_loop().run_in_executor(
                None, sys.stdin.readline
            )
            line = line.strip()

            if not line:
                continue

            # Procesar comandos
            if line.startswith('/'):
                command = line.lower()

                if command == '/help':
                    print_colored("\nComandos disponibles:", Colors.HEADER)
                    print("  /help     - Mostrar esta ayuda")
                    print("  /ping     - Verificar conexión")
                    print("  /typing   - Enviar evento de typing")
                    print("  /stats    - Ver estadísticas")
                    print("  /quit     - Salir del chat\n")

                elif command == '/ping':
                    await websocket.send(json.dumps({"type": "ping"}))

                elif command == '/typing':
                    await websocket.send(json.dumps({
                        "type": "typing",
                        "is_typing": True
                    }))

                elif command == '/stats':
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get('http://localhost:8000/ws/stats') as resp:
                            if resp.status == 200:
                                stats = await resp.json()
                                print_colored("\n📊 Estadísticas del servidor:", Colors.HEADER)
                                print(f"  Total conexiones: {stats['total_connections']}")
                                print(f"  Total salas: {stats['total_rooms']}")
                                if stats['rooms']:
                                    print("\n  Salas activas:")
                                    for room_id, room_stats in stats['rooms'].items():
                                        print(f"    - Sala {room_id}: {room_stats['connections']} conexiones, {room_stats['users']} usuarios\n")

                elif command in ['/quit', '/exit']:
                    print_colored("\n👋 Saliendo del chat...", Colors.WARNING)
                    break

                else:
                    print_colored(f"❌ Comando desconocido: {command}", Colors.FAIL)
                    print_colored("Usa /help para ver comandos disponibles", Colors.OKCYAN)

            else:
                # Enviar mensaje normal
                await websocket.send(json.dumps({
                    "type": "message",
                    "content": line
                }))

    except EOFError:
        print_colored("\n👋 EOF detectado, saliendo...", Colors.WARNING)

async def main():
    """Función principal"""
    url = f"{WS_URL}/{ROOM_ID}?user_id={USER_ID}&username={USERNAME}"

    print_colored("="*60, Colors.HEADER)
    print_colored("🚀 CLIENTE WEBSOCKET DE PRUEBA", Colors.HEADER)
    print_colored("="*60, Colors.HEADER)
    print(f"URL: {url}")
    print(f"Sala: {ROOM_ID}")
    print(f"Usuario: {USERNAME} (ID: {USER_ID})")
    print_colored("="*60 + "\n", Colors.HEADER)

    try:
        async with websockets.connect(url) as websocket:
            # Ejecutar recepción y envío en paralelo
            receive_task = asyncio.create_task(receive_messages(websocket))
            send_task = asyncio.create_task(send_messages(websocket))

            # Esperar a que cualquiera termine
            done, pending = await asyncio.wait(
                [receive_task, send_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancelar tareas pendientes
            for task in pending:
                task.cancel()

    except websockets.exceptions.WebSocketException as e:
        print_colored(f"\n❌ Error de WebSocket: {e}", Colors.FAIL)
        print_colored("\n¿El servidor está corriendo?", Colors.WARNING)
        print_colored("Ejecuta: uvicorn app.main:app --reload", Colors.OKCYAN)

    except KeyboardInterrupt:
        print_colored("\n\n👋 Interrumpido por el usuario", Colors.WARNING)

    except Exception as e:
        print_colored(f"\n❌ Error inesperado: {e}", Colors.FAIL)

if __name__ == "__main__":
    # Instalar dependencias si no están
    try:
        import websockets
        import aiohttp
    except ImportError:
        print_colored("❌ Dependencias faltantes. Instalando...", Colors.FAIL)
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "websockets", "aiohttp"])
        print_colored("✅ Dependencias instaladas. Por favor ejecuta el script nuevamente.", Colors.OKGREEN)
        sys.exit(0)

    # Ejecutar cliente
    asyncio.run(main())
