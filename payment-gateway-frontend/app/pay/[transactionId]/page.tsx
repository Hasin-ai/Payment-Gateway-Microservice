"use client"

import { useEffect, useState } from "react"
import { useParams, useSearchParams } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { 
  CreditCard, 
  Shield, 
  Globe, 
  CheckCircle, 
  Loader2, 
  AlertCircle,
  DollarSign,
  Calculator
} from "lucide-react"
import { api } from "@/lib/api"
import { formatCurrency } from "@/lib/utils"
import { toast } from "sonner"

export default function PaymentPage() {
  const params = useParams()
  const searchParams = useSearchParams()
  
  const transactionId = params.transactionId as string
  const amount = searchParams.get("amount")
  const currency = searchParams.get("currency") || "USD"
  const email = searchParams.get("email")
  
  const [transaction, setTransaction] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState("")
  const [calculation, setCalculation] = useState({
    originalAmount: 0,
    exchangeRate: 110.5,
    convertedAmount: 0,
    serviceFee: 0,
    totalAmount: 0,
  })

  useEffect(() => {
    if (transactionId) {
      fetchTransactionDetails()
    }
    if (amount) {
      calculatePaymentAmount(Number.parseFloat(amount), currency)
    }
  }, [transactionId, amount, currency])

  const fetchTransactionDetails = async () => {
    try {
      setIsLoading(true)
      const transactionData = await api.getTransaction(transactionId)
      setTransaction(transactionData)
    } catch (error) {
      console.error("Failed to fetch transaction:", error)
      setError("Invalid payment link or transaction not found")
    } finally {
      setIsLoading(false)
    }
  }

  const calculatePaymentAmount = async (amount: number, currency: string) => {
    try {
      const response = await api.calculateAmount({
        from_currency: currency,
        to_currency: "BDT",
        amount: amount,
        service_fee_percentage: 2.0,
      })

      setCalculation({
        originalAmount: amount,
        exchangeRate: response.data.exchange_rate,
        convertedAmount: response.data.converted_amount,
        serviceFee: response.data.service_fee_amount,
        totalAmount: response.data.total_amount,
      })
    } catch (error) {
      console.error("Failed to calculate amount:", error)
    }
  }

  const handlePayment = async () => {
    setIsProcessing(true)
    setError("")

    try {
      // In a real implementation, this would integrate with PayPal or other payment processors
      const paymentResponse = await api.initiatePayment({
        user_id: transaction?.user_id || 0,
        amount: Number.parseFloat(amount || "0"),
        currency: currency,
        payment_method: "paypal",
        return_url: `${window.location.origin}/payment/success?transaction_id=${transactionId}`,
        cancel_url: `${window.location.origin}/payment/cancelled?transaction_id=${transactionId}`,
      })

      if (paymentResponse.payment_url) {
        // Redirect to PayPal or payment processor
        window.location.href = paymentResponse.payment_url
      } else {
        throw new Error("Payment URL not received")
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : "Payment initiation failed")
      toast.error("Failed to initiate payment")
    } finally {
      setIsProcessing(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading Payment Details...</h2>
          <p className="text-gray-600">Please wait while we prepare your payment.</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md mx-auto">
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <div className="text-center">
                <AlertCircle className="h-16 w-16 text-red-600 mx-auto mb-4" />
                <h2 className="text-xl font-semibold text-gray-900 mb-2">Payment Error</h2>
                <p className="text-gray-600 mb-6">{error}</p>
                <Button onClick={() => window.location.reload()}>
                  Try Again
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-green-600 rounded-lg flex items-center justify-center">
              <Globe className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900">PayGateway</span>
            <Badge className="bg-green-100 text-green-800 ml-auto">
              <Shield className="w-3 h-3 mr-1" />
              Secure Payment
            </Badge>
          </div>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
        {/* Payment Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Complete Your Payment</h1>
          <p className="text-gray-600">
            You're paying {transaction?.user_id ? "a freelancer" : "a business"} for their services
          </p>
        </div>

        {/* Payment Details */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <DollarSign className="w-5 h-5 mr-2" />
              Payment Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">Amount</p>
                <p className="text-2xl font-bold text-blue-600">
                  {currency} {formatCurrency(Number.parseFloat(amount || "0"))}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Payment To</p>
                <p className="font-semibold">{email || "Service Provider"}</p>
              </div>
            </div>

            {transaction && (
              <>
                <Separator />
                <div>
                  <p className="text-sm text-gray-500">Description</p>
                  <p className="font-medium">{transaction.description}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Transaction ID</p>
                  <p className="font-mono text-sm">{transaction.transaction_id}</p>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Cost Breakdown */}
        {calculation.originalAmount > 0 && (
          <Card className="bg-blue-50 border-blue-200">
            <CardHeader>
              <CardTitle className="flex items-center text-blue-900">
                <Calculator className="w-5 h-5 mr-2" />
                Cost Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between">
                <span>Amount:</span>
                <span className="font-medium">{currency} {formatCurrency(calculation.originalAmount)}</span>
              </div>
              <div className="flex justify-between">
                <span>Exchange Rate:</span>
                <span className="font-medium">1 {currency} = {formatCurrency(calculation.exchangeRate)} BDT</span>
              </div>
              <div className="flex justify-between">
                <span>Converted Amount:</span>
                <span className="font-medium">{formatCurrency(calculation.convertedAmount)} BDT</span>
              </div>
              <div className="flex justify-between text-red-600">
                <span>Processing Fee:</span>
                <span className="font-medium">+{formatCurrency(calculation.serviceFee)} BDT</span>
              </div>
              <Separator />
              <div className="flex justify-between text-lg font-bold text-blue-900">
                <span>Total:</span>
                <span>{formatCurrency(calculation.totalAmount)} BDT</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Payment Method */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <CreditCard className="w-5 h-5 mr-2" />
              Payment Method
            </CardTitle>
            <CardDescription>
              You'll be redirected to PayPal to complete your payment securely
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between p-4 border rounded-lg bg-blue-50 border-blue-200">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-8 bg-blue-600 rounded flex items-center justify-center">
                  <span className="text-white font-bold text-xs">PayPal</span>
                </div>
                <div>
                  <p className="font-medium text-blue-900">PayPal</p>
                  <p className="text-sm text-blue-700">Pay with your PayPal account or credit card</p>
                </div>
              </div>
              <CheckCircle className="w-5 h-5 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        {/* Security Notice */}
        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-6">
            <div className="flex items-start space-x-3">
              <Shield className="w-5 h-5 text-green-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-green-900 mb-2">Secure Payment</h4>
                <ul className="text-sm text-green-800 space-y-1">
                  <li>• Your payment is processed securely through PayPal</li>
                  <li>• We never store your payment information</li>
                  <li>• All transactions are encrypted and monitored</li>
                  <li>• You'll receive a confirmation email after payment</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {error && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-3">
                <AlertCircle className="w-5 h-5 text-red-600" />
                <p className="text-red-800">{error}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Payment Button */}
        <Button 
          onClick={handlePayment} 
          className="w-full h-12 text-lg" 
          size="lg"
          disabled={isProcessing}
        >
          {isProcessing ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              Pay {currency} {formatCurrency(Number.parseFloat(amount || "0"))}
              <CreditCard className="ml-2 h-5 w-5" />
            </>
          )}
        </Button>

        {/* Footer */}
        <div className="text-center text-sm text-gray-500 pt-6">
          <p>Powered by PayGateway • Secure International Payments</p>
          <p className="mt-1">
            Need help? Contact support or the person who sent you this payment link.
          </p>
        </div>
      </div>
    </div>
  )
}