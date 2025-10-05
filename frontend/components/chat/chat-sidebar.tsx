"use client"

import { useState } from "react"
import { Search, Plus } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ConversationItem } from "./conversation-item"
import { NewConversationDialog } from "./new-conversation-dialog"
import type { Conversation, User } from "./chat-layout"

type ChatSidebarProps = {
  conversations: Conversation[]
  selectedConversation: Conversation | null
  onSelectConversation: (conversation: Conversation) => void
  onConversationCreated: () => void
  currentUser: User
}

export function ChatSidebar({
  conversations,
  selectedConversation,
  onSelectConversation,
  onConversationCreated,
  currentUser,
}: ChatSidebarProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [newConversationOpen, setNewConversationOpen] = useState(false)

  const filteredConversations = conversations.filter((conv) =>
    conv.user.username.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  return (
    <div className="w-full md:w-96 border-r border-border bg-card flex flex-col">
      {/* Search Bar */}
      <div className="p-4 space-y-3">
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar conversaciones..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button
            size="icon"
            variant="ghost"
            title="Nueva conversación"
            onClick={() => setNewConversationOpen(true)}
          >
            <Plus className="h-5 w-5" />
          </Button>
        </div>
      </div>

      {/* Conversations List */}
      <ScrollArea className="flex-1">
        <div className="space-y-1 px-2">
          {filteredConversations.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground text-sm">No hay conversaciones</div>
          ) : (
            filteredConversations.map((conversation) => (
              <ConversationItem
                key={conversation.id}
                conversation={conversation}
                isSelected={selectedConversation?.id === conversation.id}
                onClick={() => onSelectConversation(conversation)}
                currentUserId={currentUser.id}
              />
            ))
          )}
        </div>
      </ScrollArea>

      {/* New Conversation Dialog */}
      <NewConversationDialog
        open={newConversationOpen}
        onOpenChange={setNewConversationOpen}
        onConversationCreated={onConversationCreated}
      />
    </div>
  )
}
