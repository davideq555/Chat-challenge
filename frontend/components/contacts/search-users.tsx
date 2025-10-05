"use client"

import { useState } from "react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Search, UserPlus, Loader2, Check } from "lucide-react"
import { apiClient } from "@/lib/api"

type User = {
  id: number
  username: string
  email: string
  is_public: boolean
}

export function SearchUsers() {
  const [query, setQuery] = useState("")
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [searching, setSearching] = useState(false)
  const [addingId, setAddingId] = useState<number | null>(null)
  const [addedIds, setAddedIds] = useState<Set<number>>(new Set())

  const handleSearch = async () => {
    if (!query.trim()) return

    try {
      setSearching(true)
      const data = await apiClient.searchPublicUsers(query)
      setUsers(data)
    } catch (error) {
      console.error("Error searching users:", error)
    } finally {
      setSearching(false)
    }
  }

  const handleAddContact = async (userId: number) => {
    try {
      setAddingId(userId)
      await apiClient.sendContactRequest(userId)
      setAddedIds(new Set([...addedIds, userId]))
    } catch (error) {
      console.error("Error adding contact:", error)
    } finally {
      setAddingId(null)
    }
  }

  const getInitials = (username: string) => {
    return username.slice(0, 2).toUpperCase()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch()
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar por nombre de usuario o email..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="pl-9"
          />
        </div>
        <Button onClick={handleSearch} disabled={searching || !query.trim()}>
          {searching ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <>
              <Search className="h-4 w-4 mr-2" />
              Buscar
            </>
          )}
        </Button>
      </div>

      {users.length > 0 && (
        <ScrollArea className="h-[400px]">
          <div className="space-y-2">
            {users.map((user) => {
              const isAdded = addedIds.has(user.id)
              return (
                <div
                  key={user.id}
                  className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-accent transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Avatar>
                      <AvatarFallback className="bg-primary/10 text-primary">
                        {getInitials(user.username)}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-semibold">{user.username}</p>
                      <p className="text-sm text-muted-foreground">{user.email}</p>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant={isAdded ? "outline" : "default"}
                    onClick={() => handleAddContact(user.id)}
                    disabled={addingId === user.id || isAdded}
                  >
                    {addingId === user.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : isAdded ? (
                      <>
                        <Check className="h-4 w-4 mr-2" />
                        Solicitud enviada
                      </>
                    ) : (
                      <>
                        <UserPlus className="h-4 w-4 mr-2" />
                        Agregar
                      </>
                    )}
                  </Button>
                </div>
              )
            })}
          </div>
        </ScrollArea>
      )}

      {users.length === 0 && !searching && query && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No se encontraron usuarios</p>
        </div>
      )}

      {!query && (
        <div className="text-center py-12">
          <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">Busca usuarios por nombre o email</p>
          <p className="text-sm text-muted-foreground mt-2">
            Solo se mostrarán usuarios públicos
          </p>
        </div>
      )}
    </div>
  )
}
