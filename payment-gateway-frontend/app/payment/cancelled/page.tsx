"use client"

import { useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { AlertCircle, ArrowLeft, RefreshCw, Home } from "lucide-react"
import Link from "next/link"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { useAppStore } from "@/lib/store"
import { api } from "@/lib/api"
import SSLCommerzIntegration from "@/lib/sslcommerz"

export default function PaymentCancelledPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user } = useAppStore()
  
  const transactionId = searchParams.get("transaction_id")
  const reason = searchParams.get("reason") || "Payment was cancelled by user"

  useEffect(() => {
    // Handle payment cancellation
    if (user && transactionId) {
      const handleCancellation = async () => {
        try {
          // Handle payment failure with SSLCommerz integration
          await SSLCommerzIntegration.handlePaymentFailure(transactionId, reason)
          
          // Log the cancellation event
          await api.logAuditEvent({
            user_id: user.id,
            action: "PAYMENT_CANCELLED",
            service_name: "frontend",
            details: {
              transaction_id: transactionId,
              reason: reason,
              timestamp: new Date().toISOString(),
            },
          })
        } catch (error) {
          console.error("Failed to handle payment cancellation:", error)
        }
      }
      
      handleCancellation()
    }
  }, [user, transactionId, reason])

  return (
    <DashboardLayout>
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Cancellation Header */}
        <div className="text-center">
          <div className="w-20 h-20 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <AlertCircle className="w-12 h-12 text-yellow-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Payment Cancelled</h1>
          <p className="text-gray-600">
            Your payment was cancelled and no charges were made to your account.
          </p>
        </div>

        {/* Cancellation Details */}
        <Card className="border-yellow-200 bg-yellow-50">
          <CardHeader>
            <CardTitle className="text-yellow-900">What happened?</CardTitle>
            <CardDescription className="text-yellow-700">
              Your payment process was interrupted or cancelled
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {transactionId && (
              <div>
                <p className="text-sm text-yellow-700">Transaction ID</p>
                <p className="font-mono text-sm font-medium text-yellow-900">{transactionId}</p>
              </div>
            )}
            
            <div>
              <p className="text-sm text-yellow-700">Reason</p>
              <p className="font-medium text-yellow-900">{reason}</p>
            </div>

            <div className="bg-yellow-100 p-4 rounded-lg">
              <h4 className="font-medium text-yellow-900 mb-2">Common reasons for cancellation:</h4>
              <ul className="text-sm text-yellow-800 space-y-1">
                <li>• Payment was cancelled by user</li>
                <li>• Browser was closed during payment process</li>
                <li>• Payment gateway timeout</li>
                <li>• Insufficient funds or payment method issues</li>
                <li>• Network connectivity problems</li>
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Next Steps */}
        <Card>
          <CardHeader>
            <CardTitle>What can you do next?</CardTitle>
            <CardDescription>Choose from the options below to continue</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Button asChild className="h-auto p-4 flex-col items-start">
                <Link href="/send">
                  <RefreshCw className="w-6 h-6 mb-2" />
                  <div className="text-left">
                    <div className="font-semibold">Try Again</div>
                    <div className="text-xs opacity-90">Retry your payment</div>
                  </div>
                </Link>
              </Button>

              <Button variant="outline" asChild className="h-auto p-4 flex-col items-start bg-transparent">
                <Link href="/transactions">
                  <AlertCircle className="w-6 h-6 mb-2" />
                  <div className="text-left">
                    <div className="font-semibold">Check Status</div>
                    <div className="text-xs opacity-90">View transaction history</div>
                  </div>
                </Link>
              </Button>
            </div>

            <div className="pt-4 border-t">
              <h4 className="font-medium text-gray-900 mb-3">Need help?</h4>
              <div className="space-y-2 text-sm text-gray-600">
                <p>If you're experiencing repeated issues with payments:</p>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>Check your internet connection</li>
                  <li>Verify your payment method has sufficient funds</li>
                  <li>Try using a different browser or device</li>
                  <li>Contact our support team if the problem persists</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4">
          <Button asChild className="flex-1">
            <Link href="/send">
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Payment Again
            </Link>
          </Button>
          <Button variant="outline" asChild className="flex-1 bg-transparent">
            <Link href="/dashboard">
              <Home className="w-4 h-4 mr-2" />
              Return to Dashboard
            </Link>
          </Button>
        </div>

        <div className="text-center">
          <Button variant="ghost" asChild>
            <Link href="/transactions">
              <ArrowLeft className="w-4 h-4 mr-2" />
              View Transaction History
            </Link>
          </Button>
        </div>
      </div>
    </DashboardLayout>
  )
}