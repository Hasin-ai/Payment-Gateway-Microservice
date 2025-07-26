import { create } from "zustand"
import { persist } from "zustand/middleware"
import { api, type User, type Transaction, type PaymentLimits, type Notification } from "@/lib/api"

interface AppState {
  // Authentication
  user: User | null
  token: string | null
  isAuthenticated: boolean

  // Transactions
  transactions: Transaction[]
  currentTransaction: Transaction | null
  paymentLimits: PaymentLimits | null

  // Exchange Rates
  currentRates: Record<string, number>

  // Notifications
  notifications: Notification[]
  unreadCount: number

  // UI State
  isLoading: boolean
  error: string | null
  sidebarOpen: boolean
}

interface AppActions {
  // Authentication
  login: (credentials: { email: string; password: string }) => Promise<void>
  logout: () => void
  setUser: (user: User) => void
  initializeAuth: () => void

  // Transactions
  fetchTransactions: () => Promise<void>
  createTransaction: (data: any) => Promise<Transaction>
  setCurrentTransaction: (transaction: Transaction | null) => void

  // Exchange Rates
  fetchCurrentRate: (currency: string) => Promise<void>

  // Notifications
  fetchNotifications: () => Promise<void>
  markAsRead: (notificationId: number) => Promise<void>

  // Payment Limits
  fetchPaymentLimits: () => Promise<void>

  // UI State
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setSidebarOpen: (open: boolean) => void
}

export const useAppStore = create<AppState & AppActions>()(
  persist(
    (set, get) => ({
      // Initial State
      user: null,
      token: null,
      isAuthenticated: false,
      transactions: [],
      currentTransaction: null,
      paymentLimits: null,
      currentRates: {},
      notifications: [],
      unreadCount: 0,
      isLoading: false,
      error: null,
      sidebarOpen: false,

      // Authentication Actions
      login: async (credentials) => {
        try {
          set({ isLoading: true, error: null })
          const response = await api.login(credentials)
          
          // Set the token in the API client
          api.setToken(response.access_token)
          
          set({
            user: response.user,
            token: response.access_token,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : "Login failed",
            isLoading: false,
          })
          throw error
        }
      },

      logout: () => {
        api.clearToken()
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          transactions: [],
          currentTransaction: null,
          paymentLimits: null,
          notifications: [],
          unreadCount: 0,
        })
      },

      setUser: (user) => set({ user }),

      // Initialize authentication from persisted state
      initializeAuth: () => {
        const { token, user } = get()
        if (token && user) {
          api.setToken(token)
          set({ isAuthenticated: true })
        }
      },

      // Transaction Actions
      fetchTransactions: async () => {
        try {
          set({ isLoading: true })
          const transactions = await api.getTransactions()
          set({ transactions, isLoading: false })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : "Failed to fetch transactions",
            isLoading: false,
          })
        }
      },

      createTransaction: async (data) => {
        try {
          set({ isLoading: true })
          const transaction = await api.createTransaction(data)
          set((state) => ({
            transactions: [transaction, ...state.transactions],
            currentTransaction: transaction,
            isLoading: false,
          }))
          return transaction
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : "Failed to create transaction",
            isLoading: false,
          })
          throw error
        }
      },

      setCurrentTransaction: (transaction) => set({ currentTransaction: transaction }),

      // Exchange Rate Actions
      fetchCurrentRate: async (currency) => {
        try {
          const response = await api.getCurrentRate(currency)
          set((state) => ({
            currentRates: {
              ...state.currentRates,
              [currency]: response.data.rate_to_bdt,
            },
          }))
        } catch (error) {
          console.error("Failed to fetch exchange rate:", error)
        }
      },

      // Notification Actions
      fetchNotifications: async () => {
        const { user } = get()
        if (!user) return

        try {
          const notifications = await api.getNotifications(user.id)
          const unreadCount = notifications.filter((n) => !n.read).length
          set({ notifications, unreadCount })
        } catch (error) {
          console.error("Failed to fetch notifications:", error)
        }
      },

      markAsRead: async (notificationId) => {
        try {
          await api.markAsRead(notificationId)
          set((state) => ({
            notifications: state.notifications.map((n) => (n.id === notificationId ? { ...n, read: true } : n)),
            unreadCount: Math.max(0, state.unreadCount - 1),
          }))
        } catch (error) {
          console.error("Failed to mark notification as read:", error)
        }
      },

      // Payment Limits
      fetchPaymentLimits: async () => {
        const { user } = get()
        if (!user) return

        try {
          const limits = await api.getUserLimits(user.id)
          set({ paymentLimits: limits })
        } catch (error) {
          console.error("Failed to fetch payment limits:", error)
        }
      },

      // UI Actions
      setLoading: (isLoading) => set({ isLoading }),
      setError: (error) => set({ error }),
      setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
    }),
    {
      name: "payment-gateway-store",
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
)
