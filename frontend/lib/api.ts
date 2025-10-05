const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('token')
    }
    return null
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken()
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Error desconocido' }))
      throw new Error(error.message || `HTTP ${response.status}`)
    }

    return response.json()
  }

  // Users
  async login(email: string, password: string) {
    // Backend acepta email o username en el campo 'username'
    const response = await this.request<{
      access_token: string
      token_type: string
      user: any
    }>('/users/login', {
      method: 'POST',
      body: JSON.stringify({ username: email, password }),
    })

    // Guardar token JWT en localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', response.access_token)
      localStorage.setItem('user', JSON.stringify(response.user))
    }

    return { user: response.user, token: response.access_token }
  }

  async register(username: string, email: string, password: string) {
    return this.request<any>('/users/', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    })
  }

  logout() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }

  getStoredUser(): any | null {
    if (typeof window !== 'undefined') {
      const userStr = localStorage.getItem('user')
      return userStr ? JSON.parse(userStr) : null
    }
    return null
  }

  async getUser(userId: number) {
    return this.request<any>(`/users/${userId}`)
  }

  async getUsers() {
    return this.request<any[]>('/users/')
  }

  // Chat Rooms
  async getChatRooms(userId: number) {
    return this.request<any[]>(`/chat-rooms/my-rooms/${userId}`)
  }

  async getChatRoom(roomId: number, userId: number) {
    return this.request<any>(`/chat-rooms/${roomId}?user_id=${userId}`)
  }

  async createChatRoom(creatorId: number, name: string, isGroup: boolean = false) {
    return this.request<any>(`/chat-rooms/?creator_id=${creatorId}`, {
      method: 'POST',
      body: JSON.stringify({ name, is_group: isGroup }),
    })
  }

  // Room Participants
  async addParticipant(roomId: number, userId: number) {
    return this.request<any>(`/chat-rooms/${roomId}/participants?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    })
  }

  async getRoomParticipants(roomId: number) {
    return this.request<any[]>(`/chat-rooms/${roomId}/participants`)
  }

  // Messages
  async getMessages(roomId: number, requestingUserId: number) {
    return this.request<any[]>(`/messages/?requesting_user_id=${requestingUserId}&room_id=${roomId}`)
  }

  async getLatestMessages(roomId: number, requestingUserId: number, limit: number = 50) {
    return this.request<any[]>(`/messages/room/${roomId}/latest?requesting_user_id=${requestingUserId}&limit=${limit}`)
  }

  async sendMessage(roomId: number, userId: number, content: string) {
    return this.request<any>('/messages/', {
      method: 'POST',
      body: JSON.stringify({ room_id: roomId, user_id: userId, content }),
    })
  }

  async deleteMessage(messageId: number, requestingUserId: number, hard: boolean = false) {
    return this.request<any>(`/messages/${messageId}?requesting_user_id=${requestingUserId}${hard ? '&hard=true' : ''}`, {
      method: 'DELETE',
    })
  }

  // Attachments
  async uploadAttachment(messageId: number, fileUrl: string, fileName: string, fileType: string, fileSize: number) {
    return this.request<any>('/attachments/', {
      method: 'POST',
      body: JSON.stringify({ message_id: messageId, file_url: fileUrl, file_name: fileName, file_type: fileType, file_size: fileSize }),
    })
  }

  async getAttachments(messageId: number) {
    return this.request<any[]>(`/attachments/message/${messageId}/all`)
  }

  // Load conversations with participants and last messages
  async loadUserConversations(userId: number) {
    try {
      // Get user's rooms
      const rooms = await this.getChatRooms(userId)

      // For each room, get participants and latest message
      const conversations = await Promise.all(
        rooms.map(async (room: any) => {
          const [participants, messages] = await Promise.all([
            this.getRoomParticipants(room.id),
            this.getLatestMessages(room.id, userId, 1).catch(() => [])
          ])

          // Find the other participant (not the current user)
          const otherParticipantData = participants.find((p: any) => p.user_id !== userId)

          // If there's another participant, get their full user data
          let otherParticipant = null
          if (otherParticipantData) {
            const userData = await this.getUser(otherParticipantData.user_id)
            otherParticipant = {
              ...otherParticipantData,
              user: userData
            }
          }

          return {
            room,
            participants,
            otherParticipant,
            lastMessage: messages.length > 0 ? messages[0] : null
          }
        })
      )

      return conversations
    } catch (error) {
      console.error('Error loading conversations:', error)
      throw error
    }
  }
}

export const apiClient = new ApiClient(API_URL)
