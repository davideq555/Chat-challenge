"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send, Paperclip, ImageIcon, File, Smile, MoreVertical } from "lucide-react"
import { MessageBubble } from "./message-bubble"
import { FileUploadDialog } from "./file-upload-dialog"
import type { Conversation, User, Message } from "./chat-layout"
import { websocketService } from "@/lib/websocket"
import { useWebSocket } from "@/hooks/use-websocket"

type ChatWindowProps = {
  selectedConversation: Conversation | null
  currentUser: User
}

export function ChatWindow({ selectedConversation, currentUser }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [messageInput, setMessageInput] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const [fileDialogOpen, setFileDialogOpen] = useState(false)
  const [uploadType, setUploadType] = useState<"image" | "document">("image")
  const scrollRef = useRef<HTMLDivElement>(null)
  const typingTimeoutRef = useRef<NodeJS.Timeout>()

  const ws = useWebSocket((message) => {
    if (message.type === "message" && selectedConversation) {
      const newMessage = message.data as Message
      // Only add message if it's for this conversation
      if (
        (newMessage.senderId === selectedConversation.user.id && newMessage.receiverId === currentUser.id) ||
        (newMessage.senderId === currentUser.id && newMessage.receiverId === selectedConversation.user.id)
      ) {
        setMessages((prev) => [...prev, newMessage])
      }
    } else if (message.type === "typing" && selectedConversation) {
      if (message.data.senderId === selectedConversation.user.id) {
        setIsTyping(message.data.isTyping)
      }
    }
  })

  useEffect(() => {
    if (selectedConversation) {
      loadMessages(selectedConversation.user.id)

      const roomId = [currentUser.id, selectedConversation.user.id].sort().join("-")
      websocketService.joinRoom(roomId)

      return () => {
        websocketService.leaveRoom(roomId)
      }
    }
  }, [selectedConversation, currentUser.id])

  const loadMessages = async (userId: string) => {
    try {
      // TODO: Cargar mensajes desde el backend
      const response = await fetch(`/api/messages?userId=${userId}`)
      if (response.ok) {
        const data = await response.json()
        setMessages(data.messages)
      } else {
        // Datos de ejemplo si falla la API
        setMessages([
          {
            id: "1",
            content: "Hola, ¿cómo estás?",
            senderId: userId,
            receiverId: currentUser.id,
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            type: "text",
          },
          {
            id: "2",
            content: "¡Hola! Todo bien, gracias. ¿Y tú?",
            senderId: currentUser.id,
            receiverId: userId,
            timestamp: new Date(Date.now() - 3500000).toISOString(),
            type: "text",
          },
          {
            id: "3",
            content: "Muy bien también. ¿Tienes tiempo para una reunión hoy?",
            senderId: userId,
            receiverId: currentUser.id,
            timestamp: new Date(Date.now() - 3400000).toISOString(),
            type: "text",
          },
          {
            id: "4",
            content: "Claro, ¿a qué hora te viene bien?",
            senderId: currentUser.id,
            receiverId: userId,
            timestamp: new Date(Date.now() - 3300000).toISOString(),
            type: "text",
          },
        ])
      }
    } catch (error) {
      console.error("[v0] Error loading messages:", error)
    }
  }

  useEffect(() => {
    // Auto-scroll al final cuando hay nuevos mensajes
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleSendMessage = async () => {
    if (!messageInput.trim() || !selectedConversation) return

    const newMessage: Message = {
      id: Date.now().toString(),
      content: messageInput,
      senderId: currentUser.id,
      receiverId: selectedConversation.user.id,
      timestamp: new Date().toISOString(),
      type: "text",
    }

    setMessages([...messages, newMessage])
    setMessageInput("")

    websocketService.sendMessage(newMessage)

    try {
      await fetch("/api/messages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify(newMessage),
      })
    } catch (error) {
      console.error("[v0] Error sending message:", error)
    }
  }

  const handleFileUpload = async (file: File, caption: string) => {
    if (!selectedConversation) return

    try {
      // Upload file to server
      const formData = new FormData()
      formData.append("file", file)
      formData.append("receiverId", selectedConversation.user.id)
      formData.append("caption", caption)

      const response = await fetch("/api/upload", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: formData,
      })

      if (!response.ok) {
        throw new Error("Upload failed")
      }

      const data = await response.json()

      // Create message with file
      const newMessage: Message = {
        id: Date.now().toString(),
        content: caption,
        senderId: currentUser.id,
        receiverId: selectedConversation.user.id,
        timestamp: new Date().toISOString(),
        type: file.type.startsWith("image/") ? "image" : "document",
        fileUrl: data.fileUrl,
        fileName: file.name,
      }

      setMessages([...messages, newMessage])
      websocketService.sendMessage(newMessage)

      // Save message to database
      await fetch("/api/messages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify(newMessage),
      })
    } catch (error) {
      console.error("[v0] Error uploading file:", error)
      throw error
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setMessageInput(e.target.value)

    if (selectedConversation) {
      // Send typing indicator
      websocketService.sendTyping(selectedConversation.user.id, true)

      // Clear previous timeout
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current)
      }

      // Stop typing after 2 seconds of inactivity
      typingTimeoutRef.current = setTimeout(() => {
        websocketService.sendTyping(selectedConversation.user.id, false)
      }, 2000)
    }
  }

  const handleImageUpload = () => {
    setUploadType("image")
    setFileDialogOpen(true)
  }

  const handleDocumentUpload = () => {
    setUploadType("document")
    setFileDialogOpen(true)
  }

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2)
  }

  if (!selectedConversation) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[var(--chat-bg)]">
        <div className="text-center space-y-3">
          <div className="h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
            <Send className="h-10 w-10 text-primary" />
          </div>
          <h3 className="text-xl font-semibold text-foreground">Selecciona una conversación</h3>
          <p className="text-muted-foreground">Elige un contacto para comenzar a chatear</p>
        </div>
      </div>
    )
  }

  const { user } = selectedConversation

  return (
    <div className="flex-1 flex flex-col bg-[var(--chat-bg)]">
      {/* Chat Header */}
      <div className="h-16 border-b border-border bg-card flex items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Avatar>
              <AvatarFallback className="bg-primary/10 text-primary">{getInitials(user.name)}</AvatarFallback>
            </Avatar>
            {user.isOnline && (
              <div className="absolute bottom-0 right-0 h-3 w-3 rounded-full bg-[var(--online-indicator)] border-2 border-card" />
            )}
          </div>
          <div>
            <h3 className="font-semibold text-card-foreground">{user.name}</h3>
            <p className="text-xs text-muted-foreground">
              {isTyping ? "Escribiendo..." : user.isOnline ? "En línea" : user.lastSeen || "Desconectado"}
            </p>
          </div>
        </div>

        <Button variant="ghost" size="icon">
          <MoreVertical className="h-5 w-5" />
        </Button>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="space-y-4 max-w-4xl mx-auto">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} isOwn={message.senderId === currentUser.id} />
          ))}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t border-border bg-card p-4">
        <div className="flex items-end gap-2 max-w-4xl mx-auto">
          <div className="flex gap-1">
            <Button variant="ghost" size="icon" title="Adjuntar archivo" onClick={handleDocumentUpload}>
              <Paperclip className="h-5 w-5" />
            </Button>
            <Button variant="ghost" size="icon" title="Enviar imagen" onClick={handleImageUpload}>
              <ImageIcon className="h-5 w-5" />
            </Button>
            <Button variant="ghost" size="icon" title="Enviar documento" onClick={handleDocumentUpload}>
              <File className="h-5 w-5" />
            </Button>
          </div>

          <div className="flex-1 relative">
            <Input
              placeholder="Escribe un mensaje..."
              value={messageInput}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              className="pr-10"
            />
            <Button variant="ghost" size="icon" className="absolute right-1 top-1/2 -translate-y-1/2" title="Emoji">
              <Smile className="h-5 w-5" />
            </Button>
          </div>

          <Button onClick={handleSendMessage} size="icon" disabled={!messageInput.trim()}>
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </div>

      {/* File Upload Dialog */}
      <FileUploadDialog
        open={fileDialogOpen}
        onOpenChange={setFileDialogOpen}
        onUpload={handleFileUpload}
        acceptedTypes={uploadType === "image" ? "image/*" : "application/pdf,.doc,.docx,.txt,.zip"}
      />
    </div>
  )
}
