"use client"

import { useState, useEffect } from "react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Loader2, Unlock } from "lucide-react"
import { apiClient } from "@/lib/api"

type BlockedContact = {
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

export function BlockedContacts() {
  const [blockedContacts, setBlockedContacts] = useState<BlockedContact[]>([])
  const [loading, setLoading] = useState(true)
  const [unblockingId, setUnblockingId] = useState<number | null>(null)

  const loadBlockedContacts = async () => {
    try {
      setLoading(true)
      // Por ahora, getMyContacts devuelve solo accepted
      // Necesitamos un endpoint específico o filtrar aquí
      // Para simplificar, vamos a dejar vacío hasta que el backend lo soporte
      setBlockedContacts([])
    } catch (error) {
      console.error("Error loading blocked contacts:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadBlockedContacts()
  }, [])

  const handleUnblock = async (contactId: number) => {
    try {
      setUnblockingId(contactId)
      await apiClient.deleteContact(contactId)
      setBlockedContacts(blockedContacts.filter(c => c.id !== contactId))
    } catch (error) {
      console.error("Error unblocking contact:", error)
    } finally {
      setUnblockingId(null)
    }
  }

  const getInitials = (username: string) => {
    return username.slice(0, 2).toUpperCase()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (blockedContacts.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No tienes contactos bloqueados</p>
      </div>
    )
  }

  return (
    <ScrollArea className="h-[500px]">
      <div className="space-y-2">
        {blockedContacts.map((contact) => (
          <div
            key={contact.id}
            className="flex items-center justify-between p-4 rounded-lg border border-border bg-destructive/5"
          >
            <div className="flex items-center gap-3">
              <Avatar>
                <AvatarFallback className="bg-destructive/10 text-destructive">
                  {getInitials(contact.contact.username)}
                </AvatarFallback>
              </Avatar>
              <div>
                <p className="font-semibold">{contact.contact.username}</p>
                <p className="text-sm text-muted-foreground">{contact.contact.email}</p>
              </div>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleUnblock(contact.id)}
              disabled={unblockingId === contact.id}
            >
              {unblockingId === contact.id ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Unlock className="h-4 w-4 mr-2" />
                  Desbloquear
                </>
              )}
            </Button>
          </div>
        ))}
      </div>
    </ScrollArea>
  )
}
