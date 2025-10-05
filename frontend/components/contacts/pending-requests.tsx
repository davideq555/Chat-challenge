"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ReceivedRequests } from "./received-requests"
import { SentRequests } from "./sent-requests"

export function PendingRequests() {
  const [activeTab, setActiveTab] = useState("received")

  return (
    <Tabs value={activeTab} onValueChange={setActiveTab}>
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="received">Recibidas</TabsTrigger>
        <TabsTrigger value="sent">Enviadas</TabsTrigger>
      </TabsList>

      <TabsContent value="received" className="mt-4">
        <ReceivedRequests />
      </TabsContent>

      <TabsContent value="sent" className="mt-4">
        <SentRequests />
      </TabsContent>
    </Tabs>
  )
}
