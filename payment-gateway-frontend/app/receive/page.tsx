"use client"

import Link from "next/link"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Separator } from "@/components/ui/separator"
import {
  Download,
  DollarSign,
  Calculator,
  LinkIcon,
  QrCode,
  Mail,
  Copy,
  CheckCircle,
  Loader2,
  ArrowRight,
} from "lucide-react"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { useAppStore } from "@/lib/store"
import { api } from "@/lib/api"
import { formatCurrency, validateEmail } from "@/lib/utils"
import { toast } from "sonner"

const currencies = [
  { code: "USD", name: "US Dollar", symbol: "$" },
  { code: "EUR", name: "Euro", symbol: "€" },
  { code: "GBP", name: "British Pound", symbol: "£" },
  { code: "CAD", name: "Canadian Dollar", symbol: "C$" },
  { code: "AUD", name: "Australian Dollar", symbol: "A$" },
]

interface PaymentRequest {
  amount: number
  currency: string
  client_email: string
  client_name: string
  description: string
  project_reference?: string
}

export default function ReceivePaymentPage() {
  const router = useRouter()
  const { user, createTransaction, fetchCurrentRate, currentRates } = useAppStore()

  const [step, setStep] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [paymentLink, setPaymentLink] = useState("")
  const [transactionId, setTransactionId] = useState("")

  const [formData, setFormData] = useState<PaymentRequest>({
    amount: 0,
    currency: "USD",
    client_email: "",
    client_name: "",
    description: "",
    project_reference: "",
  })

  const [calculation, setCalculation] = useState({
    originalAmount: 0,
    exchangeRate: 110.5,
    convertedAmount: 0,
    serviceFee: 0,
    netAmount: 0,
  })

  const handleInputChange = (field: keyof PaymentRequest, value: string | number) => {
    const updatedData = { ...formData, [field]: value }
    setFormData(updatedData)

    // Recalculate when amount or currency changes
    if (field === "amount" || field === "currency") {
      calculateAmount(updatedData.amount, updatedData.currency)
    }
  }

  const calculateAmount = async (amount: number, currency: string) => {
    if (!amount || amount <= 0) {
      setCalculation({
        originalAmount: 0,
        exchangeRate: 110.5,
        convertedAmount: 0,
        serviceFee: 0,
        netAmount: 0,
      })
      return
    }

    try {
      // Fetch current exchange rate
      await fetchCurrentRate(currency)
      const rate = currentRates[currency] || 110.5

      // Calculate using the API
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
        netAmount: response.data.converted_amount - response.data.service_fee_amount,
      })
    } catch (error) {
      console.error("Failed to calculate amount:", error)
      // Fallback calculation
      const convertedAmount = amount * 110.5
      const serviceFee = convertedAmount * 0.02
      setCalculation({
        originalAmount: amount,
        exchangeRate: 110.5,
        convertedAmount,
        serviceFee,
        netAmount: convertedAmount - serviceFee,
      })
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    // Validation
    if (!formData.amount || formData.amount <= 0) {
      setError("Please enter a valid amount")
      return
    }

    if (!validateEmail(formData.client_email)) {
      setError("Please enter a valid client email")
      return
    }

    if (!formData.client_name.trim()) {
      setError("Please enter client name")
      return
    }

    if (!formData.description.trim()) {
      setError("Please enter a description")
      return
    }

    setIsLoading(true)

    try {
      // Create transaction
      const transaction = await createTransaction({
        user_id: user!.id,
        amount: formData.amount,
        currency: formData.currency,
        transaction_type: "receive",
        recipient_email: formData.client_email,
        description: formData.description,
      })

      setTransactionId(transaction.transaction_id)

      // Generate payment link (in real app, this would be a proper payment gateway URL)
      const link = `${window.location.origin}/pay/${transaction.transaction_id}?amount=${formData.amount}&currency=${formData.currency}&email=${encodeURIComponent(formData.client_email)}`
      setPaymentLink(link)

      setStep(2)

      toast.success("Payment request created! Share the payment link with your client.")
    } catch (error) {
      setError(error instanceof Error ? error.message : "Failed to create payment request")
    } finally {
      setIsLoading(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success("Payment link copied to clipboard!")
  }

  const sendEmailToClient = () => {
    const subject = encodeURIComponent(`Payment Request - ${formData.description}`)
    const body = encodeURIComponent(`Hi ${formData.client_name},

I've created a payment request for our project: ${formData.description}

Amount: ${formData.currency} ${formatCurrency(formData.amount)}
You'll receive: ${formatCurrency(calculation.netAmount)} BDT

Please use this secure link to complete the payment:
${paymentLink}

Thank you!
${user?.first_name} ${user?.last_name}`)

    window.open(`mailto:${formData.client_email}?subject=${subject}&body=${body}`)
  }

  if (step === 2) {
    return (
      <DashboardLayout>
        <div className="max-w-2xl mx-auto space-y-6">
          <div className="text-center">
            <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Payment Request Created!</h1>
            <p className="text-gray-600">Share this payment link with your client to receive payment.</p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Payment Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm text-gray-500">Amount</Label>
                  <p className="font-semibold">
                    {formData.currency} {formatCurrency(formData.amount)}
                  </p>
                </div>
                <div>
                  <Label className="text-sm text-gray-500">You'll Receive</Label>
                  <p className="font-semibold text-green-600">{formatCurrency(calculation.netAmount)} BDT</p>
                </div>
                <div>
                  <Label className="text-sm text-gray-500">Client</Label>
                  <p className="font-semibold">{formData.client_name}</p>
                </div>
                <div>
                  <Label className="text-sm text-gray-500">Transaction ID</Label>
                  <p className="font-mono text-sm">{transactionId}</p>
                </div>
              </div>

              <Separator />

              <div>
                <Label className="text-sm text-gray-500">Description</Label>
                <p>{formData.description}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <LinkIcon className="w-5 h-5 mr-2" />
                Payment Link
              </CardTitle>
              <CardDescription>Share this secure link with your client</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2">
                <Input value={paymentLink} readOnly className="font-mono text-sm" />
                <Button variant="outline" size="sm" onClick={() => copyToClipboard(paymentLink)}>
                  <Copy className="w-4 h-4" />
                </Button>
              </div>

              <div className="flex space-x-2">
                <Button onClick={sendEmailToClient} className="flex-1">
                  <Mail className="w-4 h-4 mr-2" />
                  Send via Email
                </Button>
                <Button variant="outline" className="flex-1 bg-transparent">
                  <QrCode className="w-4 h-4 mr-2" />
                  Generate QR Code
                </Button>
              </div>
            </CardContent>
          </Card>

          <div className="flex space-x-4">
            <Button variant="outline" onClick={() => setStep(1)} className="flex-1">
              Create Another Request
            </Button>
            <Button asChild className="flex-1">
              <Link href="/transactions">
                View Transactions
                <ArrowRight className="w-4 h-4 ml-2" />
              </Link>
            </Button>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="max-w-2xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <Download className="w-8 h-8 mr-3 text-green-600" />
            Create Payment Request
          </h1>
          <p className="text-gray-600 mt-2">
            Generate a secure payment link for your client to pay you internationally.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <DollarSign className="w-5 h-5 mr-2" />
                Payment Amount
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="amount">Amount</Label>
                  <Input
                    id="amount"
                    type="number"
                    step="0.01"
                    min="1"
                    max="10000"
                    placeholder="0.00"
                    value={formData.amount || ""}
                    onChange={(e) => handleInputChange("amount", Number.parseFloat(e.target.value) || 0)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="currency">Currency</Label>
                  <Select value={formData.currency} onValueChange={(value) => handleInputChange("currency", value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {currencies.map((currency) => (
                        <SelectItem key={currency.code} value={currency.code}>
                          {currency.symbol} {currency.code} - {currency.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {formData.amount > 0 && (
                <Card className="bg-blue-50 border-blue-200">
                  <CardContent className="pt-4">
                    <div className="flex items-center mb-3">
                      <Calculator className="w-4 h-4 mr-2 text-blue-600" />
                      <span className="font-medium text-blue-900">Conversion Preview</span>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Amount:</span>
                        <span className="font-medium">
                          {formData.currency} {formatCurrency(calculation.originalAmount)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Exchange Rate:</span>
                        <span className="font-medium">
                          1 {formData.currency} = {formatCurrency(calculation.exchangeRate)} BDT
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Converted Amount:</span>
                        <span className="font-medium">{formatCurrency(calculation.convertedAmount)} BDT</span>
                      </div>
                      <div className="flex justify-between text-red-600">
                        <span>Service Fee (2%):</span>
                        <span className="font-medium">-{formatCurrency(calculation.serviceFee)} BDT</span>
                      </div>
                      <Separator />
                      <div className="flex justify-between text-lg font-bold text-green-600">
                        <span>You'll Receive:</span>
                        <span>{formatCurrency(calculation.netAmount)} BDT</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Client Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="client_name">Client Name</Label>
                <Input
                  id="client_name"
                  placeholder="John Doe"
                  value={formData.client_name}
                  onChange={(e) => handleInputChange("client_name", e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="client_email">Client Email</Label>
                <Input
                  id="client_email"
                  type="email"
                  placeholder="client@company.com"
                  value={formData.client_email}
                  onChange={(e) => handleInputChange("client_email", e.target.value)}
                  required
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Project Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Describe the work or service provided..."
                  value={formData.description}
                  onChange={(e) => handleInputChange("description", e.target.value)}
                  required
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="project_reference">Project Reference (Optional)</Label>
                <Input
                  id="project_reference"
                  placeholder="Project #123 or Invoice #456"
                  value={formData.project_reference}
                  onChange={(e) => handleInputChange("project_reference", e.target.value)}
                />
              </div>
            </CardContent>
          </Card>

          <Button type="submit" className="w-full" size="lg" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating Payment Request...
              </>
            ) : (
              <>
                Create Payment Request
                <ArrowRight className="ml-2 h-4 w-4" />
              </>
            )}
          </Button>
        </form>
      </div>
    </DashboardLayout>
  )
}
