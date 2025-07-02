# Payment Service API Documentation

## Overview
This document provides sample inputs and outputs for all API endpoints in the Payment Gateway Payment Service.

**Base URL**: `http://localhost:8000`

## Table of Contents
- [Health & System Endpoints](#health--system-endpoints)
- [SSLCommerz Endpoints](#sslcommerz-endpoints)
- [PayPal Endpoints](#paypal-endpoints)
- [Webhook Endpoints](#webhook-endpoints)
- [Error Responses](#error-responses)

---

## Health & System Endpoints

### Health Check
Check service health status.

**Endpoint**: `GET /health`

**Request**: No parameters required

**Response**:
```json
{
  "status": "healthy",
  "service": "payment-service",
  "version": "1.0.0"
}
```

### Service Information
Get basic service information.

**Endpoint**: `GET /`

**Request**: No parameters required

**Response**:
```json
{
  "message": "Payment Gateway Payment Service",
  "version": "1.0.0",
  "description": "Payment processing service for international transfers"
}
```

---

## SSLCommerz Endpoints

### Initiate Payment
Create a new SSLCommerz payment session for inbound payments.

**Endpoint**: `POST /api/v1/sslcommerz/initiate`

**Request Body**:
```json
{
  "transaction_id": 12345,
  "internal_tran_id": "TXN_001_20250702",
  "total_amount": 1500.50,
  "currency": "BDT",
  "product_name": "Mobile Recharge",
  "product_category": "Telecom",
  "customer_name": "John Doe",
  "customer_email": "john.doe@example.com",
  "customer_phone": "+8801712345678",
  "customer_address": "123 Main Street, Dhaka, Bangladesh"
}
```

**Success Response**:
```json
{
  "success": true,
  "message": "Payment session initiated successfully",
  "data": {
    "sessionkey": "D2A49C5A73A6D4B11A90E5C91E0A7C8B",
    "gateway_url": "https://sandbox.sslcommerz.com/gwprocess/v4/gw.php?Q=PAY&SESSIONKEY=D2A49C5A73A6D4B11A90E5C91E0A7C8B",
    "redirect_url": "https://sandbox.sslcommerz.com/gwprocess/v4/gw.php?Q=PAY&SESSIONKEY=D2A49C5A73A6D4B11A90E5C91E0A7C8B",
    "valid_till": "2025-07-02T18:30:00.000Z"
  },
  "timestamp": "2025-07-02T17:00:00.000Z"
}
```

### Get Payment Status
Retrieve the current status of an SSLCommerz payment.

**Endpoint**: `GET /api/v1/sslcommerz/status/{transaction_id}`

**Path Parameters**:
- `transaction_id` (integer): The transaction ID

**Example Request**: `GET /api/v1/sslcommerz/status/12345`

**Success Response**:
```json
{
  "success": true,
  "message": "Payment status retrieved successfully",
  "data": {
    "transaction_id": 12345,
    "internal_tran_id": "TXN_001_20250702",
    "sslcz_status": "VALID",
    "amount_matched": true,
    "validation_status": "SUCCESS",
    "payment_method": "VISA",
    "risk_assessment": "LOW",
    "processing_time": "2025-07-02T17:05:00.000Z"
  },
  "timestamp": "2025-07-02T17:10:00.000Z"
}
```

---

## PayPal Endpoints

### Initiate Payout
Create a PayPal payout for outbound payments.

**Endpoint**: `POST /api/v1/paypal/payout`

**Request Body**:
```json
{
  "transaction_id": 12346,
  "recipient_email": "recipient@example.com",
  "amount": 100.00,
  "currency": "USD",
  "note": "Monthly salary payment"
}
```

**Success Response**:
```json
{
  "success": true,
  "message": "Payout initiated successfully",
  "data": {
    "paypal_payout_id": "BATCH123456789",
    "transaction_id": 12346,
    "recipient_email": "recipient@example.com",
    "amount": 100.00,
    "currency": "USD",
    "status": "PENDING",
    "created_time": "2025-07-02T17:00:00.000Z",
    "links": [
      {
        "href": "https://api-m.sandbox.paypal.com/v1/payments/payouts/BATCH123456789",
        "rel": "self",
        "method": "GET"
      }
    ]
  },
  "timestamp": "2025-07-02T17:00:00.000Z"
}
```

### Get Payout Status
Retrieve the current status of a PayPal payout.

**Endpoint**: `GET /api/v1/paypal/status/{payout_id}`

**Path Parameters**:
- `payout_id` (string): The PayPal payout batch ID

**Example Request**: `GET /api/v1/paypal/status/BATCH123456789`

**Success Response**:
```json
{
  "success": true,
  "message": "Payout status retrieved successfully",
  "data": {
    "payout_batch_id": "BATCH123456789",
    "payout_item_id": "ITEM987654321",
    "transaction_id": "TXN_PAYPAL_12346",
    "transaction_status": "SUCCESS",
    "payout_batch_status": "SUCCESS",
    "amount": {
      "value": "100.00",
      "currency": "USD"
    },
    "fees": {
      "value": "2.50",
      "currency": "USD"
    },
    "time_processed": "2025-07-02T17:05:00.000Z",
    "errors": null
  },
  "timestamp": "2025-07-02T17:10:00.000Z"
}
```

---

## Webhook Endpoints

### SSLCommerz IPN Handler
Handle Instant Payment Notification (IPN) from SSLCommerz.

**Endpoint**: `POST /api/v1/webhooks/sslcommerz/ipn`

**Request Body** (Form Data):
```
val_id=2007071722281727JRaW7vGBBGI
store_id=finte68130d77bd2a7
store_passwd=finte68130d77bd2a7@ssl
tran_id=TXN_001_20250702
amount=1500.50
currency=BDT
bank_tran_id=200707172228127
status=VALID
tran_date=2025-07-02 17:05:00
card_type=VISA-Dutch Bangla
card_no=432149XXXXXX0087
card_issuer=BRAC BANK, LTD.
card_brand=VISA
card_issuer_country=Bangladesh
card_issuer_country_code=BD
risk_level=0
risk_title=Safe
```

**Success Response**:
```json
{
  "success": true,
  "message": "IPN processed successfully",
  "data": {
    "webhook_id": 1,
    "transaction_id": "TXN_001_20250702",
    "validation_status": "VALID",
    "payment_updated": true,
    "processed_at": "2025-07-02T17:05:30.000Z"
  },
  "timestamp": "2025-07-02T17:05:30.000Z"
}
```

### PayPal Webhook Handler
Handle webhook notifications from PayPal.

**Endpoint**: `POST /api/v1/webhooks/paypal`

**Headers**:
```
PAYPAL-TRANSMISSION-ID: 12345678-1234-1234-1234-123456789012
PAYPAL-CERT-ID: CERT123456789
PAYPAL-AUTH-ALGO: SHA256withRSA
PAYPAL-TRANSMISSION-SIG: base64_encoded_signature
```

**Request Body**:
```json
{
  "id": "WH-12345678901234567890123456789012",
  "event_version": "1.0",
  "create_time": "2025-07-02T17:05:00.000Z",
  "resource_type": "payouts",
  "event_type": "PAYMENT.PAYOUTS-ITEM.SUCCEEDED",
  "summary": "A payout item has succeeded",
  "resource": {
    "payout_item_id": "ITEM987654321",
    "transaction_id": "TXN_PAYPAL_12346",
    "payout_batch_id": "BATCH123456789",
    "payout_item": {
      "amount": {
        "value": "100.00",
        "currency": "USD"
      },
      "receiver": "recipient@example.com",
      "recipient_type": "EMAIL"
    },
    "time_processed": "2025-07-02T17:05:00.000Z",
    "payout_item_fee": {
      "value": "2.50",
      "currency": "USD"
    },
    "transaction_status": "SUCCESS"
  }
}
```

**Success Response**:
```json
{
  "success": true,
  "message": "Webhook processed successfully",
  "data": {
    "webhook_id": 2,
    "event_type": "PAYMENT.PAYOUTS-ITEM.SUCCEEDED",
    "payout_item_id": "ITEM987654321",
    "verification_status": "VERIFIED",
    "payment_updated": true,
    "processed_at": "2025-07-02T17:06:00.000Z"
  },
  "timestamp": "2025-07-02T17:06:00.000Z"
}
```

---

## Error Responses

### Validation Error
When request data is invalid.

**HTTP Status**: `400 Bad Request`

**Response**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": [
      {
        "field": "amount",
        "message": "Amount must be greater than 0"
      }
    ]
  },
  "timestamp": "2025-07-02T17:00:00.000Z"
}
```

### Payment Not Found
When requested payment record doesn't exist.

**HTTP Status**: `404 Not Found`

**Response**:
```json
{
  "success": false,
  "error": {
    "code": "PAYMENT_NOT_FOUND",
    "message": "Payment record not found",
    "details": {
      "transaction_id": 99999
    }
  },
  "timestamp": "2025-07-02T17:00:00.000Z"
}
```

### Service Error
When an internal service error occurs.

**HTTP Status**: `500 Internal Server Error`

**Response**:
```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An internal error occurred while processing the request",
    "details": {
      "error_id": "ERR_12345678",
      "support_message": "Please contact support with this error ID"
    }
  },
  "timestamp": "2025-07-02T17:00:00.000Z"
}
```

### Rate Limit Exceeded
When API rate limits are exceeded.

**HTTP Status**: `429 Too Many Requests`

**Response**:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "details": {
      "limit": 300,
      "window": "60 seconds",
      "retry_after": 45
    }
  },
  "timestamp": "2025-07-02T17:00:00.000Z"
}
```

