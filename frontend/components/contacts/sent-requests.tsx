"use client"

import { useState, useEffect } from "react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { X, Loader2, Clock } from "lucide-react"
import { apiClient } from "@/lib/api"

type SentRequest = {
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

export function SentRequests() {
  const [requests, setRequests] = useState<SentRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [cancelingId, setCancelingId] = useState<number | null>(null)

  const loadRequests = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getSentRequests()
      console.log("Sent requests data:", data)
      setRequests(data)
    } catch (error) {
      console.error("Error loading sent requests:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRequests()
  }, [])

  const handleCancel = async (requestId: number) => {
    try {
      setCancelingId(requestId)
      await apiClient.deleteContact(requestId)
      setRequests(requests.filter(r => r.id !== requestId))
    } catch (error) {
      console.error("Error canceling request:", error)
    } finally {
      setCancelingId(null)
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

  if (requests.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No tienes solicitudes enviadas pendientes</p>
      </div>
    )
  }

  return (
    <ScrollArea className="h-[500px]">
      <div className="space-y-2">
        {requests.map((request) => (
          <div
            key={request.id}
            className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-accent transition-colors"
          >
            <div className="flex items-center gap-3">
              <Avatar>
                <AvatarFallback className="bg-primary/10 text-primary">
                  {getInitials(request.contact.username)}
                </AvatarFallback>
              </Avatar>
              <div>
                <p className="font-semibold">{request.contact.username}</p>
                <p className="text-sm text-muted-foreground">{request.contact.email}</p>
                <div className="flex items-center gap-1 mt-1">
                  <Clock className="h-3 w-3 text-amber-500" />
                  <span className="text-xs text-amber-500">Pendiente de aceptación</span>
                </div>
              </div>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleCancel(request.id)}
              disabled={cancelingId === request.id}
            >
              {cancelingId === request.id ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <X className="h-4 w-4 mr-2" />
                  Cancelar
                </>
              )}
            </Button>
          </div>
        ))}
      </div>
    </ScrollArea>
  )
}
