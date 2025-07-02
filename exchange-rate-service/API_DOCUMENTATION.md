# Exchange Rate Service API Documentation

## Overview
The Exchange Rate Service provides real-time currency exchange rates and conversion calculations with service fees. All rates are relative to BDT (Bangladeshi Taka) as the base currency.

## Base URL
```
http://localhost:8000/api/v1/rates
```

## Authentication
Currently, no authentication is required for the API endpoints.

---

## API Endpoints

### 1. Get Current Exchange Rate

**Endpoint:** `GET /current`

**Description:** Retrieves the current exchange rate for a specific currency.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `currency` | string | Yes | Currency code (e.g., USD, EUR, GBP) |

**Example Request:**
```bash
GET /api/v1/rates/current?currency=USD
```

**Success Response:**
```json
{
  "message": "Exchange rate retrieved successfully",
  "data": {
    "currency_code": "USD",
    "rate_to_bdt": 117.5,
    "source": "exchangerate-api",
    "last_updated": "2025-07-02T12:00:00Z",
    "expires_at": "2025-07-02T13:00:00Z",
    "is_active": true
  }
}
```

**Error Responses:**
- `404 Not Found` - Currency not found
- `500 Internal Server Error` - Server error

---

### 2. Get All Current Exchange Rates

**Endpoint:** `GET /all`

**Description:** Retrieves current exchange rates for all supported currencies.

**Example Request:**
```bash
GET /api/v1/rates/all
```

**Success Response:**
```json
{
  "message": "All exchange rates retrieved successfully",
  "data": {
    "rates": [
      {
        "currency_code": "USD",
        "rate_to_bdt": 117.5,
        "source": "exchangerate-api",
        "last_updated": "2025-07-02T12:00:00Z",
        "expires_at": "2025-07-02T13:00:00Z",
        "is_active": true
      },
      {
        "currency_code": "EUR",
        "rate_to_bdt": 127.8,
        "source": "exchangerate-api",
        "last_updated": "2025-07-02T12:00:00Z",
        "expires_at": "2025-07-02T13:00:00Z",
        "is_active": true
      }
    ],
    "base_currency": "BDT",
    "last_updated": "2025-07-02T12:00:00Z"
  }
}
```

**Error Responses:**
- `500 Internal Server Error` - Server error

---

### 3. Calculate BDT Amount with Service Fees

**Endpoint:** `POST /calculate`

**Description:** Calculates the BDT amount for a foreign currency amount, including service fees.

**Request Body:**
```json
{
  "from_currency": "USD",
  "to_currency": "BDT",
  "amount": 100,
  "service_fee_percentage": 2.0
}
```

**Request Body Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from_currency` | string | Yes | Source currency code (3 characters) |
| `to_currency` | string | No | Target currency code (default: "BDT") |
| `amount` | decimal | Yes | Amount to convert (must be positive) |
| `service_fee_percentage` | decimal | No | Service fee percentage (0-100) |

**Example Request:**
```bash
POST /api/v1/rates/calculate
Content-Type: application/json

