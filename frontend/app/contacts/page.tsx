"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import { ContactList } from "@/components/contacts/contact-list"
import { PendingRequests } from "@/components/contacts/pending-requests"
import { BlockedContacts } from "@/components/contacts/blocked-contacts"
import { SearchUsers } from "@/components/contacts/search-users"

export default function ContactsPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState("contacts")

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push("/chat")}
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold">Contactos</h1>
              <p className="text-sm text-muted-foreground">
                Administra tus contactos y solicitudes
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="contacts">Contactos</TabsTrigger>
            <TabsTrigger value="pending">Pendientes</TabsTrigger>
            <TabsTrigger value="blocked">Bloqueados</TabsTrigger>
            <TabsTrigger value="search">Buscar</TabsTrigger>
          </TabsList>

          <TabsContent value="contacts" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Mis Contactos</CardTitle>
                <CardDescription>
                  Lista de contactos aceptados
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ContactList />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="pending" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Solicitudes Pendientes</CardTitle>
                <CardDescription>
                  Solicitudes de contacto recibidas
                </CardDescription>
              </CardHeader>
              <CardContent>
                <PendingRequests />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="blocked" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Contactos Bloqueados</CardTitle>
                <CardDescription>
                  Usuarios que has bloqueado
                </CardDescription>
              </CardHeader>
              <CardContent>
                <BlockedContacts />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="search" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Buscar Usuarios</CardTitle>
                <CardDescription>
                  Encuentra usuarios públicos para agregar como contactos
                </CardDescription>
              </CardHeader>
              <CardContent>
                <SearchUsers />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
