"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Eye, EyeOff, Loader2 } from "lucide-react"
import { apiClient } from "@/lib/api"

export function SettingsForm() {
  const [currentUser, setCurrentUser] = useState<any>(null)
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [loadingPassword, setLoadingPassword] = useState(false)
  const [loadingPrivacy, setLoadingPrivacy] = useState(false)
  const [passwordError, setPasswordError] = useState("")
  const [privacyError, setPrivacyError] = useState("")
  const [passwordSuccess, setPasswordSuccess] = useState(false)
  const [privacySuccess, setPrivacySuccess] = useState(false)
  const [isPublic, setIsPublic] = useState(true)
  const [passwordData, setPasswordData] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  })

  const isValidPassword = (pw: string) => {
    if (!pw) return false
    // at least 8 chars and at least one digit
    return /^(?=.*\d).{8,}$/.test(pw)
  }

  useEffect(() => {
    const user = apiClient.getStoredUser()
    if (user) {
      setCurrentUser(user)
      setIsPublic(user.is_public !== false)
    }
  }, [])

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordError("")
    setPasswordSuccess(false)

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setPasswordError("Las contraseñas nuevas no coinciden")
      return
    }

    if (!isValidPassword(passwordData.newPassword)) {
      setPasswordError("La contraseña debe tener al menos 8 caracteres e incluir al menos un número")
      return
    }

    if (!currentUser) {
      setPasswordError("No se encontró el usuario actual")
      return
    }

    setLoadingPassword(true)

    try {
      // Primero verificar credenciales actuales
      await apiClient.login(currentUser.email, passwordData.currentPassword)

      // Si el login es exitoso, actualizar la contraseña
      await apiClient.updateUser(currentUser.id, { password: passwordData.newPassword })

      setPasswordSuccess(true)
      setPasswordData({
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      })
    } catch (error) {
      console.error("Error:", error)
      setPasswordError(error instanceof Error ? error.message : "Error al cambiar la contraseña")
    } finally {
      setLoadingPassword(false)
    }
  }

  const handlePrivacySubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setPrivacyError("")
    setPrivacySuccess(false)

    if (!currentUser) {
      setPrivacyError("No se encontró el usuario actual")
      return
    }

    setLoadingPrivacy(true)

    try {
      const updatedUser = await apiClient.updateUser(currentUser.id, { is_public: isPublic })

      // Actualizar el usuario en localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('user', JSON.stringify(updatedUser))
      }

      setCurrentUser(updatedUser)
      setPrivacySuccess(true)

      setTimeout(() => {
        setPrivacySuccess(false)
      }, 3000)
    } catch (error) {
      console.error("Error:", error)
      setPrivacyError(error instanceof Error ? error.message : "Error al actualizar la privacidad")
    } finally {
      setLoadingPrivacy(false)
    }
  }

  if (!currentUser) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Password Change Section */}
      <Card>
        <CardHeader>
          <CardTitle>Cambiar Contraseña</CardTitle>
          <CardDescription>Actualiza tu contraseña de acceso</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            {passwordError && (
              <div className="p-3 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md">
                {passwordError}
              </div>
            )}

            {passwordSuccess && (
              <div className="p-3 text-sm text-green-600 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
                Contraseña actualizada exitosamente
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="currentPassword">Contraseña Actual</Label>
              <div className="relative">
                <Input
                  id="currentPassword"
                  type={showCurrentPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={passwordData.currentPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, currentPassword: e.target.value })}
                  required
                  disabled={loadingPassword || passwordSuccess}
                />
                <button
                  type="button"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showCurrentPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="newPassword">Nueva Contraseña</Label>
              <div className="relative">
                <Input
                  id="newPassword"
                  type={showNewPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={passwordData.newPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                  required
                  minLength={8}
                  disabled={loadingPassword || passwordSuccess}
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {!isValidPassword(passwordData.newPassword) && passwordData.newPassword.length > 0 && (
                <p className="text-sm text-destructive mt-1">La contraseña debe tener al menos 8 caracteres e incluir al menos un número.</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirmar Nueva Contraseña</Label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={passwordData.confirmPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                  required
                  minLength={8}
                  disabled={loadingPassword || passwordSuccess}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {passwordData.confirmPassword.length > 0 && passwordData.newPassword !== passwordData.confirmPassword && (
                <p className="text-sm text-destructive mt-1">Las contraseñas no coinciden.</p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={
                loadingPassword ||
                passwordSuccess ||
                !isValidPassword(passwordData.newPassword) ||
                passwordData.newPassword !== passwordData.confirmPassword
              }
            >
              {loadingPassword ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Cambiando contraseña...
                </>
              ) : (
                "Cambiar Contraseña"
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Privacy Settings Section */}
      <Card>
        <CardHeader>
          <CardTitle>Privacidad del Perfil</CardTitle>
          <CardDescription>Controla la visibilidad de tu perfil</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePrivacySubmit} className="space-y-4">
            {privacyError && (
              <div className="p-3 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md">
                {privacyError}
              </div>
            )}

            {privacySuccess && (
              <div className="p-3 text-sm text-green-600 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
                Configuración de privacidad actualizada exitosamente
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="isPublic">Visibilidad del Perfil</Label>
              <select
                id="isPublic"
                value={isPublic ? "public" : "private"}
                onChange={(e) => setIsPublic(e.target.value === "public")}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                disabled={loadingPrivacy}
              >
                <option value="public">Público - Otros usuarios pueden iniciar conversacion</option>
                <option value="private">Privado - Solo contactos pueden iniciar conversacion</option>
              </select>
              <p className="text-sm text-muted-foreground">
                {isPublic
                  ? "Tu perfil es visible para que todos los usuarios puedan iniciar conversacion."
                  : "Tu perfil es privado. Solo tus contactos pueden conversar contigo."}
              </p>
            </div>

            <Button type="submit" className="w-full" disabled={loadingPrivacy}>
              {loadingPrivacy ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Guardando...
                </>
              ) : (
                "Guardar Configuración"
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
