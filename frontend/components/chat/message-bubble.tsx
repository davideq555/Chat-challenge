"use client"

import { cn } from "@/lib/utils"
import type { Message } from "./chat-layout"
import { format } from "date-fns"
import { es } from "date-fns/locale"
import { CheckCheck, Download, FileIcon, ExternalLink } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useState } from "react"

type MessageBubbleProps = {
  message: Message
  isOwn: boolean
  isGroup?: boolean
  senderName?: string
}

export function MessageBubble({ message, isOwn, isGroup, senderName }: MessageBubbleProps) {
  const [imageLoaded, setImageLoaded] = useState(false)

  const formatTime = (timestamp: string) => {
    try {
      return format(new Date(timestamp), "HH:mm", { locale: es })
    } catch {
      return ""
    }
  }

  const handleDownload = async () => {
    if (!message.fileUrl) return

    try {
      const response = await fetch(message.fileUrl)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = message.fileName || "download"
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error("[v0] Error downloading file:", error)
    }
  }

  const renderMessageContent = () => {
    if (message.type === "image" && message.fileUrl) {
      return (
        <div className="space-y-2">
          <div className="relative group">
            {!imageLoaded && (
              <div className="w-full h-48 bg-muted animate-pulse rounded-lg flex items-center justify-center">
                <span className="text-muted-foreground text-sm">Cargando...</span>
              </div>
            )}
            <img
              src={message.fileUrl || "/placeholder.svg"}
              alt="Imagen compartida"
              className={cn(
                "rounded-lg max-w-xs cursor-pointer transition-opacity",
                imageLoaded ? "opacity-100" : "opacity-0",
              )}
              onLoad={() => setImageLoaded(true)}
              onClick={() => window.open(message.fileUrl, "_blank")}
            />
            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center gap-2">
              <Button
                size="icon"
                variant="secondary"
                className="h-10 w-10"
                onClick={(e) => {
                  e.stopPropagation()
                  handleDownload()
                }}
              >
                <Download className="h-5 w-5" />
              </Button>
              <Button
                size="icon"
                variant="secondary"
                className="h-10 w-10"
                onClick={(e) => {
                  e.stopPropagation()
                  window.open(message.fileUrl, "_blank")
                }}
              >
                <ExternalLink className="h-5 w-5" />
              </Button>
            </div>
          </div>
          {message.content && <p className="text-sm">{message.content}</p>}
        </div>
      )
    }

    if (message.type === "document" && message.fileUrl) {
      return (
        <div className="flex items-center gap-3 p-3 bg-background/50 rounded-lg min-w-[250px]">
          <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
            <FileIcon className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{message.fileName || "Documento"}</p>
            {message.content && <p className="text-xs text-muted-foreground mt-1">{message.content}</p>}
          </div>
          <Button size="icon" variant="ghost" onClick={handleDownload} title="Descargar">
            <Download className="h-4 w-4" />
          </Button>
        </div>
      )
    }

    return <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
  }

  return (
    <div className={cn("flex flex-col", isOwn ? "items-end" : "items-start")}>
      {isGroup && !isOwn && senderName && (
        <span className="text-xs font-medium text-muted-foreground mb-1 ml-2">
          {senderName}
        </span>
      )}
      <div
        className={cn(
          "max-w-[70%] rounded-lg px-4 py-2 shadow-sm",
          isOwn
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-foreground",
        )}
      >
        {renderMessageContent()}
        <div className={cn("flex items-center gap-1 mt-1", isOwn ? "justify-end" : "justify-start")}>
          <span className={cn("text-xs", isOwn ? "text-primary-foreground/70" : "text-muted-foreground")}>
            {formatTime(message.timestamp)}
          </span>
          {isOwn && <CheckCheck className="h-3.5 w-3.5 text-primary-foreground/70" />}
        </div>
      </div>
    </div>
  )
}
