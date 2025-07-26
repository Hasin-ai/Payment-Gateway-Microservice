"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { CheckCircle, XCircle, Loader2, RefreshCw, AlertTriangle } from "lucide-react"
import { api } from "@/lib/api"

interface ServiceStatus {
  name: string
  url: string
  status: "checking" | "healthy" | "unhealthy" | "unknown"
  responseTime?: number
  error?: string
}

export function BackendStatus() {
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: "Load Balancer", url: "http://localhost:8080", status: "unknown" },
    { name: "API Gateway", url: "http://localhost:8000", status: "unknown" },
    { name: "User Service", url: "http://localhost:8001", status: "unknown" },
    { name: "Payment Service", url: "http://localhost:8002", status: "unknown" },
    { name: "Transaction Service", url: "http://localhost:8003", status: "unknown" },
    { name: "Notification Service", url: "http://localhost:8004", status: "unknown" },
    { name: "Audit Service", url: "http://localhost:8005", status: "unknown" },
    { name: "Exchange Rate Service", url: "http://localhost:8006", status: "unknown" },
    { name: "Admin Service", url: "http://localhost:8007", status: "unknown" },
  ])

  const [isChecking, setIsChecking] = useState(false)

  const checkServiceHealth = async (service: ServiceStatus): Promise<ServiceStatus> => {
    const startTime = Date.now()
    
    try {
      let response
      
      if (service.name === "Load Balancer") {
        // Check load balancer health through our API
        response = await api.getSystemHealth()
      } else {
        // Direct health check to individual services
        const healthUrl = `${service.url}/health`
        response = await fetch(healthUrl, { 
          method: "GET",
          headers: { "Content-Type": "application/json" }
        })
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        
        await response.json() // Parse JSON to ensure it's valid
      }
      
      const responseTime = Date.now() - startTime
      
      return {
        ...service,
        status: "healthy",
        responseTime,
        error: undefined
      }
    } catch (error: any) {
      const responseTime = Date.now() - startTime
      
      return {
        ...service,
        status: "unhealthy",
        responseTime,
        error: error.message
      }
    }
  }

  const checkAllServices = async () => {
    setIsChecking(true)
    
    // Set all services to checking status
    setServices(prev => prev.map(service => ({ ...service, status: "checking" as const })))
    
    // Check each service
    const promises = services.map(checkServiceHealth)
    const results = await Promise.all(promises)
    
    setServices(results)
    setIsChecking(false)
  }

  useEffect(() => {
    // Check services on component mount
    checkAllServices()
  }, [])

  const getStatusIcon = (status: ServiceStatus["status"]) => {
    switch (status) {
      case "checking":
        return <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
      case "healthy":
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case "unhealthy":
        return <XCircle className="h-4 w-4 text-red-600" />
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusBadge = (status: ServiceStatus["status"]) => {
    switch (status) {
      case "checking":
        return <Badge variant="secondary">Checking...</Badge>
      case "healthy":
        return <Badge className="bg-green-100 text-green-800">Healthy</Badge>
      case "unhealthy":
        return <Badge variant="destructive">Unhealthy</Badge>
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  const healthyCount = services.filter(s => s.status === "healthy").length
  const unhealthyCount = services.filter(s => s.status === "unhealthy").length
  const totalServices = services.length

  const overallStatus = unhealthyCount === 0 ? "healthy" : unhealthyCount < totalServices ? "partial" : "unhealthy"

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center">
            {overallStatus === "healthy" && <CheckCircle className="h-5 w-5 text-green-600 mr-2" />}
            {overallStatus === "partial" && <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2" />}
            {overallStatus === "unhealthy" && <XCircle className="h-5 w-5 text-red-600 mr-2" />}
            Backend Services Status
          </CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={checkAllServices}
            disabled={isChecking}
          >
            {isChecking ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Refresh
          </Button>
        </div>
        <div className="text-sm text-gray-600">
          {healthyCount}/{totalServices} services healthy
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {services.map((service, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 border rounded-lg"
            >
              <div className="flex items-center space-x-3">
                {getStatusIcon(service.status)}
                <div>
                  <div className="font-medium text-sm">{service.name}</div>
                  <div className="text-xs text-gray-500">
                    {service.url.replace("http://localhost:", ":")}
                  </div>
                  {service.responseTime && (
                    <div className="text-xs text-gray-400">
                      {service.responseTime}ms
                    </div>
                  )}
                </div>
              </div>
              <div className="text-right">
                {getStatusBadge(service.status)}
                {service.error && (
                  <div className="text-xs text-red-600 mt-1 max-w-20 truncate" title={service.error}>
                    {service.error}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {unhealthyCount > 0 && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="text-sm text-red-800">
              <strong>Some services are not responding.</strong> Make sure the backend is running:
            </div>
            <div className="text-xs text-red-700 mt-2 space-y-1">
              <div>1. Navigate to services directory: <code>cd services</code></div>
              <div>2. Start services: <code>docker-compose up -d --build</code></div>
              <div>3. Check status: <code>docker-compose ps</code></div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}