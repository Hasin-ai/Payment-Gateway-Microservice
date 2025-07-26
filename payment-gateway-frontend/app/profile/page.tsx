"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  User,
  Shield,
  CreditCard,
  DollarSign,
  CheckCircle,
  AlertCircle,
  Edit,
  Save,
  X,
  Eye,
  EyeOff,
} from "lucide-react"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { useAppStore } from "@/lib/store"
import { api } from "@/lib/api"
import { formatCurrency } from "@/lib/utils"
import { toast } from "sonner"

export default function ProfilePage() {
  const { user, setUser } = useAppStore()
  const [isEditing, setIsEditing] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [paymentLimits, setPaymentLimits] = useState<any>(null)
  const [showChangePassword, setShowChangePassword] = useState(false)

  const [editForm, setEditForm] = useState({
    first_name: user?.first_name || "",
    last_name: user?.last_name || "",
    phone: user?.phone || "",
  })

  const [passwordForm, setPasswordForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  })

  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  })

  useEffect(() => {
    if (user) {
      fetchPaymentLimits()
      setEditForm({
        first_name: user.first_name,
        last_name: user.last_name,
        phone: user.phone,
      })
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

  const handleSaveProfile = async () => {
    setIsLoading(true)
    try {
      // In a real app, you would call an API to update the profile
      // For now, we'll just update the local state
      const updatedUser = {
        ...user!,
        ...editForm,
      }
      setUser(updatedUser)
      setIsEditing(false)
      toast.success("Profile updated successfully!")
    } catch (error) {
      toast.error("Failed to update profile. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleChangePassword = async () => {
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      toast.error("New passwords do not match.")
      return
    }

    if (passwordForm.new_password.length < 8) {
      toast.error("Password must be at least 8 characters long.")
      return
    }

    setIsLoading(true)
    try {
      // In a real app, you would call an API to change the password
      toast.success("Password changed successfully!")
      setShowChangePassword(false)
      setPasswordForm({
        current_password: "",
        new_password: "",
        confirm_password: "",
      })
    } catch (error) {
      toast.error("Failed to change password. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  const getLimitUsagePercentage = (used: number, limit: number) => {
    return Math.min((used / limit) * 100, 100)
  }

  const getLimitColor = (percentage: number) => {
    if (percentage >= 90) return "text-red-600"
    if (percentage >= 70) return "text-yellow-600"
    return "text-green-600"
  }

  if (!user) return null

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <User className="w-8 h-8 mr-3 text-blue-600" />
            Profile Settings
          </h1>
          <p className="text-gray-600 mt-2">Manage your account information and payment settings.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Profile Information */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center">
                    <User className="w-5 h-5 mr-2" />
                    Personal Information
                  </CardTitle>
                  {!isEditing ? (
                    <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
                      <Edit className="w-4 h-4 mr-2" />
                      Edit
                    </Button>
                  ) : (
                    <div className="flex space-x-2">
                      <Button variant="outline" size="sm" onClick={() => setIsEditing(false)}>
                        <X className="w-4 h-4" />
                      </Button>
                      <Button size="sm" onClick={handleSaveProfile} disabled={isLoading}>
                        <Save className="w-4 h-4 mr-2" />
                        Save
                      </Button>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>First Name</Label>
                    {isEditing ? (
                      <Input
                        value={editForm.first_name}
                        onChange={(e) => setEditForm((prev) => ({ ...prev, first_name: e.target.value }))}
                      />
                    ) : (
                      <p className="text-sm font-medium py-2">{user.first_name}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label>Last Name</Label>
                    {isEditing ? (
                      <Input
                        value={editForm.last_name}
                        onChange={(e) => setEditForm((prev) => ({ ...prev, last_name: e.target.value }))}
                      />
                    ) : (
                      <p className="text-sm font-medium py-2">{user.last_name}</p>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Email Address</Label>
                  <div className="flex items-center space-x-2">
                    <p className="text-sm font-medium py-2">{user.email}</p>
                    <Badge variant={user.email_verified ? "default" : "secondary"}>
                      {user.email_verified ? (
                        <>
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Verified
                        </>
                      ) : (
                        <>
                          <AlertCircle className="w-3 h-3 mr-1" />
                          Unverified
                        </>
                      )}
                    </Badge>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Phone Number</Label>
                  {isEditing ? (
                    <Input
                      value={editForm.phone}
                      onChange={(e) => setEditForm((prev) => ({ ...prev, phone: e.target.value }))}
                    />
                  ) : (
                    <p className="text-sm font-medium py-2">{user.phone}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label>Account Status</Label>
                  <Badge variant="default" className="capitalize">
                    {user.status}
                  </Badge>
                </div>

                <div className="space-y-2">
                  <Label>Member Since</Label>
                  <p className="text-sm text-gray-600">
                    {new Date(user.created_at).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Security Settings */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Shield className="w-5 h-5 mr-2" />
                  Security Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">Password</h3>
                    <p className="text-sm text-gray-600">Last changed: Never (or date if available)</p>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => setShowChangePassword(!showChangePassword)}>
                    Change Password
                  </Button>
                </div>

                {showChangePassword && (
                  <Card className="bg-gray-50">
                    <CardContent className="pt-6 space-y-4">
                      <div className="space-y-2">
                        <Label>Current Password</Label>
                        <div className="relative">
                          <Input
                            type={showPasswords.current ? "text" : "password"}
                            value={passwordForm.current_password}
                            onChange={(e) => setPasswordForm((prev) => ({ ...prev, current_password: e.target.value }))}
                          />
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="absolute right-0 top-0 h-full px-3"
                            onClick={() => setShowPasswords((prev) => ({ ...prev, current: !prev.current }))}
                          >
                            {showPasswords.current ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </Button>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label>New Password</Label>
                        <div className="relative">
                          <Input
                            type={showPasswords.new ? "text" : "password"}
                            value={passwordForm.new_password}
                            onChange={(e) => setPasswordForm((prev) => ({ ...prev, new_password: e.target.value }))}
                          />
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="absolute right-0 top-0 h-full px-3"
                            onClick={() => setShowPasswords((prev) => ({ ...prev, new: !prev.new }))}
                          >
                            {showPasswords.new ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </Button>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label>Confirm New Password</Label>
                        <div className="relative">
                          <Input
                            type={showPasswords.confirm ? "text" : "password"}
                            value={passwordForm.confirm_password}
                            onChange={(e) => setPasswordForm((prev) => ({ ...prev, confirm_password: e.target.value }))}
                          />
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="absolute right-0 top-0 h-full px-3"
                            onClick={() => setShowPasswords((prev) => ({ ...prev, confirm: !prev.confirm }))}
                          >
                            {showPasswords.confirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </Button>
                        </div>
                      </div>

                      <div className="flex space-x-2">
                        <Button onClick={handleChangePassword} disabled={isLoading}>
                          Update Password
                        </Button>
                        <Button variant="outline" onClick={() => setShowChangePassword(false)}>
                          Cancel
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Payment Limits & Settings */}
          <div className="space-y-6">
            {/* Payment Limits */}
            {paymentLimits && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <DollarSign className="w-5 h-5 mr-2" />
                    Payment Limits
                  </CardTitle>
                  <CardDescription>Your current payment limits and usage</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Daily Limit</span>
                      <span
                        className={getLimitColor(
                          getLimitUsagePercentage(paymentLimits.daily_used, paymentLimits.daily_limit),
                        )}
                      >
                        ${formatCurrency(paymentLimits.daily_used)} / ${formatCurrency(paymentLimits.daily_limit)}
                      </span>
                    </div>
                    <Progress
                      value={getLimitUsagePercentage(paymentLimits.daily_used, paymentLimits.daily_limit)}
                      className="h-2"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Monthly Limit</span>
                      <span
                        className={getLimitColor(
                          getLimitUsagePercentage(paymentLimits.monthly_used, paymentLimits.monthly_limit),
                        )}
                      >
                        ${formatCurrency(paymentLimits.monthly_used)} / ${formatCurrency(paymentLimits.monthly_limit)}
                      </span>
                    </div>
                    <Progress
                      value={getLimitUsagePercentage(paymentLimits.monthly_used, paymentLimits.monthly_limit)}
                      className="h-2"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Yearly Limit</span>
                      <span
                        className={getLimitColor(
                          getLimitUsagePercentage(paymentLimits.yearly_used, paymentLimits.yearly_limit),
                        )}
                      >
                        ${formatCurrency(paymentLimits.yearly_used)} / ${formatCurrency(paymentLimits.yearly_limit)}
                      </span>
                    </div>
                    <Progress
                      value={getLimitUsagePercentage(paymentLimits.yearly_used, paymentLimits.yearly_limit)}
                      className="h-2"
                    />
                  </div>

                  <Button variant="outline" className="w-full bg-transparent" size="sm">
                    Request Limit Increase
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* PayPal Integration */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <CreditCard className="w-5 h-5 mr-2" />
                  PayPal Integration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">PayPal Account</p>
                    <p className="text-sm text-gray-600">{user.email}</p>
                  </div>
                  <Badge variant="outline">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Connected
                  </Badge>
                </div>

                <Separator />

                <div className="space-y-2">
                  <p className="text-sm font-medium">Account Status</p>
                  <Badge variant="default">Verified</Badge>
                </div>

                <Button variant="outline" className="w-full bg-transparent" size="sm">
                  Test PayPal Connection
                </Button>
              </CardContent>
            </Card>

            {/* Account Verification */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Shield className="w-5 h-5 mr-2" />
                  Account Verification
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Email Verification</span>
                    <Badge variant={user.email_verified ? "default" : "secondary"}>
                      {user.email_verified ? "Verified" : "Pending"}
                    </Badge>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm">Phone Verification</span>
                    <Badge variant="secondary">Pending</Badge>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm">Identity Verification</span>
                    <Badge variant="secondary">Not Required</Badge>
                  </div>
                </div>

                {!user.email_verified && (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Please verify your email address to unlock full account features.
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
