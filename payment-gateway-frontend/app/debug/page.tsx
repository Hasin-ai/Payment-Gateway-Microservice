"use client"

import { useAppStore } from "@/lib/store"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { BackendStatus } from "@/components/backend-status"

export default function DebugPage() {
  const { user, token, isAuthenticated, initializeAuth, login } = useAppStore()

  const handleInitAuth = () => {
    initializeAuth()
  }

  const checkLocalStorage = () => {
    if (typeof window !== "undefined") {
      const storedToken = localStorage.getItem("access_token")
      console.log("LocalStorage token:", storedToken)
      
      const cookies = document.cookie
      console.log("Document cookies:", cookies)
    }
  }

  const clearAuthData = () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token")
      document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT"
      console.log("Auth data cleared")
      window.location.reload()
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-2xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold">Debug Authentication</h1>
        
        <Card>
          <CardHeader>
            <CardTitle>Authentication State</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <strong>Is Authenticated:</strong> {isAuthenticated ? "Yes" : "No"}
            </div>
            <div>
              <strong>Has Token:</strong> {token ? "Yes" : "No"}
            </div>
            <div>
              <strong>Token Preview:</strong> {token ? `${token.substring(0, 20)}...` : "None"}
            </div>
            <div>
              <strong>Has User:</strong> {user ? "Yes" : "No"}
            </div>
            <div>
              <strong>User Email:</strong> {user?.email || "None"}
            </div>
            <div>
              <strong>User Name:</strong> {user ? `${user.first_name} ${user.last_name}` : "None"}
            </div>
          </CardContent>
        </Card>

        <div className="flex space-x-4">
          <Button onClick={handleInitAuth}>
            Initialize Auth
          </Button>
          <Button onClick={checkLocalStorage} variant="outline">
            Check Storage
          </Button>
          <Button onClick={clearAuthData} variant="destructive">
            Clear Auth Data
          </Button>
        </div>
        
        <BackendStatus />
        
        <Card className="bg-yellow-50 border-yellow-200">
          <CardContent className="pt-6">
            <p className="text-sm text-yellow-800">
              <strong>Note:</strong> To test login, use the actual login page at <code>/login</code> with 
              credentials from a user you've registered via the backend API or registration page.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}