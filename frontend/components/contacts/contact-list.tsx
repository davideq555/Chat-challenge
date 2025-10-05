"use client"

import { useState, useEffect } from "react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Trash2, MessageCircle, Loader2 } from "lucide-react"
import { apiClient } from "@/lib/api"
import { useRouter } from "next/navigation"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"

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

export function ContactList() {
  const router = useRouter()
  const [contacts, setContacts] = useState<Contact[]>([])
  const [loading, setLoading] = useState(true)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const loadContacts = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getMyContacts()
      setContacts(data)
    } catch (error) {
      console.error("Error loading contacts:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadContacts()
  }, [])

  const handleDelete = async (contactId: number) => {
    try {
      setDeletingId(contactId)
      await apiClient.deleteContact(contactId)
      setContacts(contacts.filter(c => c.id !== contactId))
    } catch (error) {
      console.error("Error deleting contact:", error)
    } finally {
      setDeletingId(null)
    }
  }

  const handleStartChat = (contactUserId: number) => {
    // Navigate to chat page - will need to create or find existing room
    router.push("/chat")
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

  if (contacts.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No tienes contactos aún</p>
        <p className="text-sm text-muted-foreground mt-2">
          Ve a la pestaña "Buscar" para agregar contactos
        </p>
      </div>
    )
  }

  return (
    <ScrollArea className="h-[500px]">
      <div className="space-y-2">
        {contacts.map((contact) => (
          <div
            key={contact.id}
            className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-accent transition-colors"
          >
            <div className="flex items-center gap-3">
              <Avatar>
                <AvatarFallback className="bg-primary/10 text-primary">
                  {getInitials(contact.contact.username)}
                </AvatarFallback>
              </Avatar>
              <div>
                <p className="font-semibold">{contact.contact.username}</p>
                <p className="text-sm text-muted-foreground">{contact.contact.email}</p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleStartChat(contact.contact.id)}
              >
                <MessageCircle className="h-4 w-4 mr-2" />
                Chatear
              </Button>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={deletingId === contact.id}
                  >
                    {deletingId === contact.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>¿Eliminar contacto?</AlertDialogTitle>
                    <AlertDialogDescription>
                      ¿Estás seguro de eliminar a {contact.contact.username} de tus contactos?
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancelar</AlertDialogCancel>
                    <AlertDialogAction onClick={() => handleDelete(contact.id)}>
                      Eliminar
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </div>
        ))}
      </div>
    </ScrollArea>
  )
}
