"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, XCircle, Loader2, RefreshCw } from "lucide-react"
import { api } from "@/lib/api"

interface ServiceTest {
  name: string
  endpoint: string
  status: "idle" | "testing" | "success" | "error"
  response?: any
  error?: string
  responseTime?: number
}

export default function TestBackendPage() {
  const [tests, setTests] = useState<ServiceTest[]>([
    { name: "System Health", endpoint: "/health", status: "idle" },
    { name: "Circuit Breaker Status", endpoint: "/circuit-breaker/status", status: "idle" },
    { name: "Exchange Rate (USD)", endpoint: "/api/exchange-rate/api/v1/rates/current?currency=USD", status: "idle" },
    { name: "User Registration", endpoint: "/api/users/register", status: "idle" },
    { name: "Notification Stats", endpoint: "/api/notifications/stats", status: "idle" },
    { name: "Audit Logs", endpoint: "/api/audit/logs", status: "idle" },
  ])

  const [isTestingAll, setIsTestingAll] = useState(false)

  const testEndpoint = async (index: number) => {
    const test = tests[index]
    setTests(prev => prev.map((t, i) => i === index ? { ...t, status: "testing" } : t))

    const startTime = Date.now()
    
    try {
      let response
      
      switch (test.endpoint) {
        case "/health":
          response = await api.getSystemHealth()
          break
        case "/circuit-breaker/status":
          response = await fetch("http://localhost:8080/circuit-breaker/status").then(r => r.json())
          break
        case "/api/exchange-rate/api/v1/rates/current?currency=USD":
          response = await api.getCurrentRate("USD")
          break
        case "/api/users/register":
          // Test with a dummy registration (this will likely fail due to duplicate email, but that's expected)
          try {
            response = await api.register({
              email: `test-${Date.now()}@example.com`,
              password: "testpassword123",
              first_name: "Test",
              last_name: "User",
              phone: "+1234567890"
            })
          } catch (error: any) {
            // If it's a validation error or duplicate email, that means the endpoint is working
            if (error.message.includes("already exists") || error.message.includes("validation")) {
              response = { message: "Endpoint accessible (expected validation error)" }
            } else {
              throw error
            }
          }
          break
        case "/api/notifications/stats":
          response = await api.getNotificationStats()
          break
        case "/api/audit/logs":
          response = await api.getAuditLogs({ limit: 5 })
          break
        default:
          response = await fetch(`http://localhost:8080${test.endpoint}`).then(r => r.json())
      }

      const responseTime = Date.now() - startTime
      
      setTests(prev => prev.map((t, i) => 
        i === index 
          ? { ...t, status: "success", response, responseTime, error: undefined }
          : t
      ))
    } catch (error: any) {
      const responseTime = Date.now() - startTime
      
      setTests(prev => prev.map((t, i) => 
        i === index 
          ? { ...t, status: "error", error: error.message, responseTime, response: undefined }
          : t
      ))
    }
  }

  const testAllEndpoints = async () => {
    setIsTestingAll(true)
    
    // Reset all tests
    setTests(prev => prev.map(t => ({ ...t, status: "idle", response: undefined, error: undefined })))
    
    // Test each endpoint sequentially
    for (let i = 0; i < tests.length; i++) {
      await testEndpoint(i)
      // Small delay between tests
      await new Promise(resolve => setTimeout(resolve, 500))
    }
    
    setIsTestingAll(false)
  }

  const getStatusIcon = (status: ServiceTest["status"]) => {
    switch (status) {
      case "testing":
        return <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case "error":
        return <XCircle className="h-4 w-4 text-red-600" />
      default:
        return <div className="h-4 w-4 rounded-full bg-gray-300" />
    }
  }

  const getStatusBadge = (status: ServiceTest["status"]) => {
    switch (status) {
      case "testing":
        return <Badge variant="secondary">Testing...</Badge>
      case "success":
        return <Badge className="bg-green-100 text-green-800">Success</Badge>
      case "error":
        return <Badge variant="destructive">Error</Badge>
      default:
        return <Badge variant="outline">Not Tested</Badge>
    }
  }

  const successCount = tests.filter(t => t.status === "success").length
  const errorCount = tests.filter(t => t.status === "error").length
  const totalTests = tests.length

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Backend Connectivity Test</h1>
          <p className="text-gray-600">Test all backend microservices to ensure proper connectivity</p>
        </div>

        {/* Summary */}
        <Card>
          <CardHeader>
            <CardTitle>Test Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-green-600">{successCount}</div>
                <div className="text-sm text-gray-500">Successful</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-red-600">{errorCount}</div>
                <div className="text-sm text-gray-500">Failed</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-600">{totalTests}</div>
                <div className="text-sm text-gray-500">Total Tests</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Controls */}
        <div className="flex justify-center">
          <Button 
            onClick={testAllEndpoints} 
            disabled={isTestingAll}
            size="lg"
          >
            {isTestingAll ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Testing All Services...
              </>
            ) : (
              <>
                <RefreshCw className="mr-2 h-4 w-4" />
                Test All Services
              </>
            )}
          </Button>
        </div>

        {/* Test Results */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {tests.map((test, index) => (
            <Card key={index}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{test.name}</CardTitle>
                  {getStatusIcon(test.status)}
                </div>
                <div className="flex items-center justify-between">
                  <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                    {test.endpoint}
                  </code>
                  {getStatusBadge(test.status)}
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                {test.responseTime && (
                  <div className="text-sm text-gray-500 mb-2">
                    Response time: {test.responseTime}ms
                  </div>
                )}
                
                {test.error && (
                  <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                    <strong>Error:</strong> {test.error}
                  </div>
                )}
                
                {test.response && (
                  <div className="text-sm">
                    <strong>Response:</strong>
                    <pre className="mt-1 bg-gray-100 p-2 rounded text-xs overflow-x-auto">
                      {JSON.stringify(test.response, null, 2)}
                    </pre>
                  </div>
                )}
                
                <div className="mt-3">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => testEndpoint(index)}
                    disabled={test.status === "testing"}
                  >
                    {test.status === "testing" ? "Testing..." : "Test"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Backend Status Info */}
        <Card className="bg-blue-50 border-blue-200">
          <CardHeader>
            <CardTitle className="text-blue-900">Backend Requirements</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-blue-800 space-y-2">
              <p><strong>Make sure the backend services are running:</strong></p>
              <ul className="list-disc list-inside space-y-1 ml-4">
                <li>Navigate to the services directory: <code>cd services</code></li>
                <li>Start all services: <code>docker-compose up -d --build</code></li>
                <li>Check service status: <code>docker-compose ps</code></li>
                <li>View logs if needed: <code>docker-compose logs -f</code></li>
              </ul>
              <p className="mt-3">
                <strong>Expected services:</strong> Gateway (8000), User (8001), Payment (8002), 
                Transaction (8003), Notification (8004), Audit (8005), Exchange Rate (8006), 
                Admin (8007), Nginx (8080), PostgreSQL (5433), Redis (6380)
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}