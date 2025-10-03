import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { name, email, password } = body

    // TODO: Implementar lógica de registro con tu backend
    console.log("[v0] Register attempt:", { name, email })

    // Simular respuesta exitosa
    return NextResponse.json({
      message: "Usuario registrado exitosamente",
      user: {
        id: Date.now().toString(),
        name,
        email,
      },
    })
  } catch (error) {
    console.error("[v0] Register error:", error)
    return NextResponse.json({ message: "Error al registrar usuario" }, { status: 500 })
  }
}
