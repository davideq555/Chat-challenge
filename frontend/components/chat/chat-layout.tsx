"use client"

import { useState, useEffect } from "react"
import { ChatSidebar } from "./chat-sidebar"
import { ChatWindow } from "./chat-window"
import { ChatHeader } from "./chat-header"
import { useRouter } from "next/navigation"
import { websocketService } from "@/lib/websocket"
import { useWebSocket } from "@/hooks/use-websocket"

export type User = {
  id: string
  name: string
  email: string
  avatar?: string
  isOnline?: boolean
  lastSeen?: string
}

export type Message = {
  id: string
  content: string
  senderId: string
  receiverId: string
  roomId?: string
  timestamp: string
  type: "text" | "image" | "document"
  fileUrl?: string
  fileName?: string
}

export type Conversation = {
  id: string
  user: User
  lastMessage?: Message
  unreadCount: number
}

export function ChatLayout() {
  const router = useRouter()
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [onlineUsers, setOnlineUsers] = useState<Set<string>>(new Set())

  const ws = useWebSocket((message) => {
    console.log("[v0] Received WebSocket message:", message)

    switch (message.type) {
      case "message":
        handleNewMessage(message.data)
        break
      case "online":
        setOnlineUsers((prev) => new Set(prev).add(message.data.userId))
        updateUserOnlineStatus(message.data.userId, true)
        break
      case "offline":
        setOnlineUsers((prev) => {
          const newSet = new Set(prev)
          newSet.delete(message.data.userId)
          return newSet
        })
        updateUserOnlineStatus(message.data.userId, false)
        break
      case "typing":
        // Handle typing indicator
        break
    }
  })

  const handleNewMessage = (newMessage: Message) => {
    // Update conversations with new message
    setConversations((prev) =>
      prev.map((conv) => {
        if (conv.user.id === newMessage.senderId || conv.user.id === newMessage.receiverId) {
          return {
            ...conv,
            lastMessage: newMessage,
            unreadCount: newMessage.senderId !== currentUser?.id ? conv.unreadCount + 1 : conv.unreadCount,
          }
        }
        return conv
      }),
    )
  }

  const updateUserOnlineStatus = (userId: string, isOnline: boolean) => {
    setConversations((prev) =>
      prev.map((conv) => {
        if (conv.user.id === userId) {
          return {
            ...conv,
            user: {
              ...conv.user,
              isOnline,
              lastSeen: isOnline ? undefined : "Hace un momento",
            },
          }
        }
        return conv
      }),
    )
  }

  useEffect(() => {
    // Verificar autenticación
    const token = localStorage.getItem("token")
    const userStr = localStorage.getItem("user")

    if (!token || !userStr) {
      router.push("/login")
      return
    }

    const user = JSON.parse(userStr)
    setCurrentUser(user)

    // TODO: Reemplazar con la URL de tu backend WebSocket
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8080/ws"
    websocketService.connect(wsUrl, token)

    // TODO: Cargar conversaciones desde el backend
    // Datos de ejemplo
    setConversations([
      {
        id: "1",
        user: {
          id: "2",
          name: "María García",
          email: "maria@example.com",
          isOnline: true,
        },
        lastMessage: {
          id: "1",
          content: "Hola, ¿cómo estás?",
          senderId: "2",
          receiverId: user.id,
          timestamp: new Date().toISOString(),
          type: "text",
        },
        unreadCount: 2,
      },
      {
        id: "2",
        user: {
          id: "3",
          name: "Carlos Rodríguez",
          email: "carlos@example.com",
          isOnline: false,
          lastSeen: "Hace 2 horas",
        },
        lastMessage: {
          id: "2",
          content: "Perfecto, nos vemos mañana",
          senderId: user.id,
          receiverId: "3",
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          type: "text",
        },
        unreadCount: 0,
      },
      {
        id: "3",
        user: {
          id: "4",
          name: "Ana Martínez",
          email: "ana@example.com",
          isOnline: true,
        },
        lastMessage: {
          id: "3",
          content: "Gracias por la información",
          senderId: "4",
          receiverId: user.id,
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          type: "text",
        },
        unreadCount: 0,
      },
    ])

    return () => {
      websocketService.disconnect()
    }
  }, [router])

  if (!currentUser) {
    return (
      <div className="h-screen flex items-center justify-center bg-background">
        <div className="text-muted-foreground">Cargando...</div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-background">
      <ChatHeader currentUser={currentUser} />
      <div className="flex-1 flex overflow-hidden">
        <ChatSidebar
          conversations={conversations}
          selectedConversation={selectedConversation}
          onSelectConversation={setSelectedConversation}
          currentUser={currentUser}
        />
        <ChatWindow selectedConversation={selectedConversation} currentUser={currentUser} />
      </div>
    </div>
  )
}
