"use client"

import { useState, useEffect } from "react"
import { Search, Loader2, UserPlus } from "lucide-react"
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

type AddParticipantDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  roomId: string
  onParticipantAdded: () => void
}

type UserSearchResult = {
  id: number
  username: string
  email: string
}

export function AddParticipantDialog({
  open,
  onOpenChange,
  roomId,
  onParticipantAdded,
}: AddParticipantDialogProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [users, setUsers] = useState<UserSearchResult[]>([])
  const [filteredUsers, setFilteredUsers] = useState<UserSearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [adding, setAdding] = useState(false)

  useEffect(() => {
    if (open) {
      loadUsers()
    }
  }, [open, roomId])

  useEffect(() => {
    if (searchQuery.trim() === "") {
      setFilteredUsers(users)
    } else {
      const query = searchQuery.toLowerCase()
      setFilteredUsers(
        users.filter(
          (user) =>
            user.username.toLowerCase().includes(query) ||
            user.email.toLowerCase().includes(query)
        )
      )
    }
  }, [searchQuery, users])

  const loadUsers = async () => {
    setLoading(true)
    try {
      const availableUsers = await apiClient.getAvailableUsersForRoom(parseInt(roomId))
      setUsers(availableUsers)
      setFilteredUsers(availableUsers)
    } catch (error) {
      console.error("Error loading users:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleAddParticipant = async (user: UserSearchResult) => {
    setAdding(true)
    try {
      await apiClient.addParticipant(parseInt(roomId), user.id)

      // Close dialog and refresh
      onOpenChange(false)
      onParticipantAdded()
    } catch (error) {
      console.error("Error adding participant:", error)
      alert("Error al añadir participante. Por favor intenta de nuevo.")
    } finally {
      setAdding(false)
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
          <DialogTitle>Añadir Participante</DialogTitle>
          <DialogDescription>
            Busca un usuario para añadirlo a esta conversación
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
          <ScrollArea className="h-[300px] pr-4">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : filteredUsers.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground text-sm">
                {searchQuery
                  ? "No se encontraron usuarios"
                  : "Todos los usuarios ya son participantes"}
              </div>
            ) : (
              <div className="space-y-2">
                {filteredUsers.map((user) => (
                  <div
                    key={user.id}
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
                      onClick={() => handleAddParticipant(user)}
                      disabled={adding}
                    >
                      {adding ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <>
                          <UserPlus className="h-4 w-4 mr-1" />
                          Añadir
                        </>
                      )}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  )
}
