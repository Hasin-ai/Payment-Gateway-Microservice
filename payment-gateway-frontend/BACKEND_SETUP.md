# Backend Setup Guide

This guide will help you set up and run the backend services required for the Payment Gateway Frontend.

## Prerequisites

- Docker and Docker Compose installed
- Ports 5433, 6380, 8000-8007, and 8080 available
- At least 4GB of available RAM

## Quick Start

### 1. Navigate to Services Directory
```bash
cd services
```

### 2. Start All Services
```bash
docker-compose up -d --build
```

### 3. Verify Services are Running
```bash
docker-compose ps
```

You should see all 11 services running:
- `nginx` (Port 8080) - Load Balancer
- `gateway` (Port 8000) - API Gateway
- `user-service` (Port 8001) - User Management
- `payment-service` (Port 8002) - Payment Processing
- `transaction-service` (Port 8003) - Transaction Management
- `notification-service` (Port 8004) - Notifications
- `audit-service` (Port 8005) - Audit Logging
- `exchange-rate-service` (Port 8006) - Exchange Rates
- `admin-service` (Port 8007) - Admin Functions
- `postgres` (Port 5433) - Database
- `redis` (Port 6380) - Cache

### 4. Check Service Health
Visit: http://localhost:8080/health

Expected response:
```json
{
  "gateway": "healthy",
  "services": {
    "user-service": {"status": "healthy"},
    "payment-service": {"status": "healthy"},
    "transaction-service": {"status": "healthy"},
    "notification-service": {"status": "healthy"},
    "audit-service": {"status": "healthy"},
    "exchange-rate-service": {"status": "healthy"},
    "admin-service": {"status": "healthy"}
  }
}
```

## Frontend Testing

### 1. Start Frontend Development Server
```bash
cd payment-gateway-frontend
npm install
npm run dev
```

### 2. Test Backend Connectivity
Visit: http://localhost:3000/test-backend

This page will test all backend endpoints and show their status.

### 3. Debug Authentication
Visit: http://localhost:3000/debug

This page shows authentication state and allows you to test login functionality.

## Creating Test Users

### Option 1: Via Frontend Registration
1. Go to http://localhost:3000/register
2. Fill out the registration form
3. Use the created credentials to login

### Option 2: Via API (using curl)
```bash
# Register a new user
curl -X POST http://localhost:8080/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123",
    "first_name": "Test",
    "last_name": "User",
    "phone": "+1234567890"
  }'

# Login with the user
curl -X POST http://localhost:8080/api/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

## Troubleshooting

### Services Not Starting
```bash
# Check logs for specific service
docker-compose logs -f [service-name]

# Check all logs
docker-compose logs -f

# Restart all services
docker-compose down
docker-compose up -d --build
```

### Port Conflicts
If you get port conflicts, check what's using the ports:
```bash
# Check port usage
lsof -i :8080
lsof -i :8000

# Kill processes if needed
sudo kill -9 [PID]
```

### Database Issues
```bash
# Reset database
docker-compose down -v
docker-compose up -d --build
```

### Frontend Can't Connect to Backend
1. Verify all services are running: `docker-compose ps`
2. Check service health: http://localhost:8080/health
3. Test individual services:
   - User Service: http://localhost:8001/health
   - Payment Service: http://localhost:8002/health
   - etc.

## Environment Variables

The backend uses these key environment variables (already configured in docker-compose.yml):

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/payment_gateway
REDIS_URL=redis://redis:6379

# PayPal (for testing, use sandbox)
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-client-secret
PAYPAL_MODE=sandbox

# SSLCommerz (for testing, use sandbox)
SSLCOMMERZ_STORE_ID=your-sslcommerz-store-id
SSLCOMMERZ_STORE_PASSWORD=your-sslcommerz-password
SSLCOMMERZ_MODE=sandbox

# Email (optional for testing)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# SMS (optional for testing)
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
```

## API Endpoints

All API endpoints are accessible through the load balancer at http://localhost:8080:

- **User Management**: `/api/users/*`
- **Transactions**: `/api/transactions/*`
- **Payments**: `/api/payments/*`
- **Exchange Rates**: `/api/exchange-rate/*`
- **Notifications**: `/api/notifications/*`
- **Audit**: `/api/audit/*`
- **Admin**: `/api/admin/*`

## Success Indicators

✅ All services show "healthy" status
✅ Frontend can register new users
✅ Frontend can login users
✅ Exchange rates are fetched successfully
✅ Transactions can be created
✅ Notifications are sent

## Getting Help

If you encounter issues:

1. Check the service logs: `docker-compose logs -f`
2. Verify all ports are available
3. Ensure Docker has enough resources allocated
4. Check the frontend console for API errors
5. Use the test pages at `/test-backend` and `/debug`

## Production Deployment

For production deployment:

1. Update environment variables with real API keys
2. Change database passwords
3. Use production-grade secrets management
4. Configure proper SSL certificates
5. Set up monitoring and logging
6. Configure backup strategies