"use client"

import { useState, useEffect } from "react"
import { Search, Loader2, Users, Globe } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { apiClient } from "@/lib/api"

type NewConversationDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConversationCreated: () => void
}

type UserSearchResult = {
  id: number
  username: string
  email: string
}

type Contact = {
  id: number
  user_id: number
  contact_id: number
  status: string
  contact: {
    id: number
    username: string
    email: string
  }
}

export function NewConversationDialog({
  open,
  onOpenChange,
  onConversationCreated,
}: NewConversationDialogProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [contacts, setContacts] = useState<UserSearchResult[]>([])
  const [publicUsers, setPublicUsers] = useState<UserSearchResult[]>([])
  const [filteredContacts, setFilteredContacts] = useState<UserSearchResult[]>([])
  const [filteredPublicUsers, setFilteredPublicUsers] = useState<UserSearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    if (open) {
      loadUsers()
    }
  }, [open])

  useEffect(() => {
    const query = searchQuery.toLowerCase()

    if (searchQuery.trim() === "") {
      setFilteredContacts(contacts)
      setFilteredPublicUsers(publicUsers)
    } else {
      setFilteredContacts(
        contacts.filter(
          (user) =>
            user.username.toLowerCase().includes(query) ||
            user.email.toLowerCase().includes(query)
        )
      )
      setFilteredPublicUsers(
        publicUsers.filter(
          (user) =>
            user.username.toLowerCase().includes(query) ||
            user.email.toLowerCase().includes(query)
        )
      )
    }
  }, [searchQuery, contacts, publicUsers])

  const loadUsers = async () => {
    setLoading(true)
    try {
      // 1. Cargar contactos aceptados
      const myContacts: Contact[] = await apiClient.getMyContacts()
      const contactUsers = myContacts.map(c => ({
        id: c.contact.id,
        username: c.contact.username,
        email: c.contact.email,
      }))

      // 2. Cargar usuarios disponibles (sin conversaciones previas)
      const availableUsers = await apiClient.getAvailableUsersForChat()

      // 3. Filtrar usuarios públicos (excluir contactos ya agregados)
      const contactIds = new Set(contactUsers.map(c => c.id))
      const publicUsersFiltered = availableUsers.filter((u: UserSearchResult) => !contactIds.has(u.id))

      setContacts(contactUsers)
      setPublicUsers(publicUsersFiltered)
      setFilteredContacts(contactUsers)
      setFilteredPublicUsers(publicUsersFiltered)
    } catch (error) {
      console.error("Error loading users:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateConversation = async (user: UserSearchResult) => {
    setCreating(true)
    try {
      // Create a 1-to-1 room with the selected user
      const room = await apiClient.createChatRoom(
        `Chat with ${user.username}`,
        false // is_group = false for 1-to-1 chat
      )

      // Add the other user as participant
      await apiClient.addParticipant(room.id, user.id)

      // Close dialog and refresh conversations
      onOpenChange(false)
      onConversationCreated()
    } catch (error) {
      console.error("Error creating conversation:", error)
      alert("Error al crear la conversación. Por favor intenta de nuevo.")
    } finally {
      setCreating(false)
    }
  }

  const getInitials = (username: string) => {
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

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Nueva Conversación</DialogTitle>
          <DialogDescription>
            Busca un usuario para empezar a chatear
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Search Input */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar por nombre o email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>

          {/* Users List */}
          <ScrollArea className="h-[400px] pr-4">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <div className="space-y-4">
                {/* Contactos */}
                {filteredContacts.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-3 px-1">
                      <Users className="h-4 w-4 text-primary" />
                      <h3 className="text-sm font-semibold text-foreground">Mis Contactos</h3>
                      <span className="text-xs text-muted-foreground">({filteredContacts.length})</span>
                    </div>
                    <div className="space-y-2">
                      {filteredContacts.map((user) => (
                        <div
                          key={`contact-${user.id}`}
                          className="flex items-center gap-3 p-3 rounded-lg hover:bg-accent transition-colors"
                        >
                          <Avatar className="h-10 w-10">
                            <AvatarFallback className="bg-primary/10 text-primary">
                              {getInitials(user.username)}
                            </AvatarFallback>
                          </Avatar>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">{user.username}</p>
                            <p className="text-sm text-muted-foreground truncate">{user.email}</p>
                          </div>
                          <Button
                            size="sm"
                            onClick={() => handleCreateConversation(user)}
                            disabled={creating}
                          >
                            {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : "Chatear"}
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Usuarios Públicos */}
                {filteredPublicUsers.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-3 px-1">
                      <Globe className="h-4 w-4 text-muted-foreground" />
                      <h3 className="text-sm font-semibold text-foreground">Otros Usuarios</h3>
                      <span className="text-xs text-muted-foreground">({filteredPublicUsers.length})</span>
                    </div>
                    <div className="space-y-2">
                      {filteredPublicUsers.map((user) => (
                        <div
                          key={`public-${user.id}`}
                          className="flex items-center gap-3 p-3 rounded-lg hover:bg-accent transition-colors"
                        >
                          <Avatar className="h-10 w-10">
                            <AvatarFallback className="bg-muted text-muted-foreground">
                              {getInitials(user.username)}
                            </AvatarFallback>
                          </Avatar>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">{user.username}</p>
                            <p className="text-sm text-muted-foreground truncate">{user.email}</p>
                          </div>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleCreateConversation(user)}
                            disabled={creating}
                          >
                            {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : "Chatear"}
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Empty state */}
                {filteredContacts.length === 0 && filteredPublicUsers.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground text-sm">
                    {searchQuery ? "No se encontraron usuarios" : "No hay usuarios disponibles"}
                  </div>
                )}
              </div>
            )}
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  )
}
