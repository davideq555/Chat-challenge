import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { email, password } = body

    // TODO: Implementar lógica de autenticación con tu backend
    // Este es un ejemplo simulado
    console.log("[v0] Login attempt:", { email })

    // Simular respuesta exitosa
    return NextResponse.json({
      token: "example-jwt-token",
      user: {
        id: "1",
        name: "Usuario Demo",
        email: email,
      },
    })
  } catch (error) {
    console.error("[v0] Login error:", error)
    return NextResponse.json({ message: "Error al iniciar sesión" }, { status: 500 })
  }
}
