"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Send, Paperclip, ImageIcon, File, Smile, MoreVertical, ArrowLeft, UserPlus } from "lucide-react"
import { MessageBubble } from "./message-bubble"
import { FileUploadDialog } from "./file-upload-dialog"
import { AddParticipantDialog } from "./add-participant-dialog"
import type { Conversation, User, Message } from "./chat-layout"
import { websocketService } from "@/lib/websocket"
import { useWebSocket } from "@/hooks/use-websocket"
import { apiClient } from "@/lib/api"
import dynamic from "next/dynamic"

// Import EmojiPicker dynamically to avoid SSR issues
const EmojiPicker = dynamic(() => import("emoji-picker-react"), { ssr: false })

type ChatWindowProps = {
  selectedConversation: Conversation | null
  currentUser: User
  onBack?: () => void
}

export function ChatWindow({ selectedConversation, currentUser, onBack }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [messageInput, setMessageInput] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const [fileDialogOpen, setFileDialogOpen] = useState(false)
  const [uploadType, setUploadType] = useState<"image" | "document">("image")
  const [emojiPickerOpen, setEmojiPickerOpen] = useState(false)
  const [addParticipantOpen, setAddParticipantOpen] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const typingTimeoutRef = useRef<NodeJS.Timeout>()

  const ws = useWebSocket((message) => {
    if (message.type === "message" && selectedConversation) {
      // Backend sends message data inside "data" property
      const msgData = message.data

      // Transform backend message to frontend format
      const newMessage: Message = {
        id: msgData?.id?.toString() || Date.now().toString(),
        content: msgData?.content || "",
        senderId: msgData?.user_id?.toString() || "",
        receiverId: selectedConversation.user.id,
        timestamp: msgData?.created_at || new Date().toISOString(),
        type: "text",
      }

      setMessages((prev) => [...prev, newMessage])
    } else if (message.type === "typing" && selectedConversation) {
      if (message.data?.senderId === selectedConversation.user.id) {
        setIsTyping(message.data.isTyping)
      }
    }
  })

  useEffect(() => {
    if (selectedConversation) {
      loadMessages(selectedConversation.user.id)

      // Get token from localStorage
      const token = localStorage.getItem("token") || "temp-token"

      // Use the conversation ID as room ID
      const roomId = selectedConversation.id

      // Connect to WebSocket for this room
      websocketService.connect(roomId, token)

      return () => {
        websocketService.disconnect()
      }
    }
  }, [selectedConversation, currentUser.id])

  const loadMessages = async (userId: string) => {
    try {
      // For now, we assume the room ID is the conversation ID
      // In a real app, you'd get the room ID from the conversation object
      const roomId = parseInt(selectedConversation?.id || "1")

      // Load latest messages from backend
      const messages = await apiClient.getLatestMessages(roomId, 50)
      // Transform backend messages to frontend format
      const transformedMessages: Message[] = messages.map((msg: any) => ({
        id: msg.id.toString(),
        content: msg.content,
        senderId: msg.user_id.toString(),
        receiverId: userId,
        timestamp: msg.created_at,
        type: "text" as const,
        isDeleted: msg.is_deleted,
      }))

      setMessages(transformedMessages)
    } catch (error) {
      console.error("Error loading messages:", error)
      setMessages([])
    }
  }

  useEffect(() => {
    // Auto-scroll al final cuando hay nuevos mensajes
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSendMessage = async () => {
    if (!messageInput.trim() || !selectedConversation) return

    const content = messageInput
    setMessageInput("")

    try {
      // Send via WebSocket only (backend will save to DB and broadcast)
      websocketService.send({
        type: "message",
        content: content,
      })
    } catch (error) {
      console.error("Error sending message:", error)
      // Restore message input on error
      setMessageInput(content)
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

  const handleKeyDown = (e: React.KeyboardEvent) => {
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

  const handleEmojiClick = (emojiData: any) => {
    // Insert emoji at cursor position
    setMessageInput((prev) => prev + emojiData.emoji)
    setEmojiPickerOpen(false)
  }

  const handleParticipantAdded = () => {
    // Optionally refresh room participants or show notification
    console.log("Participante añadido exitosamente")
  }

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

  if (!selectedConversation) {
    return (
      <div className="hidden md:flex flex-1 items-center justify-center bg-[var(--chat-bg)]">
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

  const { user, isGroup, roomName, participants } = selectedConversation
  const displayName = isGroup && roomName ? roomName : user.username
  const participantNames = isGroup && participants ? participants.map(p => p.username).join(', ') : ''

  return (
    <div className="flex-1 flex flex-col bg-[var(--chat-bg)] min-h-0">
      {/* Chat Header */}
      <div className="shrink-0 h-16 border-b border-border bg-card flex items-center justify-between px-4">
        <div className="flex items-center gap-3">
          {/* Back button - only visible on mobile */}
          {onBack && (
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={onBack}
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
          )}
          <div className="relative">
            <Avatar>
              <AvatarFallback className="bg-primary/10 text-primary">{getInitials(displayName)}</AvatarFallback>
            </Avatar>
            {!isGroup && user.isOnline && (
              <div className="absolute bottom-0 right-0 h-3 w-3 rounded-full bg-[var(--online-indicator)] border-2 border-card" />
            )}
          </div>
          <div>
            <h3 className="font-semibold text-card-foreground">{displayName}</h3>
            <p className="text-xs text-muted-foreground">
              {isGroup
                ? participantNames ? `(${participantNames})` : 'Grupo'
                : isTyping ? "Escribiendo..." : user.isOnline ? "En línea" : user.lastSeen || "Desconectado"
              }
            </p>
          </div>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreVertical className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => setAddParticipantOpen(true)}>
              <UserPlus className="h-4 w-4 mr-2" />
              Añadir participante
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 min-h-0 p-4">
        <div className="space-y-4 max-w-4xl mx-auto">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} isOwn={message.senderId === currentUser.id.toString()} />
          ))}
          {/* Elemento invisible para auto-scroll */}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="shrink-0 border-t border-border bg-card p-4">
        <div className="flex items-end gap-2 max-w-4xl mx-auto">
          <div className="flex gap-1">
            <Button variant="ghost" size="icon" title="Adjuntar archivo" onClick={handleDocumentUpload}>
              <Paperclip className="h-5 w-5" />
            </Button>
          </div>

          <div className="flex-1 relative">
            <Input
              placeholder="Escribe un mensaje..."
              value={messageInput}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              className="pr-10"
            />
            <Popover open={emojiPickerOpen} onOpenChange={setEmojiPickerOpen}>
              <PopoverTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-1 top-1/2 -translate-y-1/2"
                  title="Emoji"
                >
                  <Smile className="h-5 w-5" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-full p-0 border-0" side="top" align="end">
                <EmojiPicker onEmojiClick={handleEmojiClick} width={350} height={400} />
              </PopoverContent>
            </Popover>
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

      {/* Add Participant Dialog */}
      <AddParticipantDialog
        open={addParticipantOpen}
        onOpenChange={setAddParticipantOpen}
        roomId={selectedConversation.id}
        onParticipantAdded={handleParticipantAdded}
      />
    </div>
  )
}
