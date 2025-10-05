"use client"

import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"
import type { Conversation } from "./chat-layout"
import { formatDistanceToNow } from "date-fns"
import { es } from "date-fns/locale"

type ConversationItemProps = {
  conversation: Conversation
  isSelected: boolean
  onClick: () => void
  currentUserId: string
}

export function ConversationItem({ conversation, isSelected, onClick, currentUserId }: ConversationItemProps) {
  const { user, lastMessage, unreadCount, isGroup, roomName, participants } = conversation

  const displayName = isGroup && roomName ? roomName : user.username

  const getInitials = (username: string) => {
    // Si el username tiene espacios, tomar iniciales de cada palabra
    // Si no, tomar las primeras 2 letras
    if (username.includes(" ")) {
      return username
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    }
    return username.slice(0, 2).toUpperCase()
  }

  const formatTime = (timestamp: string) => {
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true, locale: es })
    } catch {
      return ""
    }
  }

  const getMessagePreview = () => {
    if (!lastMessage) return "Sin mensajes"

    let prefix = ""

    if (isGroup) {
      // En grupos, mostrar el nombre del usuario que envió el mensaje
      if (lastMessage.senderId === currentUserId) {
        prefix = "Tú: "
      } else {
        // Buscar el nombre del participante que envió el mensaje
        const sender = participants?.find(p => p.id === lastMessage.senderId)
        prefix = sender ? `${sender.username}: ` : ""
      }
    } else {
      // En chats 1-a-1, solo mostrar "Tú:" si fue el usuario actual
      prefix = lastMessage.senderId === currentUserId ? "Tú: " : ""
    }

    if (lastMessage.type === "image") return `${prefix}📷 Imagen`
    if (lastMessage.type === "document") return `${prefix}📄 ${lastMessage.fileName || "Documento"}`

    return `${prefix}${lastMessage.content}`
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full flex items-center gap-3 p-3 rounded-lg hover:bg-accent transition-colors text-left",
        isSelected && "bg-accent",
      )}
    >
      <div className="relative">
        <Avatar>
          <AvatarFallback className="bg-primary/10 text-primary">{getInitials(displayName)}</AvatarFallback>
        </Avatar>
        {!isGroup && user.isOnline && (
          <div className="absolute bottom-0 right-0 h-3 w-3 rounded-full bg-[var(--online-indicator)] border-2 border-card" />
        )}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 mb-1">
          <span className="font-semibold text-card-foreground truncate">{displayName}</span>
          {lastMessage && (
            <span className="text-xs text-muted-foreground flex-shrink-0">{formatTime(lastMessage.timestamp)}</span>
          )}
        </div>
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm text-muted-foreground truncate">{getMessagePreview()}</p>
          {unreadCount > 0 && (
            <span className="flex-shrink-0 h-5 min-w-5 px-1.5 rounded-full bg-primary text-primary-foreground text-xs font-medium flex items-center justify-center">
              {unreadCount}
            </span>
          )}
        </div>
      </div>
    </button>
  )
}
