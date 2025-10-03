"use client"

type WebSocketMessage = {
  type: "message" | "typing" | "online" | "offline" | "join_room" | "leave_room"
  data: any
}

type WebSocketCallback = (message: WebSocketMessage) => void

class WebSocketService {
  private ws: WebSocket | null = null
  private callbacks: Set<WebSocketCallback> = new Set()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 3000
  private url = ""
  private token = ""

  connect(url: string, token: string) {
    this.url = url
    this.token = token

    try {
      // Conectar al WebSocket del backend
      this.ws = new WebSocket(`${url}?token=${token}`)

      this.ws.onopen = () => {
        console.log("[v0] WebSocket connected")
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          console.log("[v0] WebSocket message received:", message)
          this.callbacks.forEach((callback) => callback(message))
        } catch (error) {
          console.error("[v0] Error parsing WebSocket message:", error)
        }
      }

      this.ws.onerror = (error) => {
        console.error("[v0] WebSocket error:", error)
      }

      this.ws.onclose = () => {
        console.log("[v0] WebSocket disconnected")
        this.handleReconnect()
      }
    } catch (error) {
      console.error("[v0] Error connecting to WebSocket:", error)
    }
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`[v0] Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
      setTimeout(() => {
        this.connect(this.url, this.token)
      }, this.reconnectDelay)
    } else {
      console.error("[v0] Max reconnection attempts reached")
    }
  }

  send(message: WebSocketMessage) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
      console.log("[v0] WebSocket message sent:", message)
    } else {
      console.error("[v0] WebSocket is not connected")
    }
  }

  subscribe(callback: WebSocketCallback) {
    this.callbacks.add(callback)
    return () => {
      this.callbacks.delete(callback)
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.callbacks.clear()
  }

  joinRoom(roomId: string) {
    this.send({
      type: "join_room",
      data: { roomId },
    })
  }

  leaveRoom(roomId: string) {
    this.send({
      type: "leave_room",
      data: { roomId },
    })
  }

  sendMessage(message: any) {
    this.send({
      type: "message",
      data: message,
    })
  }

  sendTyping(receiverId: string, isTyping: boolean) {
    this.send({
      type: "typing",
      data: { receiverId, isTyping },
    })
  }
}

export const websocketService = new WebSocketService()
