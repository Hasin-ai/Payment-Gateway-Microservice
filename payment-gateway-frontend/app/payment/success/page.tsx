"use client"

import { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, ArrowRight, Download, Share2, Loader2 } from "lucide-react"
import Link from "next/link"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { useAppStore } from "@/lib/store"
import { api } from "@/lib/api"
import { formatCurrency, formatDate } from "@/lib/utils"
import { toast } from "sonner"
import SSLCommerzIntegration from "@/lib/sslcommerz"

export default function PaymentSuccessPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user, fetchTransactions } = useAppStore()
  
  const [transaction, setTransaction] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")

  const transactionId = searchParams.get("transaction_id")
  const paymentId = searchParams.get("payment_id")

  useEffect(() => {
    if (transactionId) {
      fetchTransactionDetails()
    } else {
      setError("No transaction ID provided")
      setIsLoading(false)
    }
  }, [transactionId])

  const fetchTransactionDetails = async () => {
    try {
      setIsLoading(true)
      
      // Handle payment success with SSLCommerz integration
      const confirmResult = await SSLCommerzIntegration.handlePaymentSuccess(
        transactionId!,
        paymentId || undefined
      )
      
      if (!confirmResult.success) {
        throw new Error(confirmResult.message)
      }
      
      const transactionData = await api.getTransaction(transactionId!)
      setTransaction(transactionData)
      
      // Refresh transactions list
      await fetchTransactions()
      
      // Send notification about successful payment
      if (user) {
        await api.sendNotification({
          user_id: user.id,
          title: "Payment Successful",
          message: `Your payment of ${transactionData.currency} ${transactionData.amount} has been processed successfully.`,
          channels: ["email", "in_app"],
          priority: 5,
        })
      }
      
      toast.success("Payment completed successfully!")
    } catch (error) {
      console.error("Failed to process payment success:", error)
      setError("Failed to process payment confirmation")
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="max-w-2xl mx-auto flex items-center justify-center h-96">
          <div className="text-center">
            <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Processing Payment...</h2>
            <p className="text-gray-600">Please wait while we confirm your payment.</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (error || !transaction) {
    return (
      <DashboardLayout>
        <div className="max-w-2xl mx-auto">
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-red-600 text-2xl">✕</span>
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">Payment Error</h2>
                <p className="text-gray-600 mb-6">{error || "Unable to load payment details"}</p>
                <Button asChild>
                  <Link href="/dashboard">Return to Dashboard</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Success Header */}
        <div className="text-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-12 h-12 text-green-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Payment Successful!</h1>
          <p className="text-gray-600">
            Your payment has been processed successfully and the recipient will be notified.
          </p>
        </div>

        {/* Transaction Details */}
        <Card>
          <CardHeader>
            <CardTitle>Transaction Details</CardTitle>
            <CardDescription>Payment confirmation and details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">Transaction ID</p>
                <p className="font-mono text-sm font-medium">{transaction.transaction_id}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Status</p>
                <Badge className="bg-green-100 text-green-800">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  {transaction.status}
                </Badge>
              </div>
              <div>
                <p className="text-sm text-gray-500">Amount</p>
                <p className="font-semibold">
                  {transaction.currency} {formatCurrency(Number.parseFloat(transaction.amount))}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Converted Amount</p>
                <p className="font-semibold text-green-600">
                  {formatCurrency(Number.parseFloat(transaction.converted_amount))} BDT
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Exchange Rate</p>
                <p className="font-medium">
                  1 {transaction.currency} = {formatCurrency(Number.parseFloat(transaction.exchange_rate))} BDT
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Service Fee</p>
                <p className="font-medium text-red-600">
                  {formatCurrency(Number.parseFloat(transaction.fees))} BDT
                </p>
              </div>
            </div>

            {transaction.recipient_email && (
              <div>
                <p className="text-sm text-gray-500">
                  {transaction.transaction_type === "send" ? "Recipient" : "From"}
                </p>
                <p className="font-medium">{transaction.recipient_email}</p>
              </div>
            )}

            <div>
              <p className="text-sm text-gray-500">Description</p>
              <p>{transaction.description}</p>
            </div>

            <div>
              <p className="text-sm text-gray-500">Processed At</p>
              <p className="font-medium">{formatDate(transaction.updated_at)}</p>
            </div>

            {paymentId && (
              <div>
                <p className="text-sm text-gray-500">Payment Reference</p>
                <p className="font-mono text-sm">{paymentId}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Next Steps */}
        <Card className="bg-blue-50 border-blue-200">
          <CardHeader>
            <CardTitle className="text-blue-900">What happens next?</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {transaction.transaction_type === "send" ? (
              <>
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold mt-0.5">
                    1
                  </div>
                  <div>
                    <p className="font-medium text-blue-900">Payment Processing</p>
                    <p className="text-sm text-blue-700">
                      Your BDT payment has been received and is being converted to {transaction.currency}.
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold mt-0.5">
                    2
                  </div>
                  <div>
                    <p className="font-medium text-blue-900">International Transfer</p>
                    <p className="text-sm text-blue-700">
                      The {transaction.currency} amount will be sent to {transaction.recipient_email} via PayPal.
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold mt-0.5">
                    3
                  </div>
                  <div>
                    <p className="font-medium text-blue-900">Confirmation</p>
                    <p className="text-sm text-blue-700">
                      Both you and the recipient will receive confirmation emails once the transfer is complete.
                    </p>
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-green-600 text-white rounded-full flex items-center justify-center text-xs font-bold mt-0.5">
                    1
                  </div>
                  <div>
                    <p className="font-medium text-green-900">Payment Received</p>
                    <p className="text-sm text-green-700">
                      Your client's payment has been successfully processed.
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-green-600 text-white rounded-full flex items-center justify-center text-xs font-bold mt-0.5">
                    2
                  </div>
                  <div>
                    <p className="font-medium text-green-900">Currency Conversion</p>
                    <p className="text-sm text-green-700">
                      The {transaction.currency} amount has been converted to BDT at the current exchange rate.
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-green-600 text-white rounded-full flex items-center justify-center text-xs font-bold mt-0.5">
                    3
                  </div>
                  <div>
                    <p className="font-medium text-green-900">Funds Available</p>
                    <p className="text-sm text-green-700">
                      The converted BDT amount will be available in your account within 1-2 business days.
                    </p>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4">
          <Button asChild className="flex-1">
            <Link href="/transactions">
              <Download className="w-4 h-4 mr-2" />
              View All Transactions
            </Link>
          </Button>
          <Button variant="outline" className="flex-1 bg-transparent">
            <Share2 className="w-4 h-4 mr-2" />
            Share Receipt
          </Button>
        </div>

        <div className="text-center">
          <Button variant="ghost" asChild>
            <Link href="/dashboard">
              Return to Dashboard
              <ArrowRight className="w-4 h-4 ml-2" />
            </Link>
          </Button>
        </div>
      </div>
    </DashboardLayout>
  )
}