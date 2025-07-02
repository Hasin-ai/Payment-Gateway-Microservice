# Admin Service API Samples

This document provides sample input and output for the endpoints in the Admin Service API.

## Dashboard API

### Get Dashboard Statistics

**Endpoint:** GET `/api/v1/admin/dashboard/stats`

**Parameters:**
- `period`: String (today, week, month, year)

**Sample Response:**
```json
{
  "period": "today",
  "date_range": {
    "start": "2023-06-15T00:00:00",
    "end": "2023-06-15T23:59:59"
  },
  "transactions": {
    "total_count": 120,
    "completed_count": 98,
    "pending_count": 15,
    "failed_count": 7,
    "total_volume_bdt": "532450.75",
    "total_volume_usd": "4875.25",
    "average_transaction_size_usd": "40.63"
  },
  "revenue": {
    "service_fees_bdt": "10649.02",
    "service_fees_usd": "97.51"
  },
  "users": {
    "new_registrations": 15,
    "active_users": 87,
    "verified_users": 72,
    "total_users": 456
  },
  "system_health": {
    "uptime_percentage": 99.98,
    "average_response_time_ms": 145,
    "error_rate_percentage": 0.12
  }
}
```

### Get Platform Metrics

**Endpoint:** GET `/api/v1/admin/dashboard/metrics`

**Sample Response:**
```json
{
  "total_processed_volume_bdt": "23456789.50",
  "total_processed_volume_usd": "214852.65",
  "success_rate_percentage": 97.8,
  "average_processing_time_minutes": 2.5,
  "most_popular_currencies": [
    {
      "currency_code": "USD",
      "transaction_count": 12450,
      "total_volume": "214852.65",
      "percentage_of_total": 45.6
    },
    {
      "currency_code": "BDT",
      "transaction_count": 10230,
      "total_volume": "23456789.50",
      "percentage_of_total": 32.8
    },
    {
      "currency_code": "EUR",
      "transaction_count": 5430,
      "total_volume": "153420.25",
      "percentage_of_total": 21.6
    }
  ],
  "top_recipients": [
    {
      "recipient_email": "business1@example.com",
      "transaction_count": 532,
      "total_amount_usd": "45632.75"
    },
    {
      "recipient_email": "business2@example.com",
      "transaction_count": 438,
      "total_amount_usd": "38756.80"
    },
    {
      "recipient_email": "business3@example.com",
      "transaction_count": 387,
      "total_amount_usd": "31245.95"
    }
  ]
}
```

### Get System Alerts

**Endpoint:** GET `/api/v1/admin/dashboard/alerts`

**Sample Response:**
```json
[
  {
    "id": 1,
    "type": "security",
    "severity": "high",
    "message": "Multiple failed login attempts detected from IP 192.168.1.123",
    "timestamp": "2023-06-15T14:35:22",
    "resolved": false
  },
  {
    "id": 2,
    "type": "performance",
    "severity": "medium",
    "message": "Transaction processing times increased by 25%",
    "timestamp": "2023-06-15T10:12:18",
    "resolved": true
  },
  {
    "id": 3,
    "type": "system",
    "severity": "low",
    "message": "Database storage usage at 75% capacity",
    "timestamp": "2023-06-15T08:45:30",
    "resolved": false
  }
]
```

## Settings API

### List All Settings

**Endpoint:** GET `/api/v1/admin/settings`

**Sample Response:**
```json
[
  {
    "id": 1,
    "setting_key": "payment.min_amount",
    "setting_value": "5",
    "setting_type": "number",
    "description": "Minimum transaction amount in USD",
    "is_encrypted": false,
    "created_at": "2023-05-01T10:00:00",
    "updated_at": "2023-05-01T10:00:00"
  },
  {
    "id": 2,
    "setting_key": "payment.max_amount",
    "setting_value": "10000",
    "setting_type": "number",
    "description": "Maximum transaction amount in USD",
    "is_encrypted": false,
    "created_at": "2023-05-01T10:00:00",
    "updated_at": "2023-05-15T14:30:00"
  },
  {
    "id": 3,
    "setting_key": "notification.email_enabled",
    "setting_value": "true",
    "setting_type": "boolean",
    "description": "Enable email notifications",
    "is_encrypted": false,
    "created_at": "2023-05-01T10:00:00",
    "updated_at": "2023-05-01T10:00:00"
  }
]
```

