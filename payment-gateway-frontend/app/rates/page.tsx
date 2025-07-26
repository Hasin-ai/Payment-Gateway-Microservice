"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { TrendingUp, Calculator, RefreshCw, DollarSign, ArrowRightLeft, Clock, AlertCircle } from "lucide-react"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { useAppStore } from "@/lib/store"
import { api } from "@/lib/api"
import { formatCurrency } from "@/lib/utils"
import { toast } from "sonner"

const currencies = [
  { code: "USD", name: "US Dollar", symbol: "$", flag: "🇺🇸" },
  { code: "EUR", name: "Euro", symbol: "€", flag: "🇪🇺" },
  { code: "GBP", name: "British Pound", symbol: "£", flag: "🇬🇧" },
  { code: "CAD", name: "Canadian Dollar", symbol: "C$", flag: "🇨🇦" },
  { code: "AUD", name: "Australian Dollar", symbol: "A$", flag: "🇦🇺" },
  { code: "JPY", name: "Japanese Yen", symbol: "¥", flag: "🇯🇵" },
  { code: "CHF", name: "Swiss Franc", symbol: "CHF", flag: "🇨🇭" },
  { code: "SGD", name: "Singapore Dollar", symbol: "S$", flag: "🇸🇬" },
]

export default function ExchangeRatesPage() {
  const { fetchCurrentRate, currentRates } = useAppStore()
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())

  // Calculator state
  const [calculatorFrom, setCalculatorFrom] = useState("USD")
  const [calculatorTo, setCalculatorTo] = useState("BDT")
  const [calculatorAmount, setCalculatorAmount] = useState<number>(100)
  const [calculatorResult, setCalculatorResult] = useState<any>(null)
  const [isCalculating, setIsCalculating] = useState(false)

  useEffect(() => {
    // Fetch all exchange rates on mount
    refreshAllRates()

    // Set up auto-refresh every 30 seconds
    const interval = setInterval(() => {
      refreshAllRates()
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    // Recalculate when calculator inputs change
    if (calculatorAmount > 0) {
      calculateAmount()
    }
  }, [calculatorFrom, calculatorTo, calculatorAmount, currentRates])

  const refreshAllRates = async () => {
    setIsRefreshing(true)
    try {
      await Promise.all(currencies.map((currency) => fetchCurrentRate(currency.code)))
      setLastUpdated(new Date())
    } catch (error) {
      toast.error("Failed to refresh exchange rates")
    } finally {
      setIsRefreshing(false)
    }
  }

  const calculateAmount = async () => {
    if (!calculatorAmount || calculatorAmount <= 0) {
      setCalculatorResult(null)
      return
    }

    setIsCalculating(true)
    try {
      const response = await api.calculateAmount({
        from_currency: calculatorFrom,
        to_currency: calculatorTo,
        amount: calculatorAmount,
        service_fee_percentage: 2.0,
      })
      setCalculatorResult(response.data)
    } catch (error) {
      // Fallback calculation using current rates
      const fromRate = currentRates[calculatorFrom] || 1
      const toRate = calculatorTo === "BDT" ? 1 : currentRates[calculatorTo] || 1

      let convertedAmount: number
      if (calculatorTo === "BDT") {
        convertedAmount = calculatorAmount * fromRate
      } else if (calculatorFrom === "BDT") {
        convertedAmount = calculatorAmount / toRate
      } else {
        // Convert through BDT
        const bdtAmount = calculatorAmount * fromRate
        convertedAmount = bdtAmount / toRate
      }

      const serviceFee = convertedAmount * 0.02
      setCalculatorResult({
        original_amount: calculatorAmount,
        from_currency: calculatorFrom,
        to_currency: calculatorTo,
        exchange_rate: calculatorTo === "BDT" ? fromRate : fromRate / toRate,
        converted_amount: convertedAmount,
        service_fee_percentage: 2.0,
        service_fee_amount: serviceFee,
        total_amount: convertedAmount + serviceFee,
        calculation_time: new Date().toISOString(),
      })
    } finally {
      setIsCalculating(false)
    }
  }

  const swapCurrencies = () => {
    const temp = calculatorFrom
    setCalculatorFrom(calculatorTo)
    setCalculatorTo(temp)
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center">
              <TrendingUp className="w-8 h-8 mr-3 text-green-600" />
              Exchange Rates
            </h1>
            <p className="text-gray-600 mt-2">
              Live exchange rates and currency calculator for international payments.
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <div className="text-sm text-gray-500">Last updated: {lastUpdated.toLocaleTimeString()}</div>
            <Button variant="outline" onClick={refreshAllRates} disabled={isRefreshing}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Live Rates Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {currencies.map((currency) => {
            const rate = currentRates[currency.code] || 0
            return (
              <Card key={currency.code} className="hover:shadow-lg transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-2xl">{currency.flag}</span>
                      <div>
                        <CardTitle className="text-lg">{currency.code}</CardTitle>
                        <CardDescription className="text-xs">{currency.name}</CardDescription>
                      </div>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      Live
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-baseline space-x-1">
                      <span className="text-2xl font-bold">{formatCurrency(rate)}</span>
                      <span className="text-sm text-gray-500">BDT</span>
                    </div>
                    <div className="text-xs text-gray-500">
                      1 {currency.code} = {formatCurrency(rate)} BDT
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {/* Currency Calculator */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Calculator className="w-5 h-5 mr-2" />
              Currency Calculator
            </CardTitle>
            <CardDescription>Calculate exchange amounts with service fees included</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
              <div className="space-y-2">
                <Label>Amount</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={calculatorAmount || ""}
                  onChange={(e) => setCalculatorAmount(Number.parseFloat(e.target.value) || 0)}
                  placeholder="Enter amount"
                />
              </div>

              <div className="space-y-2">
                <Label>From</Label>
                <Select value={calculatorFrom} onValueChange={setCalculatorFrom}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="BDT">🇧🇩 BDT - Bangladeshi Taka</SelectItem>
                    {currencies.map((currency) => (
                      <SelectItem key={currency.code} value={currency.code}>
                        {currency.flag} {currency.code} - {currency.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex justify-center">
                <Button variant="outline" size="sm" onClick={swapCurrencies} className="h-10 w-10 p-0 bg-transparent">
                  <ArrowRightLeft className="h-4 w-4" />
                </Button>
              </div>

              <div className="space-y-2">
                <Label>To</Label>
                <Select value={calculatorTo} onValueChange={setCalculatorTo}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="BDT">🇧🇩 BDT - Bangladeshi Taka</SelectItem>
                    {currencies.map((currency) => (
                      <SelectItem key={currency.code} value={currency.code}>
                        {currency.flag} {currency.code} - {currency.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Button onClick={calculateAmount} disabled={isCalculating}>
                {isCalculating ? <RefreshCw className="h-4 w-4 animate-spin" /> : "Calculate"}
              </Button>
            </div>

            {calculatorResult && (
              <Card className="bg-blue-50 border-blue-200">
                <CardContent className="pt-6">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Original Amount:</span>
                      <span className="text-lg font-bold">
                        {formatCurrency(calculatorResult.original_amount)} {calculatorResult.from_currency}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span>Exchange Rate:</span>
                      <span>
                        1 {calculatorResult.from_currency} = {formatCurrency(calculatorResult.exchange_rate)}{" "}
                        {calculatorResult.to_currency}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span>Converted Amount:</span>
                      <span>
                        {formatCurrency(calculatorResult.converted_amount)} {calculatorResult.to_currency}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-red-600">
                      <span>Service Fee (2%):</span>
                      <span>
                        +{formatCurrency(calculatorResult.service_fee_amount)} {calculatorResult.to_currency}
                      </span>
                    </div>

                    <Separator />

                    <div className="flex items-center justify-between text-lg font-bold text-blue-900">
                      <span>Total Amount:</span>
                      <span>
                        {formatCurrency(calculatorResult.total_amount)} {calculatorResult.to_currency}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </CardContent>
        </Card>

        {/* Rate Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertCircle className="w-5 h-5 mr-2" />
              Rate Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold mb-2 flex items-center">
                  <Clock className="w-4 h-4 mr-2" />
                  Update Frequency
                </h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Rates update every 30 seconds automatically</li>
                  <li>• Manual refresh available anytime</li>
                  <li>• Real-time rates during business hours</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold mb-2 flex items-center">
                  <DollarSign className="w-4 h-4 mr-2" />
                  Service Fees
                </h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• 2% service fee on all conversions</li>
                  <li>• No hidden charges or markups</li>
                  <li>• Transparent fee calculation</li>
                </ul>
              </div>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-yellow-900">Important Note</h4>
                  <p className="text-sm text-yellow-700 mt-1">
                    Exchange rates are indicative and may vary slightly at the time of actual transaction. Final rates
                    are confirmed during payment processing.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
