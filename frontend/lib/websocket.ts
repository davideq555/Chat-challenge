"use client"

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'

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
  private roomId: string = ""
  private token: string = ""

  connect(roomId: string, token: string = "temp-token") {
    this.roomId = roomId
    this.token = token

    try {
      // Connect to WebSocket backend using room_id in path
      const wsUrl = `${WS_URL}/ws/${roomId}?token=${token}`
      console.log("Connecting to WebSocket:", wsUrl)

      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log("WebSocket connected to room:", roomId)
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          console.log("WebSocket message received:", message)
          this.callbacks.forEach((callback) => callback(message))
        } catch (error) {
          console.error("Error parsing WebSocket message:", error)
        }
      }

      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error)
      }

      this.ws.onclose = () => {
        console.log("WebSocket disconnected")
        this.handleReconnect()
      }
    } catch (error) {
      console.error("Error connecting to WebSocket:", error)
    }
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
      setTimeout(() => {
        this.connect(this.roomId, this.token)
      }, this.reconnectDelay)
    } else {
      console.error("Max reconnection attempts reached")
    }
  }

  send(message: WebSocketMessage) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
      console.log("WebSocket message sent:", message)
    } else {
      console.error("WebSocket is not connected")
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
