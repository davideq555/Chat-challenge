export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes"

  const k = 1024
  const sizes = ["Bytes", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i]
}

export function getFileExtension(filename: string): string {
  return filename.slice(((filename.lastIndexOf(".") - 1) >>> 0) + 2)
}

export function isImageFile(filename: string): boolean {
  const imageExtensions = ["jpg", "jpeg", "png", "gif", "webp", "svg", "bmp"]
  const ext = getFileExtension(filename).toLowerCase()
  return imageExtensions.includes(ext)
}

export function isDocumentFile(filename: string): boolean {
  const docExtensions = ["pdf", "doc", "docx", "txt", "xls", "xlsx", "ppt", "pptx"]
  const ext = getFileExtension(filename).toLowerCase()
  return docExtensions.includes(ext)
}

export function validateFile(file: File, maxSize: number = 10 * 1024 * 1024): { valid: boolean; error?: string } {
  if (file.size > maxSize) {
    return {
      valid: false,
      error: `El archivo es demasiado grande. Máximo ${formatFileSize(maxSize)}`,
    }
  }

  return { valid: true }
}
