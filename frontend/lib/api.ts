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

    // 204 No Content no tiene cuerpo para parsear
    if (response.status === 204) {
      return undefined as T
    }

    return response.json()
  }

  // Users
  async login(email: string, password: string) {
    // Login NO requiere token, así que usamos fetch directamente
    const response = await fetch(`${this.baseUrl}/users/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username: email, password }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    const data = await response.json()

    // Guardar token JWT en localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
    }

    return { user: data.user, token: data.access_token }
  }

  async register(username: string, email: string, password: string) {
    // Register NO requiere token, así que usamos fetch directamente
    const response = await fetch(`${this.baseUrl}/users/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, email, password }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
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

  async updateUser(userId: number, data: { password?: string; is_public?: boolean }) {
    return this.request<any>(`/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async getAvailableUsersForChat() {
    return this.request<any[]>('/users/available-for-chat')
  }

  async getAvailableUsersForRoom(roomId: number) {
    return this.request<any[]>(`/users/available-for-room/${roomId}`)
  }

  // Chat Rooms
  async getChatRooms() {
    return this.request<any[]>('/chat-rooms/my-rooms')
  }

  async getChatRoom(roomId: number) {
    return this.request<any>(`/chat-rooms/${roomId}`)
  }

  async createChatRoom(name: string, isGroup: boolean = false) {
    return this.request<any>('/chat-rooms/', {
      method: 'POST',
      body: JSON.stringify({ name, is_group: isGroup }),
    })
  }

  // Room Participants
  async addParticipant(roomId: number, userId: number) {
    return this.request<any>(`/chat-rooms/${roomId}/participants?user_id=${userId}`, {
      method: 'POST',
    })
  }

  async getRoomParticipants(roomId: number) {
    return this.request<any[]>(`/chat-rooms/${roomId}/participants`)
  }

  // Messages
  async getMessages(roomId: number) {
    return this.request<any[]>(`/messages/?room_id=${roomId}`)
  }

  async getLatestMessages(roomId: number, limit: number = 50) {
    return this.request<any[]>(`/messages/room/${roomId}/latest?limit=${limit}`)
  }

  async sendMessage(roomId: number, content: string) {
    return this.request<any>('/messages/', {
      method: 'POST',
      body: JSON.stringify({ room_id: roomId, content }),
    })
  }

  async deleteMessage(messageId: number, hard: boolean = false) {
    return this.request<any>(`/messages/${messageId}${hard ? '?hard=true' : ''}`, {
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

  // Contacts
  async getMyContacts() {
    return this.request<any[]>('/contacts/my-contacts')
  }

  async getPendingRequests() {
    return this.request<any[]>('/contacts/pending')
  }

  async getSentRequests() {
    return this.request<any[]>('/contacts/sent')
  }

  async sendContactRequest(contactId: number) {
    return this.request<any>('/contacts/', {
      method: 'POST',
      body: JSON.stringify({ contact_id: contactId }),
    })
  }

  async updateContactStatus(contactId: number, status: 'accepted' | 'blocked') {
    return this.request<any>(`/contacts/${contactId}`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    })
  }

  async deleteContact(contactId: number) {
    return this.request<void>(`/contacts/${contactId}`, {
      method: 'DELETE',
    })
  }

  async searchPublicUsers(query: string) {
    return this.request<any[]>(`/contacts/search-public-users?query=${encodeURIComponent(query)}`)
  }

  // Load conversations with participants and last messages
  async loadUserConversations() {
    try {
      // Get current user from storage
      const currentUser = this.getStoredUser()
      if (!currentUser) {
        throw new Error('No user logged in')
      }

      // Get user's rooms
      const rooms = await this.getChatRooms()

      // For each room, get participants and latest message
      const conversations = await Promise.all(
        rooms.map(async (room: any) => {
          const [participantsData, messages] = await Promise.all([
            this.getRoomParticipants(room.id),
            this.getLatestMessages(room.id, 1).catch(() => [])
          ])

          // Get full user data for all participants
          const participants = await Promise.all(
            participantsData.map(async (p: any) => {
              const userData = await this.getUser(p.user_id)
              return {
                ...p,
                user: userData
              }
            })
          )

          // Find the other participant (not the current user)
          const otherParticipant = participants.find((p: any) => p.user_id !== currentUser.id) || null

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
