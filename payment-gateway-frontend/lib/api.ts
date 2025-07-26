const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8080"

class ApiClient {
  private baseURL: string
  private token: string | null = null

  constructor(baseURL: string) {
    this.baseURL = baseURL
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("access_token")
    }
  }

  setToken(token: string) {
    this.token = token
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", token)
      // Also set as cookie for middleware
      document.cookie = `access_token=${token}; path=/; max-age=86400; SameSite=Lax`
    }
  }

  clearToken() {
    this.token = null
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token")
      // Also clear cookie
      document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT"
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    }

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error("API Error:", error)
      throw error
    }
  }

  // Authentication
  async register(data: RegisterData): Promise<User> {
    return this.request<User>("/api/users/register", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>("/api/users/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    })
    this.setToken(response.access_token)
    return response
  }

  // Transactions
  async createTransaction(data: TransactionData): Promise<Transaction> {
    return this.request<Transaction>("/api/transactions/create", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async getTransactions(): Promise<Transaction[]> {
    return this.request<Transaction[]>("/api/transactions/list")
  }

  async getTransaction(id: string): Promise<Transaction> {
    return this.request<Transaction>(`/api/transactions/${id}`)
  }

  async getUserLimits(userId: number): Promise<PaymentLimits> {
    return this.request<PaymentLimits>(`/api/transactions/limits/${userId}`)
  }

  // Payments
  async initiatePayment(data: PaymentData): Promise<PaymentResponse> {
    return this.request<PaymentResponse>("/api/payments/initiate", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async getPaymentStatus(transactionId: string): Promise<PaymentStatus> {
    return this.request<PaymentStatus>(`/api/payments/status/${transactionId}`)
  }

  async confirmPayment(data: PaymentConfirmData): Promise<PaymentConfirmResponse> {
    return this.request<PaymentConfirmResponse>("/api/payments/confirm", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async refundPayment(data: RefundData): Promise<RefundResponse> {
    return this.request<RefundResponse>("/api/payments/refund", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  // Exchange Rates
  async getCurrentRate(currency: string): Promise<ExchangeRateResponse> {
    return this.request<ExchangeRateResponse>(`/api/rates/api/v1/rates/current?currency=${currency}`)
  }

  async calculateAmount(data: CalculationData): Promise<CalculationResponse> {
    return this.request<CalculationResponse>("/api/rates/api/v1/rates/calculate", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  // Notifications
  async getNotifications(userId: number): Promise<Notification[]> {
    return this.request<Notification[]>(`/api/notifications/list/${userId}`)
  }

  async markAsRead(notificationId: number): Promise<void> {
    return this.request<void>(`/api/notifications/${notificationId}/read`, {
      method: "PUT",
    })
  }

  async sendNotification(data: NotificationData): Promise<NotificationResponse> {
    return this.request<NotificationResponse>("/api/notifications/send", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async getNotificationStats(): Promise<NotificationStats> {
    return this.request<NotificationStats>("/api/notifications/stats")
  }

  // System Health
  async getSystemHealth(): Promise<HealthStatus> {
    return this.request<HealthStatus>("/health")
  }

  // Admin Service
  async getDashboardStats(): Promise<AdminStats> {
    return this.request<AdminStats>("/api/admin/api/v1/admin/dashboard/stats")
  }

  async getDashboardMetrics(): Promise<AdminMetrics> {
    return this.request<AdminMetrics>("/api/admin/api/v1/admin/dashboard/metrics")
  }

  async getAnalyticsDashboard(): Promise<AnalyticsDashboard> {
    return this.request<AnalyticsDashboard>("/api/admin/api/v1/admin/analytics/dashboard")
  }

  async getUsers(): Promise<User[]> {
    return this.request<User[]>("/api/admin/api/v1/admin/users/")
  }

  async updateUserStatus(userId: number, status: string): Promise<void> {
    return this.request<void>(`/api/admin/api/v1/admin/users/${userId}/status`, {
      method: "POST",
      body: JSON.stringify({ status }),
    })
  }

  // Audit Service
  async logAuditEvent(data: AuditData): Promise<void> {
    return this.request<void>("/api/audit/log", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async getAuditLogs(params?: AuditQueryParams): Promise<AuditLog[]> {
    const queryString = params ? `?${new URLSearchParams(params as any).toString()}` : ""
    return this.request<AuditLog[]>(`/api/audit/logs${queryString}`)
  }
}

export const api = new ApiClient(API_BASE_URL)

// Types
export interface RegisterData {
  email: string
  password: string
  first_name: string
  last_name: string
  phone: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  phone: string
  status: string
  role: string
  email_verified: boolean
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface TransactionData {
  user_id: number
  amount: number
  currency: string
  transaction_type: "send" | "receive"
  recipient_email?: string
  description: string
}

export interface Transaction {
  id: number
  transaction_id: string
  user_id: number
  amount: string
  currency: string
  converted_amount: string
  exchange_rate: string
  fees: string
  net_amount: string
  transaction_type: "send" | "receive"
  status: "pending" | "processing" | "completed" | "failed"
  payment_method: string | null
  recipient_email: string
  recipient_name: string | null
  description: string
  created_at: string
  updated_at: string
}

export interface PaymentData {
  user_id: number
  amount: number
  currency: string
  payment_method: string
  return_url: string
  cancel_url: string
}

export interface PaymentResponse {
  id: number
  transaction_id: string
  amount: string
  currency: string
  payment_method: string
  status: string
  payment_url: string
  created_at: string
}

export interface PaymentStatus {
  status: string
  transaction_id: string
  payment_id?: string
}

export interface PaymentConfirmData {
  transaction_id: string
  payment_id?: string
  status: string
}

export interface PaymentConfirmResponse {
  success: boolean
  message: string
  transaction_id: string
}

export interface RefundData {
  transaction_id: string
  amount?: number
  reason: string
}

export interface RefundResponse {
  success: boolean
  message: string
  refund_id: string
  amount: number
}

export interface PaymentLimits {
  daily_limit: number
  daily_used: number
  monthly_limit: number
  monthly_used: number
  yearly_limit: number
  yearly_used: number
}

export interface ExchangeRateResponse {
  message: string
  data: {
    currency_code: string
    rate_to_bdt: number
    source: string
    last_updated: string
    expires_at: string
    is_active: boolean
  }
}

export interface CalculationData {
  from_currency: string
  to_currency: string
  amount: number
  service_fee_percentage: number
}

export interface CalculationResponse {
  message: string
  data: {
    original_amount: number
    from_currency: string
    to_currency: string
    exchange_rate: number
    converted_amount: number
    service_fee_percentage: number
    service_fee_amount: number
    total_amount: number
    calculation_time: string
  }
}

export interface Notification {
  id: number
  user_id: number
  title: string
  message: string
  type: "payment" | "security" | "system" | "promotion"
  read: boolean
  created_at: string
  action_url?: string
}

export interface HealthStatus {
  gateway: string
  services: Record<
    string,
    {
      status: string
      response_time: number
    }
  >
}

export interface NotificationData {
  user_id: number
  title: string
  message: string
  channels: string[]
  priority?: number
}

export interface NotificationResponse {
  message: string
  notification_ids: number[]
}

export interface NotificationStats {
  total_sent: number
  total_delivered: number
  total_failed: number
  delivery_rate: number
}

export interface AdminStats {
  total_users: number
  total_transactions: number
  total_volume: number
  success_rate: number
}

export interface AdminMetrics {
  daily_transactions: number
  daily_volume: number
  active_users: number
  system_health: string
}

export interface AnalyticsDashboard {
  transaction_trends: Array<{
    date: string
    count: number
    volume: number
  }>
  currency_distribution: Array<{
    currency: string
    count: number
    percentage: number
  }>
  user_growth: Array<{
    date: string
    new_users: number
    total_users: number
  }>
}

export interface AuditData {
  user_id?: number
  action: string
  service_name: string
  details: Record<string, any>
}

export interface AuditLog {
  id: number
  user_id: number | null
  action: string
  service_name: string
  details: Record<string, any>
  ip_address: string | null
  user_agent: string | null
  created_at: string
}

export interface AuditQueryParams {
  user_id?: number
  action?: string
  service_name?: string
  start_date?: string
  end_date?: string
  limit?: number
  offset?: number
}