### Create Setting

**Endpoint:** POST `/api/v1/admin/settings`

**Sample Request:**
```json
{
  "setting_key": "security.max_login_attempts",
  "setting_value": "5",
  "setting_type": "number",
  "description": "Maximum number of failed login attempts before account lockout",
  "is_encrypted": false
}
```

**Sample Response:**
```json
{
  "id": 4,
  "setting_key": "security.max_login_attempts",
  "setting_value": "5",
  "setting_type": "number",
  "description": "Maximum number of failed login attempts before account lockout",
  "is_encrypted": false,
  "created_at": "2023-06-15T16:45:22",
  "updated_at": "2023-06-15T16:45:22"
}
```

### Update Setting

**Endpoint:** PUT `/api/v1/admin/settings/{setting_key}`

**Sample Request:**
```json
{
  "setting_value": "10",
  "description": "Updated: Maximum number of failed login attempts before account lockout"
}
```

**Sample Response:**
```json
{
  "id": 4,
  "setting_key": "security.max_login_attempts",
  "setting_value": "10",
  "setting_type": "number",
  "description": "Updated: Maximum number of failed login attempts before account lockout",
  "is_encrypted": false,
  "created_at": "2023-06-15T16:45:22",
  "updated_at": "2023-06-15T17:12:38"
}
```

## User Management API

### List Users

**Endpoint:** GET `/api/v1/admin/users`

**Sample Response:**
```json
{
  "users": [
    {
      "id": 1,
      "username": "john_doe",
      "email": "john.doe@example.com",
      "role": "user",
      "is_active": true,
      "is_verified": true,
      "created_at": "2023-03-15T09:30:00",
      "last_login": "2023-06-14T18:22:45"
    },
    {
      "id": 2,
      "username": "jane_smith",
      "email": "jane.smith@example.com",
      "role": "admin",
      "is_active": true,
      "is_verified": true,
      "created_at": "2023-03-16T10:15:00",
      "last_login": "2023-06-15T09:45:12"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 10
}
```

### Update User Status

**Endpoint:** PUT `/api/v1/admin/users/{user_id}/status`

**Sample Request:**
```json
{
  "action": "deactivate",
  "reason": "Suspicious activity detected on account"
}
```

**Sample Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john.doe@example.com",
  "role": "user",
  "is_active": false,
  "is_verified": true,
  "status_updated_at": "2023-06-15T17:30:45",
  "status_updated_by": "admin@paymentgateway.com"
}
```

## Reports API

### Generate Report

**Endpoint:** POST `/api/v1/admin/reports/generate`

**Sample Request:**
```json
{
  "report_type": "transaction_summary",
  "start_date": "2023-06-01",
  "end_date": "2023-06-15",
  "filters": {
    "status": "completed",
    "payment_method": "paypal"
  },
  "format": "csv"
}
```

**Sample Response:**
```json
{
  "report_id": "report-2023-06-15-1234",
  "report_type": "transaction_summary",
  "status": "processing",
  "estimated_completion_time": "2023-06-15T17:40:00",
  "download_url": null
}
```

**Sample Follow-up Response (after completion):**
```json
{
  "report_id": "report-2023-06-15-1234",
  "report_type": "transaction_summary",
  "status": "completed",
  "completion_time": "2023-06-15T17:38:22",
  "download_url": "https://api.paymentgateway.com/reports/download/report-2023-06-15-1234.csv",
  "expires_at": "2023-06-22T17:38:22"
}
```

## Authentication

All endpoints (except health check and root) require authentication via Bearer Token. Include an `Authorization` header with the value `Bearer {token}` in all requests.

**Example:**
