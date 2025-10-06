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
import { Send, Paperclip, ImageIcon, File, Smile, MoreVertical, ArrowLeft, UserPlus, Edit, Trash2 } from "lucide-react"
import { MessageBubble } from "./message-bubble"
import { FileUploadDialog } from "./file-upload-dialog"
import { AddParticipantDialog } from "./add-participant-dialog"
import { ConfirmDialog } from "@/components/ui/confirm-dialog"
import type { Conversation, User, Message } from "./chat-layout"
import { websocketService } from "@/lib/websocket"
import { useWebSocket } from "@/hooks/use-websocket"
import { apiClient } from "@/lib/api"
import * as FerruccEmoji from "@ferrucc-io/emoji-picker"

// Use direct import of the library to measure baseline performance in dev/prod.
// Normalize the export (some builds export named EmojiPicker, some default).
const EmojiPicker: any = (FerruccEmoji as any).EmojiPicker || (FerruccEmoji as any).default || FerruccEmoji

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
  // No preload: using direct import to measure raw performance
  const [addParticipantOpen, setAddParticipantOpen] = useState(false)
  const [editingMessage, setEditingMessage] = useState<{id: string, content: string} | null>(null)
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
  const [messageToDelete, setMessageToDelete] = useState<string | null>(null)
  const [deleteChatConfirmOpen, setDeleteChatConfirmOpen] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const ws = useWebSocket((message) => {
    if (message.type === "message" && selectedConversation) {
      // Backend sends message data inside "data" property
      const msgData = message.data

      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

      // Determinar tipo de mensaje basado en adjuntos
      let messageType: "text" | "image" | "document" = "text"
      let fileUrl: string | undefined
      let fileName: string | undefined

      if (msgData?.attachments && msgData.attachments.length > 0) {
        const attachment = msgData.attachments[0]
        // Construir URL completa
        fileUrl = attachment.file_url.startsWith('http')
          ? attachment.file_url
          : `${API_URL}${attachment.file_url}`
        messageType = attachment.file_type === "image" ? "image" : "document"
        fileName = fileUrl.split('/').pop() || 'file'
      }

      // Transform backend message to frontend format
      const newMessage: Message = {
        id: msgData?.id?.toString() || Date.now().toString(),
        content: msgData?.content || "",
        senderId: msgData?.user_id?.toString() || "",
        receiverId: selectedConversation.user.id,
        timestamp: msgData?.created_at || new Date().toISOString(),
        type: messageType,
        fileUrl,
        fileName,
      }

      // Evitar duplicados: verificar si ya existe un mensaje con mismo contenido y sender reciente
      setMessages((prev) => {
        const isDuplicate = prev.some(msg =>
          msg.content === newMessage.content &&
          msg.senderId === newMessage.senderId &&
          Math.abs(new Date(msg.timestamp).getTime() - new Date(newMessage.timestamp).getTime()) < 5000
        )

        if (isDuplicate) {
          // Reemplazar mensaje temporal con el mensaje real del backend
          return prev.map(msg =>
            msg.id.startsWith('temp-') && msg.content === newMessage.content && msg.senderId === newMessage.senderId
              ? newMessage
              : msg
          )
        }

        return [...prev, newMessage]
      })
    } else if (message.type === "message_updated" && selectedConversation) {
      // Actualizar mensaje editado en tiempo real
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === message.messageId
            ? { ...msg, content: message.content || msg.content }
            : msg
        )
      )
    } else if (message.type === "message_deleted" && selectedConversation) {
      // Remover mensaje eliminado en tiempo real
      setMessages((prev) => prev.filter((msg) => msg.id !== message.messageId))
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

      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

      // Transform backend messages to frontend format
      const transformedMessages: Message[] = messages.map((msg: any) => {
        // Determinar tipo de mensaje basado en adjuntos
        let messageType: "text" | "image" | "document" = "text"
        let fileUrl: string | undefined
        let fileName: string | undefined

        if (msg.attachments && msg.attachments.length > 0) {
          const attachment = msg.attachments[0]
          // Construir URL completa
          fileUrl = attachment.file_url.startsWith('http')
            ? attachment.file_url
            : `${API_URL}${attachment.file_url}`
          messageType = attachment.file_type === "image" ? "image" : "document"
          // Extraer nombre del archivo de la URL si es posible
          fileName = fileUrl.split('/').pop() || 'file'
        }

        return {
          id: msg.id.toString(),
          content: msg.content,
          senderId: msg.user_id.toString(),
          receiverId: userId,
          timestamp: msg.created_at,
          type: messageType,
          isDeleted: msg.is_deleted,
          fileUrl,
          fileName,
        }
      })

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

    const content = messageInput.trim()

    // Modo edición
    if (editingMessage) {
      try {
        const response = await apiClient.updateMessage(parseInt(editingMessage.id), content)

        // Actualizar mensaje en la UI local
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === editingMessage.id
              ? { ...msg, content: response.content, timestamp: response.updated_at || msg.timestamp }
              : msg
          )
        )

        // Limpiar estado de edición
        setEditingMessage(null)
        setMessageInput("")

        // Notificar via WebSocket
        websocketService.send({
          type: "message_updated",
          messageId: editingMessage.id,
          content: content,
        })
      } catch (error) {
        console.error("Error editing message:", error)
        alert("Error al editar el mensaje")
      }
      return
    }

    // Modo envío normal
    setMessageInput("")

    // Optimistic update: agregar mensaje localmente inmediatamente
    const optimisticMessage: Message = {
      id: `temp-${Date.now()}`,
      content: content,
      senderId: currentUser.id.toString(),
      receiverId: selectedConversation.user.id,
      roomId: selectedConversation.id,
      timestamp: new Date().toISOString(),
      type: "text",
    }

    setMessages((prev) => [...prev, optimisticMessage])

    try {
      // Send via WebSocket (backend will save to DB and broadcast)
      websocketService.send({
        type: "message",
        content: content,
      })
    } catch (error) {
      console.error("Error sending message:", error)
      // Remover mensaje optimista y restaurar input
      setMessages((prev) => prev.filter(m => m.id !== optimisticMessage.id))
      setMessageInput(content)
    }
  }

  const handleFileUpload = async (file: File, caption: string) => {
    if (!selectedConversation) return

    try {
      // 1. Subir archivo al servidor
      const uploadResponse = await apiClient.uploadFile(file)

      // 2. Usar caption o "Adjunto" por defecto si está vacío
      const messageContent = caption.trim() || "Adjunto"

      // 3. Enviar mensaje con adjunto al backend
      const roomId = parseInt(selectedConversation.id)
      const response = await apiClient.sendMessage(roomId, messageContent, [
        {
          file_url: uploadResponse.file_url,
          file_type: uploadResponse.file_type,
        },
      ])

      // 4. Construir URL completa del archivo
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const fullFileUrl = uploadResponse.file_url.startsWith('http')
        ? uploadResponse.file_url
        : `${API_URL}${uploadResponse.file_url}`

      // 5. Agregar mensaje a la UI local (con datos del backend)
      const newMessage: Message = {
        id: response.id.toString(),
        content: response.content,
        senderId: response.user_id.toString(),
        receiverId: selectedConversation.user.id,
        timestamp: response.created_at,
        type: uploadResponse.file_type === "image" ? "image" : "document",
        fileUrl: fullFileUrl,
        fileName: file.name,
      }

      setMessages((prev) => [...prev, newMessage])

      // 6. Enviar por WebSocket para notificar a otros usuarios
      websocketService.send({
        type: "message",
        content: messageContent,
      })
    } catch (error) {
      console.error("Error uploading file:", error)
      throw error
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    } else if (e.key === "Escape" && editingMessage) {
      e.preventDefault()
      handleCancelEdit()
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

  const handleEmojiSelect = (payload: any) => {
    // @ferrucc-io/emoji-picker may pass either a string or an object. Normalize.
    const emoji = typeof payload === "string" ? payload : payload?.emoji || ""
    if (emoji) {
      setMessageInput((prev) => prev + emoji)
      setEmojiPickerOpen(false)
    }
  }

  const handleParticipantAdded = () => {
    // Optionally refresh room participants or show notification
    console.log("Participante añadido exitosamente")
  }

  const handleDeleteChatClick = () => {
    // Solo permitir eliminar chats NO grupales
    if (selectedConversation?.isGroup) {
      alert("No se pueden eliminar chats grupales por el momento")
      return
    }
    setDeleteChatConfirmOpen(true)
  }

  const confirmDeleteChat = async () => {
    if (!selectedConversation) return

    try {
      const token = localStorage.getItem('token')
      console.log("Token present:", !!token)
      console.log("Attempting to delete chat room:", selectedConversation.id)
      console.log("Room ID type:", typeof selectedConversation.id)

      await apiClient.deleteChatRoom(parseInt(selectedConversation.id))

      console.log("Chat eliminado exitosamente")

      // Redirigir o cerrar chat (llamar a onBack si existe)
      if (onBack) {
        onBack()
      }
    } catch (error: any) {
      console.error("Error deleting chat:", error)
      console.error("Error details:", {
        message: error.message,
        stack: error.stack,
        name: error.name,
      })

      // Mostrar mensaje más descriptivo
      let errorMessage = "Error desconocido"
      if (error.message) {
        errorMessage = error.message
      } else if (error.toString().includes("NetworkError")) {
        errorMessage = "Error de red. Verifica tu conexión o que el servidor esté corriendo."
      }

      alert(`Error al eliminar la conversación: ${errorMessage}`)
    }
  }

  const handleEditMessage = (messageId: string, content: string) => {
    // Poner el mensaje en modo edición (estilo WhatsApp)
    setEditingMessage({ id: messageId, content })
    setMessageInput(content)
  }

  const handleCancelEdit = () => {
    setEditingMessage(null)
    setMessageInput("")
  }

  const handleDeleteMessage = (messageId: string) => {
    // Abrir modal de confirmación
    setMessageToDelete(messageId)
    setDeleteConfirmOpen(true)
  }

  const confirmDeleteMessage = async () => {
    if (!messageToDelete) return

    try {
      await apiClient.deleteMessage(parseInt(messageToDelete), false) // soft delete por defecto

      // Remover mensaje de la UI local (o marcarlo como eliminado)
      setMessages((prev) => prev.filter((msg) => msg.id !== messageToDelete))

      // Notificar via WebSocket
      websocketService.send({
        type: "message_deleted",
        messageId: messageToDelete,
      })
    } catch (error) {
      console.error("Error deleting message:", error)
      alert("Error al eliminar el mensaje")
    } finally {
      setMessageToDelete(null)
    }
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
            <DropdownMenuItem
              onClick={handleDeleteChatClick}
              disabled={isGroup}
              className="text-destructive focus:text-destructive"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Eliminar conversación
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 min-h-0 p-4">
        <div className="space-y-4 max-w-4xl mx-auto">
          {messages.map((message) => {
            // Buscar el nombre del usuario que envió el mensaje
            const sender = participants?.find(p => p.id === message.senderId)
            const senderName = sender ? sender.username : user.username

            return (
              <MessageBubble
                key={message.id}
                message={message}
                isOwn={message.senderId === currentUser.id.toString()}
                isGroup={isGroup}
                senderName={senderName}
                onEdit={handleEditMessage}
                onDelete={handleDeleteMessage}
              />
            )
          })}
          {/* Elemento invisible para auto-scroll */}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="shrink-0 border-t border-border bg-card">
        {/* Barra de edición */}
        {editingMessage && (
          <div className="flex items-center justify-between px-4 py-2 bg-primary/10 border-b border-border">
            <div className="flex items-center gap-2">
              <Edit className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium">Editando mensaje</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCancelEdit}
              className="h-8"
            >
              Cancelar
            </Button>
          </div>
        )}

        <div className="p-4">
          <div className="flex items-end gap-2 max-w-4xl mx-auto">
            <div className="flex gap-1">
              <Button variant="ghost" size="icon" title="Adjuntar archivo" onClick={handleDocumentUpload} disabled={!!editingMessage}>
                <Paperclip className="h-5 w-5" />
              </Button>
            </div>

            <div className="flex-1 relative">
              <Input
                placeholder={editingMessage ? "Editar mensaje..." : "Escribe un mensaje..."}
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
                <div className="emoji-picker-wrapper">
                  <EmojiPicker
                    className="border border-zinc-200 dark:border-zinc-800 rounded-lg"
                    emojisPerRow={10}
                    emojiSize={24}
                    onEmojiSelect={handleEmojiSelect}
                  >
                    <EmojiPicker.Header className="p-2 pb-0">
                      <EmojiPicker.Input
                        placeholder="Buscar emoji"
                        autoFocus={true}
                        hideIcon
                        className="focus:ring-2 focus:ring-inset ring-1 ring-transparent"
                      />
                    </EmojiPicker.Header>
                    <EmojiPicker.Group>
                      <EmojiPicker.List hideStickyHeader={true} containerHeight={400} />
                    </EmojiPicker.Group>
                  </EmojiPicker>
                </div>
            </PopoverContent>
            </Popover>
          </div>

          <Button onClick={handleSendMessage} size="icon" disabled={!messageInput.trim()}>
            <Send className="h-5 w-5" />
          </Button>
          </div>
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

      {/* Delete Message Confirmation Dialog */}
      <ConfirmDialog
        open={deleteConfirmOpen}
        onOpenChange={setDeleteConfirmOpen}
        onConfirm={confirmDeleteMessage}
        title="Eliminar mensaje"
        description="¿Estás seguro de que quieres eliminar este mensaje? Esta acción no se puede deshacer."
        confirmText="Eliminar"
        cancelText="Cancelar"
        variant="destructive"
      />

      {/* Delete Chat Confirmation Dialog */}
      <ConfirmDialog
        open={deleteChatConfirmOpen}
        onOpenChange={setDeleteChatConfirmOpen}
        onConfirm={confirmDeleteChat}
        title="Eliminar conversación"
        description="¿Estás seguro de que quieres eliminar esta conversación? Se eliminarán todos los mensajes y no se puede deshacer."
        confirmText="Eliminar"
        cancelText="Cancelar"
        variant="destructive"
      />
    </div>
  )
}