{
  "from_currency": "USD",
  "to_currency": "BDT",
  "amount": 100,
  "service_fee_percentage": 2.0
}
```

**Success Response:**
```json
{
  "message": "Amount calculated successfully",
  "data": {
    "original_amount": 100,
    "from_currency": "USD",
    "to_currency": "BDT",
    "exchange_rate": 117.5,
    "converted_amount": 11750,
    "service_fee_percentage": 2.0,
    "service_fee_amount": 235,
    "total_amount": 11985,
    "calculation_time": "2025-07-02T12:00:00Z"
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid input data
- `404 Not Found` - Currency rate not found
- `500 Internal Server Error` - Server error

---

### 4. Get Exchange Rate History

**Endpoint:** `GET /history/{currency_code}`

**Description:** Retrieves historical exchange rates for a specific currency.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `currency_code` | string | Yes | Currency code (e.g., USD) |

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `days` | integer | No | 7 | Number of days of history (1-365) |

**Example Request:**
```bash
GET /api/v1/rates/history/USD?days=30
```

**Success Response:**
```json
{
  "message": "Rate history retrieved successfully",
  "data": {
    "currency_code": "USD",
    "rates": [
      {
        "currency_code": "USD",
        "rate_to_bdt": 117.5,
        "source": "exchangerate-api",
        "last_updated": "2025-07-02T12:00:00Z",
        "expires_at": "2025-07-02T13:00:00Z",
        "is_active": true
      },
      {
        "currency_code": "USD",
        "rate_to_bdt": 117.2,
        "source": "exchangerate-api",
        "last_updated": "2025-07-01T12:00:00Z",
        "expires_at": "2025-07-01T13:00:00Z",
        "is_active": false
      }
    ],
    "period_start": "2025-06-02T12:00:00Z",
    "period_end": "2025-07-02T12:00:00Z"
  }
}
```

**Error Responses:**
- `500 Internal Server Error` - Server error

---

### 5. Manually Trigger Exchange Rate Updates

**Endpoint:** `POST /update`

**Description:** Manually triggers an update of exchange rates from external APIs.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `currencies` | array[string] | No | all | Specific currencies to update |
| `force` | boolean | No | false | Force update even if rates are fresh |

**Example Request:**
```bash
POST /api/v1/rates/update?currencies=USD&currencies=EUR&force=true
```

**Success Response:**
```json
{
  "message": "Rate update initiated successfully",
  "data": {
    "update_id": "manual-20250702120000",
    "status": "initiated",
    "currencies": ["USD", "EUR"]
  }
}
```

**Error Responses:**
- `500 Internal Server Error` - Server error

---

### 6. Health Check

**Endpoint:** `GET /health`

**Description:** Provides health status of the rate service including data freshness.

**Example Request:**
```bash
GET /api/v1/rates/health
```

**Success Response:**
```json
{
  "message": "Rate service health check",
  "data": {
    "service_status": "healthy",
    "database_connection": "active",
    "last_rate_update": "2025-07-02T12:00:00Z",
    "cache_status": "active",
    "external_api_status": "available"
  }
}
```

**Error Responses:**
- `500 Internal Server Error` - Health check failed

---

### 7. Compare Exchange Rates

**Endpoint:** `GET /compare`

**Description:** Compares exchange rates across multiple currencies for a given amount.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `base_currency` | string | No | "USD" | Base currency for comparison |
| `target_currencies` | array[string] | No | ["EUR", "GBP", "CAD"] | Currencies to compare |
| `amount` | float | No | 1000.0 | Amount to compare |

**Example Request:**
```bash
GET /api/v1/rates/compare?base_currency=USD&target_currencies=EUR&target_currencies=GBP&amount=500
```

**Success Response:**
```json
{
  "message": "Currency comparison completed",
  "data": {
    "base_currency": "USD",
    "base_amount": 500,
    "comparisons": [
      {
        "currency": "EUR",
        "rate": 0.85,
        "converted_amount": 425,
        "bdt_equivalent": 54400
      },
      {
        "currency": "GBP",
        "rate": 0.72,
        "converted_amount": 360,
        "bdt_equivalent": 46080
      }
    ],
    "comparison_time": "2025-07-02T12:00:00Z"
  }
}
```

**Error Responses:**
- `500 Internal Server Error` - Server error

---

## Data Models

### ExchangeRateResponse
```json
{
  "currency_code": "string",
  "rate_to_bdt": "decimal",
  "source": "string",
  "last_updated": "datetime",
  "expires_at": "datetime",
  "is_active": "boolean"
}
```

### RateCalculationRequest
```json
{
  "from_currency": "string",
  "to_currency": "string",
  "amount": "decimal",
  "service_fee_percentage": "decimal"
}
```

### RateCalculationResponse
```json
{
  "original_amount": "decimal",
  "from_currency": "string",
  "to_currency": "string",
  "exchange_rate": "decimal",
  "converted_amount": "decimal",
  "service_fee_percentage": "decimal",
  "service_fee_amount": "decimal",
  "total_amount": "decimal",
  "calculation_time": "datetime"
}
```

---

## Supported Currencies

The service supports the following currencies:
- USD (US Dollar)
- EUR (Euro)
- GBP (British Pound)
- CAD (Canadian Dollar)
- AUD (Australian Dollar)
- JPY (Japanese Yen)
- CHF (Swiss Franc)
- SGD (Singapore Dollar)

Base currency: **BDT (Bangladeshi Taka)**

---

## Error Handling

All error responses follow this format:
```json
{
  "detail": "Error message description"
}
```

Common HTTP status codes:
- `200 OK` - Success
- `400 Bad Request` - Invalid input parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Rate Limiting

- **Default Limit:** 1000 requests per minute
- **Window:** 60 seconds

When rate limit is exceeded, you'll receive a `429 Too Many Requests` response.

---

## Configuration

### Environment Variables
- `EXCHANGE_RATE_API_KEY` - API key for external rate provider
- `RATE_UPDATE_INTERVAL` - Rate update interval in seconds (default: 900)
- `RATE_CACHE_DURATION` - Cache duration in seconds (default: 600)
- `DEFAULT_SERVICE_FEE_PERCENTAGE` - Default service fee (default: 2.0%)

---

## Examples

### Python Example
```python
import requests

# Get current USD rate
response = requests.get('http://localhost:8000/api/v1/rates/current?currency=USD')
rate_data = response.json()

# Calculate BDT amount
payload = {
    "from_currency": "USD",
    "amount": 100,
    "service_fee_percentage": 2.0
}
response = requests.post('http://localhost:8000/api/v1/rates/calculate', json=payload)
calculation = response.json()
```

### cURL Examples
```bash
# Get current rate
curl -X GET "http://localhost:8000/api/v1/rates/current?currency=USD"

# Calculate amount
curl -X POST "http://localhost:8000/api/v1/rates/calculate" \
  -H "Content-Type: application/json" \
  -d '{"from_currency": "USD", "amount": 100, "service_fee_percentage": 2.0}'

# Get rate history
curl -X GET "http://localhost:8000/api/v1/rates/history/USD?days=7"
```
