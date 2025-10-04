"use client"

import { useState, useEffect } from "react"
import { ChatSidebar } from "./chat-sidebar"
import { ChatWindow } from "./chat-window"
import { ChatHeader } from "./chat-header"
import { useRouter } from "next/navigation"
import { websocketService } from "@/lib/websocket"
import { useWebSocket } from "@/hooks/use-websocket"
import { apiClient } from "@/lib/api"

export type User = {
  id: string
  username: string
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
    const loadConversations = async () => {
      // Verificar autenticación
      const token = localStorage.getItem("token")
      const userStr = localStorage.getItem("user")

      if (!token || !userStr) {
        router.push("/login")
        return
      }

      const user = JSON.parse(userStr)
      setCurrentUser(user)

      try {
        // Cargar conversaciones reales desde el backend
        const backendConversations = await apiClient.loadUserConversations(user.id)

        // Transformar al formato del frontend
        const transformedConversations: Conversation[] = backendConversations
          .filter((conv: any) => conv.otherParticipant) // Solo mostrar salas con otro participante
          .map((conv: any) => {
            const lastMsg = conv.lastMessage

            return {
              id: conv.room.id.toString(),
              user: {
                id: conv.otherParticipant.user.id.toString(),
                username: conv.otherParticipant.user.username,
                email: conv.otherParticipant.user.email,
                isOnline: false, // TODO: Implementar estado online con WebSocket
              },
              lastMessage: lastMsg ? {
                id: lastMsg.id.toString(),
                content: lastMsg.content,
                senderId: lastMsg.user_id.toString(),
                receiverId: conv.otherParticipant.user.id.toString(),
                timestamp: lastMsg.created_at,
                type: "text",
              } : undefined,
              unreadCount: 0, // TODO: Implementar contador de no leídos
            }
          })

        setConversations(transformedConversations)
      } catch (error) {
        console.error("Error loading conversations:", error)
        setConversations([])
      }
    }

    loadConversations()

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
