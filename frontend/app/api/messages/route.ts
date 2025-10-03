import { NextResponse } from "next/server"

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const userId = searchParams.get("userId")

    // TODO: Implementar lógica para cargar mensajes desde tu backend
    console.log("[v0] Loading messages for user:", userId)

    // Simular respuesta con mensajes de ejemplo
    return NextResponse.json({
      messages: [
        {
          id: "1",
          content: "Hola, ¿cómo estás?",
          senderId: userId,
          receiverId: "current-user-id",
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          type: "text",
        },
      ],
    })
  } catch (error) {
    console.error("[v0] Error loading messages:", error)
    return NextResponse.json({ message: "Error al cargar mensajes" }, { status: 500 })
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json()

    // TODO: Implementar lógica para guardar mensaje en tu backend
    console.log("[v0] Saving message:", body)

    return NextResponse.json({
      message: "Mensaje guardado exitosamente",
      id: Date.now().toString(),
    })
  } catch (error) {
    console.error("[v0] Error saving message:", error)
    return NextResponse.json({ message: "Error al guardar mensaje" }, { status: 500 })
  }
}