---

## Authentication

### JWT Token Required
Some endpoints may require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### API Key Authentication
For service-to-service communication, include the API key in headers:

```
X-API-Key: your-api-key-here
```

---

## Rate Limiting

- **Limit**: 300 requests per minute
- **Window**: 60 seconds
- **Headers**: Rate limit information is included in response headers:
  ```
  X-RateLimit-Limit: 300
  X-RateLimit-Remaining: 299
  X-RateLimit-Reset: 1656789123
  ```

---

## Testing with cURL

### SSLCommerz Payment Initiation
```bash
curl -X POST http://localhost:8000/api/v1/sslcommerz/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": 12345,
    "internal_tran_id": "TXN_001_20250702",
    "total_amount": 1500.50,
    "currency": "BDT",
    "product_name": "Mobile Recharge",
    "product_category": "Telecom",
    "customer_name": "John Doe",
    "customer_email": "john.doe@example.com",
    "customer_phone": "+8801712345678",
    "customer_address": "123 Main Street, Dhaka, Bangladesh"
  }'
```

### PayPal Payout Initiation
```bash
curl -X POST http://localhost:8000/api/v1/paypal/payout \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": 12346,
    "recipient_email": "recipient@example.com",
    "amount": 100.00,
    "currency": "USD",
    "note": "Monthly salary payment"
  }'
```

### Health Check
```bash
curl -X GET http://localhost:8000/health
```

---

## Notes

1. **Timestamps**: All timestamps are in ISO 8601 format with UTC timezone
2. **Decimal Precision**: Currency amounts support up to 2 decimal places
3. **Transaction IDs**: Must be unique for each payment
4. **Currency Codes**: Use ISO 4217 currency codes (BDT, USD, etc.)
5. **Email Validation**: Email addresses are validated for proper format
6. **Phone Numbers**: Should include country code for international numbers

For more detailed API documentation, visit: `http://localhost:8000/docs`
