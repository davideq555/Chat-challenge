import { NextResponse } from "next/server"
import { writeFile } from "fs/promises"
import { join } from "path"

export async function POST(request: Request) {
  try {
    const formData = await request.FormData()
    const file = formData.get("file") as File
    const receiverId = formData.get("receiverId") as string
    const caption = formData.get("caption") as string

    if (!file) {
      return NextResponse.json({ message: "No se proporcionó archivo" }, { status: 400 })
    }

    console.log("[v0] Uploading file:", {
      name: file.name,
      type: file.type,
      size: file.size,
      receiverId,
      caption,
    })

    // TODO: Implementar lógica de subida de archivos a tu storage
    // Opciones:
    // 1. Vercel Blob Storage
    // 2. AWS S3
    // 3. Cloudinary
    // 4. Sistema de archivos local (solo para desarrollo)

    // Ejemplo con sistema de archivos local (solo desarrollo):
    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)

    // Generar nombre único para el archivo
    const uniqueName = `${Date.now()}-${file.name}`
    const path = join(process.cwd(), "public", "uploads", uniqueName)

    // Guardar archivo
    await writeFile(path, buffer)

    const fileUrl = `/uploads/${uniqueName}`

    return NextResponse.json({
      message: "Archivo subido exitosamente",
      fileUrl,
      fileName: file.name,
      fileType: file.type,
      fileSize: file.size,
    })
  } catch (error) {
    console.error("[v0] Error uploading file:", error)
    return NextResponse.json({ message: "Error al subir archivo" }, { status: 500 })
  }
}
