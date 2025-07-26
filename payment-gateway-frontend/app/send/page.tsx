"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Checkbox } from "@/components/ui/checkbox"
import { Send, DollarSign, Calculator, CreditCard, Shield, Clock, Loader2, ArrowRight, Globe, CheckCircle } from "lucide-react"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { useAppStore } from "@/lib/store"
import { api } from "@/lib/api"
import { formatCurrency, validateEmail } from "@/lib/utils"
import { toast } from "sonner"
import SSLCommerzIntegration from "@/lib/sslcommerz"

interface SendPaymentData {
  recipient_email: string
  amount: number
  currency: string
  purpose: string
  description: string
  urgent: boolean
}

export default function SendPaymentPage() {
  const router = useRouter()
  const { user, createTransaction, fetchCurrentRate, currentRates } = useAppStore()

  const [step, setStep] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [paymentLimits, setPaymentLimits] = useState<any>(null)

  const [formData, setFormData] = useState<SendPaymentData>({
    recipient_email: "",
    amount: 0,
    currency: "USD",
    purpose: "",
    description: "",
    urgent: false,
  })

  const [calculation, setCalculation] = useState({
    usdAmount: 0,
    bdtEquivalent: 0,
    serviceFee: 0,
    totalBdtRequired: 0,
    exchangeRate: 110.5,
  })

  const [paymentMethod, setPaymentMethod] = useState("sslcommerz")
  const [agreedToTerms, setAgreedToTerms] = useState(false)

  useEffect(() => {
    // Fetch user payment limits
    if (user) {
      fetchPaymentLimits()
    }
  }, [user])

  const fetchPaymentLimits = async () => {
    try {
      const limits = await api.getUserLimits(user!.id)
      setPaymentLimits(limits)
    } catch (error) {
      console.error("Failed to fetch payment limits:", error)
    }
  }

  const handleInputChange = (field: keyof SendPaymentData, value: string | number | boolean) => {
    const updatedData = { ...formData, [field]: value }
    setFormData(updatedData)

    // Recalculate when amount changes
    if (field === "amount") {
      calculateBdtAmount(updatedData.amount)
    }
  }

  const calculateBdtAmount = async (usdAmount: number) => {
    if (!usdAmount || usdAmount <= 0) {
      setCalculation({
        usdAmount: 0,
        bdtEquivalent: 0,
        serviceFee: 0,
        totalBdtRequired: 0,
        exchangeRate: 110.5,
      })
      return
    }

    try {
      // Fetch current exchange rate
      await fetchCurrentRate("USD")
      const rate = currentRates.USD || 110.5

      // Calculate using the API
      const response = await api.calculateAmount({
        from_currency: "USD",
        to_currency: "BDT",
        amount: usdAmount,
        service_fee_percentage: 2.0,
      })

      setCalculation({
        usdAmount: usdAmount,
        bdtEquivalent: response.data.converted_amount,
        serviceFee: response.data.service_fee_amount,
        totalBdtRequired: response.data.total_amount,
        exchangeRate: response.data.exchange_rate,
      })
    } catch (error) {
      console.error("Failed to calculate amount:", error)
      // Fallback calculation
      const bdtEquivalent = usdAmount * 110.5
      const serviceFee = bdtEquivalent * 0.02
      setCalculation({
        usdAmount: usdAmount,
        bdtEquivalent: bdtEquivalent,
        serviceFee: serviceFee,
        totalBdtRequired: bdtEquivalent + serviceFee,
        exchangeRate: 110.5,
      })
    }
  }

  const checkPaymentLimits = () => {
    if (!paymentLimits) return { valid: true, message: "" }

    const dailyRemaining = paymentLimits.daily_limit - paymentLimits.daily_used
    const monthlyRemaining = paymentLimits.monthly_limit - paymentLimits.monthly_used
    const yearlyRemaining = paymentLimits.yearly_limit - paymentLimits.yearly_used

    if (formData.amount > dailyRemaining) {
      return { valid: false, message: `Exceeds daily limit. Remaining: $${formatCurrency(dailyRemaining)}` }
    }
    if (formData.amount > monthlyRemaining) {
      return { valid: false, message: `Exceeds monthly limit. Remaining: $${formatCurrency(monthlyRemaining)}` }
    }
    if (formData.amount > yearlyRemaining) {
      return { valid: false, message: `Exceeds yearly limit. Remaining: $${formatCurrency(yearlyRemaining)}` }
    }

    return { valid: true, message: "" }
  }

  const handleStepOne = (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    // Validation
    if (!formData.amount || formData.amount <= 0) {
      setError("Please enter a valid amount")
      return
    }

    if (!validateEmail(formData.recipient_email)) {
      setError("Please enter a valid recipient email")
      return
    }

    if (!formData.purpose.trim()) {
      setError("Please enter the payment purpose")
      return
    }

    if (!formData.description.trim()) {
      setError("Please enter a description")
      return
    }

    // Check payment limits
    const limitCheck = checkPaymentLimits()
    if (!limitCheck.valid) {
      setError(limitCheck.message)
      return
    }

    setStep(2)
  }

  const handleFinalSubmit = async () => {
    if (!agreedToTerms) {
      setError("Please agree to the terms and conditions")
      return
    }

    setIsLoading(true)
    setError("")

    try {
      // Create transaction
      const transaction = await createTransaction({
        user_id: user!.id,
        amount: formData.amount,
        currency: formData.currency,
        transaction_type: "send",
        recipient_email: formData.recipient_email,
        description: formData.description,
      })

      // Generate return URLs
      const returnUrls = SSLCommerzIntegration.generateReturnUrls(
        window.location.origin,
        transaction.transaction_id
      )

      // Initiate payment using SSLCommerz integration
      const paymentResponse = await SSLCommerzIntegration.initiatePayment({
        user_id: user!.id,
        amount: calculation.totalBdtRequired,
        currency: "BDT",
        payment_method: "sslcommerz",
        return_url: returnUrls.success_url,
        cancel_url: returnUrls.cancel_url,
        customer_name: `${user.first_name} ${user.last_name}`,
        customer_email: user.email,
        customer_phone: user.phone,
        product_name: `International Payment - ${formData.description}`,
        product_category: "International Transfer",
      })

      if (paymentResponse.success && paymentResponse.payment_url) {
        toast.success("Payment initiated! Redirecting to SSLCommerz payment gateway...")
        
        // Small delay to show the toast
        setTimeout(() => {
          window.location.href = paymentResponse.payment_url!
        }, 1000)
      } else {
        throw new Error(paymentResponse.error || "Failed to get payment URL")
      }
    } catch (error) {
      console.error("Payment initiation error:", error)
      setError(error instanceof Error ? error.message : "Failed to initiate payment")
      toast.error("Failed to initiate payment. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  const getLimitUsagePercentage = (used: number, limit: number) => {
    return Math.min((used / limit) * 100, 100)
  }

  if (step === 2) {
    return (
      <DashboardLayout>
        <div className="max-w-2xl mx-auto space-y-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Confirm Payment</h1>
            <p className="text-gray-600 mt-2">Review your payment details and complete the transaction.</p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Payment Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm text-gray-500">Recipient</Label>
                  <p className="font-semibold">{formData.recipient_email}</p>
                </div>
                <div>
                  <Label className="text-sm text-gray-500">Amount to Send</Label>
                  <p className="font-semibold">${formatCurrency(formData.amount)}</p>
                </div>
                <div>
                  <Label className="text-sm text-gray-500">Purpose</Label>
                  <p className="font-semibold">{formData.purpose}</p>
                </div>
                <div>
                  <Label className="text-sm text-gray-500">Priority</Label>
                  <p className="font-semibold">{formData.urgent ? "Urgent" : "Standard"}</p>
                </div>
              </div>

              <Separator />

              <div>
                <Label className="text-sm text-gray-500">Description</Label>
                <p>{formData.description}</p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-blue-50 border-blue-200">
            <CardHeader>
              <CardTitle className="flex items-center text-blue-900">
                <Calculator className="w-5 h-5 mr-2" />
                Cost Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between">
                <span>USD Amount:</span>
                <span className="font-medium">${formatCurrency(calculation.usdAmount)}</span>
              </div>
              <div className="flex justify-between">
                <span>Exchange Rate:</span>
                <span className="font-medium">1 USD = {formatCurrency(calculation.exchangeRate)} BDT</span>
              </div>
              <div className="flex justify-between">
                <span>BDT Equivalent:</span>
                <span className="font-medium">{formatCurrency(calculation.bdtEquivalent)} BDT</span>
              </div>
              <div className="flex justify-between text-red-600">
                <span>Service Fee (2%):</span>
                <span className="font-medium">+{formatCurrency(calculation.serviceFee)} BDT</span>
              </div>
              <Separator />
              <div className="flex justify-between text-lg font-bold text-blue-900">
                <span>Total BDT Required:</span>
                <span>{formatCurrency(calculation.totalBdtRequired)} BDT</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <CreditCard className="w-5 h-5 mr-2" />
                Payment Method
              </CardTitle>
              <CardDescription>Secure payment processing via SSLCommerz</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border-2 border-blue-200 rounded-lg bg-blue-50">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
                    <CreditCard className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-blue-900">SSLCommerz Payment Gateway</h4>
                    <p className="text-sm text-blue-700">
                      Pay securely with Credit/Debit Cards, Mobile Banking, or Internet Banking
                    </p>
                  </div>
                </div>
                <div className="text-blue-600">
                  <CheckCircle className="w-6 h-6" />
                </div>
              </div>
              
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-sm text-gray-600">
                  <strong>Supported Payment Methods:</strong> Visa, MasterCard, American Express, 
                  bKash, Nagad, Rocket, Dutch-Bangla Bank, and other local payment methods
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-yellow-200 bg-yellow-50">
            <CardContent className="pt-6">
              <div className="flex items-start space-x-3">
                <Shield className="w-5 h-5 text-yellow-600 mt-0.5" />
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Checkbox id="terms" checked={agreedToTerms} onCheckedChange={setAgreedToTerms} />
                    <Label htmlFor="terms" className="text-sm cursor-pointer">
                      I agree to the terms and conditions and confirm that this payment is for legitimate business
                      purposes.
                    </Label>
                  </div>
                  <p className="text-xs text-yellow-700">
                    By proceeding, you acknowledge that international payments may be subject to additional verification
                    and compliance checks.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="flex space-x-4">
            <Button variant="outline" onClick={() => setStep(1)} className="flex-1">
              Back to Edit
            </Button>
            <Button
              onClick={handleFinalSubmit}
              className="flex-1"
              disabled={isLoading || !agreedToTerms}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  Pay {formatCurrency(calculation.totalBdtRequired)} BDT
                  <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
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
            <Send className="w-8 h-8 mr-3 text-blue-600" />
            Send International Payment
          </h1>
          <p className="text-gray-600 mt-2">
            Send USD payments to international suppliers using SSLCommerz secure payment gateway.
          </p>
        </div>

        {/* Payment Limits Overview */}
        {paymentLimits && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Shield className="w-5 h-5 mr-2" />
                Payment Limits
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Daily</span>
                    <span>
                      ${formatCurrency(paymentLimits.daily_used)} / ${formatCurrency(paymentLimits.daily_limit)}
                    </span>
                  </div>
                  <Progress value={getLimitUsagePercentage(paymentLimits.daily_used, paymentLimits.daily_limit)} />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Monthly</span>
                    <span>
                      ${formatCurrency(paymentLimits.monthly_used)} / ${formatCurrency(paymentLimits.monthly_limit)}
                    </span>
                  </div>
                  <Progress value={getLimitUsagePercentage(paymentLimits.monthly_used, paymentLimits.monthly_limit)} />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Yearly</span>
                    <span>
                      ${formatCurrency(paymentLimits.yearly_used)} / ${formatCurrency(paymentLimits.yearly_limit)}
                    </span>
                  </div>
                  <Progress value={getLimitUsagePercentage(paymentLimits.yearly_used, paymentLimits.yearly_limit)} />
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <form onSubmit={handleStepOne} className="space-y-6">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Globe className="w-5 h-5 mr-2" />
                Recipient Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="recipient_email">Recipient PayPal Email</Label>
                <Input
                  id="recipient_email"
                  type="email"
                  placeholder="supplier@company.com"
                  value={formData.recipient_email}
                  onChange={(e) => handleInputChange("recipient_email", e.target.value)}
                  required
                />
                <p className="text-xs text-gray-500">
                  The recipient must have a verified PayPal account to receive USD payments.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <DollarSign className="w-5 h-5 mr-2" />
                Payment Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="amount">Amount (USD)</Label>
                <Input
                  id="amount"
                  type="number"
                  step="0.01"
                  min="1"
                  max="50000"
                  placeholder="0.00"
                  value={formData.amount || ""}
                  onChange={(e) => handleInputChange("amount", Number.parseFloat(e.target.value) || 0)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="purpose">Payment Purpose</Label>
                <Select value={formData.purpose} onValueChange={(value) => handleInputChange("purpose", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select payment purpose" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="goods">Payment for Goods</SelectItem>
                    <SelectItem value="services">Payment for Services</SelectItem>
                    <SelectItem value="software">Software License</SelectItem>
                    <SelectItem value="consulting">Consulting Services</SelectItem>
                    <SelectItem value="subscription">Subscription Payment</SelectItem>
                    <SelectItem value="other">Other Business Payment</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Provide details about this payment..."
                  value={formData.description}
                  onChange={(e) => handleInputChange("description", e.target.value)}
                  required
                  rows={3}
                />
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="urgent"
                  checked={formData.urgent}
                  onCheckedChange={(checked) => handleInputChange("urgent", checked)}
                />
                <Label htmlFor="urgent" className="flex items-center cursor-pointer">
                  <Clock className="w-4 h-4 mr-2" />
                  Urgent Payment (Priority Processing)
                </Label>
              </div>

              {formData.amount > 0 && (
                <Card className="bg-green-50 border-green-200">
                  <CardContent className="pt-4">
                    <div className="flex items-center mb-3">
                      <Calculator className="w-4 h-4 mr-2 text-green-600" />
                      <span className="font-medium text-green-900">Cost Calculation</span>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>USD Amount:</span>
                        <span className="font-medium">${formatCurrency(calculation.usdAmount)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Exchange Rate:</span>
                        <span className="font-medium">1 USD = {formatCurrency(calculation.exchangeRate)} BDT</span>
                      </div>
                      <div className="flex justify-between">
                        <span>BDT Equivalent:</span>
                        <span className="font-medium">{formatCurrency(calculation.bdtEquivalent)} BDT</span>
                      </div>
                      <div className="flex justify-between text-red-600">
                        <span>Service Fee (2%):</span>
                        <span className="font-medium">+{formatCurrency(calculation.serviceFee)} BDT</span>
                      </div>
                      <Separator />
                      <div className="flex justify-between text-lg font-bold text-green-600">
                        <span>Total BDT Required:</span>
                        <span>{formatCurrency(calculation.totalBdtRequired)} BDT</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>

          <Button type="submit" className="w-full" size="lg">
            Continue to Payment
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </form>
      </div>
    </DashboardLayout>
  )
}
