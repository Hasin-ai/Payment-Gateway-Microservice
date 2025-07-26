/**
 * SSLCommerz Integration Helper
 * Handles SSLCommerz payment gateway integration for the frontend
 */

import { api } from "./api"

export interface SSLCommerzPaymentData {
  user_id: number
  amount: number
  currency: string
  payment_method: "sslcommerz"
  return_url: string
  cancel_url: string
  customer_name?: string
  customer_email?: string
  customer_phone?: string
  product_name?: string
  product_category?: string
}

export interface SSLCommerzResponse {
  success: boolean
  payment_url?: string
  transaction_id: string
  session_key?: string
  error?: string
}

export class SSLCommerzIntegration {
  /**
   * Initiate SSLCommerz payment
   */
  static async initiatePayment(data: SSLCommerzPaymentData): Promise<SSLCommerzResponse> {
    try {
      console.log("SSLCommerz: Initiating payment", { 
        amount: data.amount, 
        currency: data.currency, 
        method: data.payment_method 
      })

      const response = await api.initiatePayment({
        user_id: data.user_id,
        amount: data.amount,
        currency: data.currency,
        payment_method: data.payment_method,
        return_url: data.return_url,
        cancel_url: data.cancel_url,
      })

      console.log("SSLCommerz: Payment initiated successfully", response)

      return {
        success: true,
        payment_url: response.payment_url,
        transaction_id: response.transaction_id,
      }
    } catch (error: any) {
      console.error("SSLCommerz: Payment initiation failed", error)
      
      return {
        success: false,
        transaction_id: "",
        error: error.message || "Payment initiation failed",
      }
    }
  }

  /**
   * Handle payment success callback
   */
  static async handlePaymentSuccess(
    transactionId: string,
    paymentId?: string
  ): Promise<{ success: boolean; message: string }> {
    try {
      console.log("SSLCommerz: Handling payment success", { transactionId, paymentId })

      // Confirm payment with backend
      await api.confirmPayment({
        transaction_id: transactionId,
        payment_id: paymentId,
        status: "completed",
      })

      console.log("SSLCommerz: Payment confirmed successfully")

      return {
        success: true,
        message: "Payment completed successfully",
      }
    } catch (error: any) {
      console.error("SSLCommerz: Payment confirmation failed", error)
      
      return {
        success: false,
        message: error.message || "Payment confirmation failed",
      }
    }
  }

  /**
   * Handle payment failure/cancellation
   */
  static async handlePaymentFailure(
    transactionId: string,
    reason: string = "Payment cancelled by user"
  ): Promise<{ success: boolean; message: string }> {
    try {
      console.log("SSLCommerz: Handling payment failure", { transactionId, reason })

      // Update payment status to failed
      await api.confirmPayment({
        transaction_id: transactionId,
        status: "failed",
      })

      console.log("SSLCommerz: Payment failure recorded")

      return {
        success: true,
        message: "Payment cancellation recorded",
      }
    } catch (error: any) {
      console.error("SSLCommerz: Failed to record payment failure", error)
      
      return {
        success: false,
        message: error.message || "Failed to record payment failure",
      }
    }
  }

  /**
   * Get payment status
   */
  static async getPaymentStatus(transactionId: string) {
    try {
      console.log("SSLCommerz: Checking payment status", { transactionId })

      const status = await api.getPaymentStatus(transactionId)
      
      console.log("SSLCommerz: Payment status retrieved", status)

      return status
    } catch (error: any) {
      console.error("SSLCommerz: Failed to get payment status", error)
      throw error
    }
  }

  /**
   * Validate payment method for SSLCommerz
   */
  static validatePaymentMethod(method: string): boolean {
    return method.toLowerCase() === "sslcommerz"
  }

  /**
   * Get payment method display name
   */
  static getPaymentMethodName(method: string): string {
    return "SSLCommerz Payment Gateway"
  }

  /**
   * Format amount for display
   */
  static formatAmount(amount: number, currency: string = "BDT"): string {
    return new Intl.NumberFormat("en-BD", {
      style: "currency",
      currency: currency === "BDT" ? "BDT" : "USD",
      minimumFractionDigits: 2,
    }).format(amount)
  }

  /**
   * Generate return URLs with proper parameters
   */
  static generateReturnUrls(baseUrl: string, transactionId: string) {
    return {
      success_url: `${baseUrl}/payment/success?transaction_id=${transactionId}`,
      fail_url: `${baseUrl}/payment/cancelled?transaction_id=${transactionId}`,
      cancel_url: `${baseUrl}/payment/cancelled?transaction_id=${transactionId}&reason=cancelled`,
    }
  }
}

export default SSLCommerzIntegration