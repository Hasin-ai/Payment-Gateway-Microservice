"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  ArrowUpRight,
  ArrowDownLeft,
  DollarSign,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  Plus,
  Send,
  Download,
  RefreshCw,
} from "lucide-react"
import Link from "next/link"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { useAppStore } from "@/lib/store"
import { formatCurrency, formatDate } from "@/lib/utils"

export default function DashboardPage() {
  const { user, transactions, fetchTransactions, fetchCurrentRate, currentRates } = useAppStore()
  const [stats, setStats] = useState({
    totalReceived: 0,
    totalSent: 0,
    pendingTransactions: 0,
    completedTransactions: 0,
  })
  const [isRefreshing, setIsRefreshing] = useState(false)

  useEffect(() => {
    fetchTransactions()
    fetchCurrentRate("USD")
  }, [fetchTransactions, fetchCurrentRate])

  useEffect(() => {
    // Calculate stats from transactions
    const received = transactions
      .filter((t) => t.transaction_type === "receive" && t.status === "completed")
      .reduce((sum, t) => sum + Number.parseFloat(t.amount), 0)

    const sent = transactions
      .filter((t) => t.transaction_type === "send" && t.status === "completed")
      .reduce((sum, t) => sum + Number.parseFloat(t.amount), 0)

    const pending = transactions.filter((t) => t.status === "pending").length
    const completed = transactions.filter((t) => t.status === "completed").length

    setStats({
      totalReceived: received,
      totalSent: sent,
      pendingTransactions: pending,
      completedTransactions: completed,
    })
  }, [transactions])

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      await Promise.all([fetchTransactions(), fetchCurrentRate("USD")])
    } finally {
      setIsRefreshing(false)
    }
  }

  const recentTransactions = transactions.slice(0, 5)
  const usdRate = currentRates.USD || 110.5

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case "pending":
        return <Clock className="h-4 w-4 text-yellow-600" />
      case "processing":
        return <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />
      default:
        return <AlertCircle className="h-4 w-4 text-red-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800"
      case "pending":
        return "bg-yellow-100 text-yellow-800"
      case "processing":
        return "bg-blue-100 text-blue-800"
      default:
        return "bg-red-100 text-red-800"
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600">Welcome back, {user?.first_name}! Here's your payment overview.</p>
          </div>
          <div className="flex items-center space-x-3">
            <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isRefreshing}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button asChild>
              <Link href="/receive">
                <Plus className="h-4 w-4 mr-2" />
                Create Payment Request
              </Link>
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Received</CardTitle>
              <ArrowDownLeft className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">${formatCurrency(stats.totalReceived)}</div>
              <p className="text-xs text-muted-foreground">≈ {formatCurrency(stats.totalReceived * usdRate)} BDT</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Sent</CardTitle>
              <ArrowUpRight className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">${formatCurrency(stats.totalSent)}</div>
              <p className="text-xs text-muted-foreground">≈ {formatCurrency(stats.totalSent * usdRate)} BDT</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending</CardTitle>
              <Clock className="h-4 w-4 text-yellow-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.pendingTransactions}</div>
              <p className="text-xs text-muted-foreground">Awaiting processing</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.completedTransactions}</div>
              <p className="text-xs text-muted-foreground">Successfully processed</p>
            </CardContent>
          </Card>
        </div>

        {/* Exchange Rate Widget */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="h-5 w-5 mr-2" />
              Current Exchange Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold">1 USD = {formatCurrency(usdRate)} BDT</div>
                <p className="text-sm text-muted-foreground">Last updated: {new Date().toLocaleTimeString()}</p>
              </div>
              <Button variant="outline" asChild>
                <Link href="/rates">View All Rates</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Transactions */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Transactions</CardTitle>
              <CardDescription>Your latest payment activities</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentTransactions.length > 0 ? (
                  recentTransactions.map((transaction) => (
                    <div
                      key={transaction.id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="flex-shrink-0">
                          {transaction.transaction_type === "receive" ? (
                            <ArrowDownLeft className="h-5 w-5 text-green-600" />
                          ) : (
                            <ArrowUpRight className="h-5 w-5 text-blue-600" />
                          )}
                        </div>
                        <div>
                          <p className="font-medium">
                            {transaction.transaction_type === "receive" ? "Received" : "Sent"} ${transaction.amount}
                          </p>
                          <p className="text-sm text-gray-500">{transaction.recipient_email || "N/A"}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge className={getStatusColor(transaction.status)}>
                          {getStatusIcon(transaction.status)}
                          <span className="ml-1 capitalize">{transaction.status}</span>
                        </Badge>
                        <p className="text-xs text-gray-500 mt-1">{formatDate(transaction.created_at)}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-500">No transactions yet</p>
                    <Button className="mt-4" asChild>
                      <Link href="/receive">Create Your First Payment Request</Link>
                    </Button>
                  </div>
                )}
              </div>
              {recentTransactions.length > 0 && (
                <div className="mt-4 pt-4 border-t">
                  <Button variant="outline" className="w-full bg-transparent" asChild>
                    <Link href="/transactions">View All Transactions</Link>
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>Common tasks to get you started</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Button className="w-full justify-start" asChild>
                  <Link href="/receive">
                    <Download className="h-4 w-4 mr-2" />
                    Create Payment Request
                  </Link>
                </Button>
                <Button variant="outline" className="w-full justify-start bg-transparent" asChild>
                  <Link href="/send">
                    <Send className="h-4 w-4 mr-2" />
                    Send International Payment
                  </Link>
                </Button>
                <Button variant="outline" className="w-full justify-start bg-transparent" asChild>
                  <Link href="/rates">
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Check Exchange Rates
                  </Link>
                </Button>
                <Button variant="outline" className="w-full justify-start bg-transparent" asChild>
                  <Link href="/profile">
                    <DollarSign className="h-4 w-4 mr-2" />
                    View Payment Limits
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}
