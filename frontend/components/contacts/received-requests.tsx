"use client"

import { useState, useEffect } from "react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Check, X, Loader2, Ban } from "lucide-react"
import { apiClient } from "@/lib/api"

type PendingRequest = {
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

export function ReceivedRequests() {
  const [requests, setRequests] = useState<PendingRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [processingId, setProcessingId] = useState<number | null>(null)

  const loadRequests = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getPendingRequests()
      console.log("Received requests data:", data)
      setRequests(data)
    } catch (error) {
      console.error("Error loading received requests:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRequests()
  }, [])

  const handleAccept = async (requestId: number) => {
    try {
      setProcessingId(requestId)
      await apiClient.updateContactStatus(requestId, "accepted")
      setRequests(requests.filter(r => r.id !== requestId))
    } catch (error) {
      console.error("Error accepting request:", error)
    } finally {
      setProcessingId(null)
    }
  }

  const handleBlock = async (requestId: number) => {
    try {
      setProcessingId(requestId)
      await apiClient.updateContactStatus(requestId, "blocked")
      setRequests(requests.filter(r => r.id !== requestId))
    } catch (error) {
      console.error("Error blocking request:", error)
    } finally {
      setProcessingId(null)
    }
  }

  const handleReject = async (requestId: number) => {
    try {
      setProcessingId(requestId)
      await apiClient.deleteContact(requestId)
      setRequests(requests.filter(r => r.id !== requestId))
    } catch (error) {
      console.error("Error rejecting request:", error)
    } finally {
      setProcessingId(null)
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
        <p className="text-muted-foreground">No tienes solicitudes recibidas</p>
      </div>
    )
  }

  return (
    <ScrollArea className="h-[450px]">
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
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="default"
                onClick={() => handleAccept(request.id)}
                disabled={processingId === request.id}
              >
                {processingId === request.id ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <Check className="h-4 w-4 mr-2" />
                    Aceptar
                  </>
                )}
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleReject(request.id)}
                disabled={processingId === request.id}
              >
                <X className="h-4 w-4 mr-2" />
                Rechazar
              </Button>
              <Button
                size="sm"
                variant="destructive"
                onClick={() => handleBlock(request.id)}
                disabled={processingId === request.id}
              >
                <Ban className="h-4 w-4 mr-2" />
                Bloquear
              </Button>
            </div>
          </div>
        ))}
      </div>
    </ScrollArea>
  )
}
