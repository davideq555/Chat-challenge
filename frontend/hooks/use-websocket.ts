"use client"

import { useEffect, useRef } from "react"
import { websocketService } from "@/lib/websocket"

type WebSocketMessage = {
  type: "message" | "typing" | "online" | "offline" | "join_room" | "leave_room"
  data: any
}

export function useWebSocket(onMessage: (message: WebSocketMessage) => void) {
  const onMessageRef = useRef(onMessage)

  useEffect(() => {
    onMessageRef.current = onMessage
  }, [onMessage])

  useEffect(() => {
    const unsubscribe = websocketService.subscribe((message) => {
      onMessageRef.current(message)
    })

    return () => {
      unsubscribe()
    }
  }, [])

  return websocketService
}
