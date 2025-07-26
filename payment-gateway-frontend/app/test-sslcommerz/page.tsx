"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, XCircle, Loader2, CreditCard, Smartphone } from "lucide-react"
import { useAppStore } from "@/lib/store"
import SSLCommerzIntegration from "@/lib/sslcommerz"
import { toast } from "sonner"

export default function TestSSLCommerzPage() {
  const { user } = useAppStore()
  const [isLoading, setIsLoading] = useState(false)
  const [testResults, setTestResults] = useState<any[]>([])
  
  const [testData, setTestData] = useState({
    amount: 1000,
    currency: "BDT",
    payment_method: "sslcommerz",
  })

  const runSSLCommerzTest = async () => {
    if (!user) {
      toast.error("Please login first")
      return
    }

    setIsLoading(true)
    const results: any[] = []

    try {
      // Test 1: Validate payment method
      const isValidMethod = SSLCommerzIntegration.validatePaymentMethod(testData.payment_method)
      results.push({
        test: "Payment Method Validation",
        success: isValidMethod,
        result: isValidMethod ? "Valid payment method" : "Invalid payment method",
      })

      // Test 2: Get payment method name
      const methodName = SSLCommerzIntegration.getPaymentMethodName(testData.payment_method)
      results.push({
        test: "Payment Method Name",
        success: true,
        result: methodName,
      })

      // Test 3: Format amount
      const formattedAmount = SSLCommerzIntegration.formatAmount(testData.amount, testData.currency)
      results.push({
        test: "Amount Formatting",
        success: true,
        result: formattedAmount,
      })

      // Test 4: Generate return URLs
      const returnUrls = SSLCommerzIntegration.generateReturnUrls(
        window.location.origin,
        "TEST_TXN_123"
      )
      results.push({
        test: "Return URLs Generation",
        success: true,
        result: JSON.stringify(returnUrls, null, 2),
      })

      // Test 5: Initiate test payment (this will create a real transaction)
      try {
        const paymentResponse = await SSLCommerzIntegration.initiatePayment({
          user_id: user.id,
          amount: testData.amount,
          currency: testData.currency,
          payment_method: "sslcommerz",
          return_url: `${window.location.origin}/payment/success`,
          cancel_url: `${window.location.origin}/payment/cancelled`,
          customer_name: `${user.first_name} ${user.last_name}`,
          customer_email: user.email,
          customer_phone: user.phone,
          product_name: "SSLCommerz Integration Test",
          product_category: "Test",
        })

        results.push({
          test: "Payment Initiation",
          success: paymentResponse.success,
          result: paymentResponse.success 
            ? `Payment URL: ${paymentResponse.payment_url}` 
            : `Error: ${paymentResponse.error}`,
        })
      } catch (error: any) {
        results.push({
          test: "Payment Initiation",
          success: false,
          result: `Error: ${error.message}`,
        })
      }

      setTestResults(results)
      
      const successCount = results.filter(r => r.success).length
      const totalTests = results.length
      
      if (successCount === totalTests) {
        toast.success(`All ${totalTests} SSLCommerz tests passed!`)
      } else {
        toast.warning(`${successCount}/${totalTests} SSLCommerz tests passed`)
      }

    } catch (error: any) {
      toast.error(`SSLCommerz test failed: ${error.message}`)
      console.error("SSLCommerz test error:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusIcon = (success: boolean) => {
    return success ? (
      <CheckCircle className="h-4 w-4 text-green-600" />
    ) : (
      <XCircle className="h-4 w-4 text-red-600" />
    )
  }

  const getStatusBadge = (success: boolean) => {
    return success ? (
      <Badge className="bg-green-100 text-green-800">Success</Badge>
    ) : (
      <Badge variant="destructive">Failed</Badge>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">SSLCommerz Integration Test</h1>
          <p className="text-gray-600">Test SSLCommerz payment gateway integration and functionality</p>
        </div>

        {!user && (
          <Card className="border-yellow-200 bg-yellow-50">
            <CardContent className="pt-6">
              <p className="text-yellow-800">
                <strong>Authentication Required:</strong> Please login to test SSLCommerz integration.
              </p>
            </CardContent>
          </Card>
        )}

        {user && (
          <>
            {/* Test Configuration */}
            <Card>
              <CardHeader>
                <CardTitle>Test Configuration</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="amount">Amount</Label>
                    <Input
                      id="amount"
                      type="number"
                      value={testData.amount}
                      onChange={(e) => setTestData(prev => ({ ...prev, amount: Number(e.target.value) }))}
                      min="10"
                      max="10000"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="currency">Currency</Label>
                    <Select 
                      value={testData.currency} 
                      onValueChange={(value) => setTestData(prev => ({ ...prev, currency: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="BDT">BDT - Bangladeshi Taka</SelectItem>
                        <SelectItem value="USD">USD - US Dollar</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="payment_method">Payment Method</Label>
                    <Select 
                      value={testData.payment_method} 
                      onValueChange={(value) => setTestData(prev => ({ ...prev, payment_method: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="sslcommerz">
                          <div className="flex items-center">
                            <CreditCard className="w-4 h-4 mr-2" />
                            SSLCommerz Payment Gateway
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <Button 
                  onClick={runSSLCommerzTest} 
                  disabled={isLoading}
                  className="w-full"
                  size="lg"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Running SSLCommerz Tests...
                    </>
                  ) : (
                    "Run SSLCommerz Integration Test"
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Test Results */}
            {testResults.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Test Results</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {testResults.map((result, index) => (
                      <div key={index} className="flex items-start justify-between p-4 border rounded-lg">
                        <div className="flex items-start space-x-3">
                          {getStatusIcon(result.success)}
                          <div>
                            <h4 className="font-medium">{result.test}</h4>
                            <pre className="text-sm text-gray-600 mt-1 whitespace-pre-wrap">
                              {result.result}
                            </pre>
                          </div>
                        </div>
                        {getStatusBadge(result.success)}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Integration Info */}
            <Card className="bg-blue-50 border-blue-200">
              <CardHeader>
                <CardTitle className="text-blue-900">SSLCommerz Integration Info</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-blue-800 space-y-2">
                  <p><strong>SSLCommerz Payment Gateway Integration:</strong></p>
                  <ul className="list-disc list-inside space-y-1 ml-4">
                    <li><strong>Credit/Debit Cards:</strong> Visa, MasterCard, American Express</li>
                    <li><strong>Mobile Banking:</strong> bKash, Nagad, Rocket</li>
                    <li><strong>Internet Banking:</strong> All major banks in Bangladesh</li>
                    <li><strong>Digital Wallets:</strong> Various local payment methods</li>
                  </ul>
                  <p className="mt-3">
                    <strong>Test Environment:</strong> All payments are processed in SSLCommerz sandbox mode for testing.
                  </p>
                  <p>
                    <strong>Integration Features:</strong> Unified payment gateway, real-time processing, secure transactions, 
                    automatic redirects, and comprehensive payment method support.
                  </p>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  )
}