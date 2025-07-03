# Payment Gateway Microservices

A comprehensive, scalable payment gateway system built with microservices architecture using FastAPI, designed to handle multiple payment providers and ensure high availability, security, and performance.

## 🏗️ Architecture Overview

This system consists of 8 specialized microservices, each responsible for specific business domains:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │────│  User Service   │────│  Admin Service  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Payment Service │────│Transaction Svc  │────│  Audit Service  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│Notification Svc │────│Exchange Rate Svc│────│   Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Services Overview

### 1. **Gateway Service** 🌐
- **Purpose**: API Gateway and load balancer
- **Features**: 
  - Request routing and load balancing
  - Rate limiting and authentication
  - API documentation aggregation
  - Circuit breaker pattern implementation
- **Port**: 8000

### 2. **User Service** 👥
- **Purpose**: User management and authentication
- **Features**: 
  - User registration and authentication
  - JWT token management
  - Profile management
  - Session handling
- **Port**: 8001

### 3. **Payment Service** 💳
- **Purpose**: Payment processing and gateway integration
- **Features**: 
  - PayPal integration
  - SSLCommerz integration
  - Webhook handling
  - Payment status management
- **Port**: 8002

### 4. **Transaction Service** 📊
- **Purpose**: Transaction management and history
- **Features**: 
  - Transaction creation and tracking
  - Payment limits management
  - Transaction history and analytics
  - Fee calculation
- **Port**: 8003

### 5. **Notification Service** 📧
- **Purpose**: Multi-channel notifications
- **Features**: 
  - Email notifications
  - SMS notifications
  - Push notifications
  - Template management
- **Port**: 8004

### 6. **Audit Service** 🔍
- **Purpose**: Audit logging and compliance
- **Features**: 
  - Comprehensive audit logging
  - Data masking for sensitive information
  - Analytics and reporting
  - Compliance monitoring
- **Port**: 8005

### 7. **Exchange Rate Service** 💱
- **Purpose**: Currency conversion and rate management
- **Features**: 
  - Real-time exchange rate fetching
  - Rate caching and optimization
  - Multi-currency support
  - Historical rate tracking
- **Port**: 8006

### 8. **Admin Service** ⚙️
- **Purpose**: Administrative dashboard and system management
- **Features**: 
  - System configuration management
  - User management dashboard
  - Analytics and reporting
  - System health monitoring
- **Port**: 8007

## 🛠️ Technology Stack

### Backend Framework
- **FastAPI**: Modern, fast web framework for building APIs
- **Python 3.12+**: Programming language
- **Pydantic**: Data validation and settings management
- **SQLAlchemy**: Database ORM
- **Alembic**: Database migrations

### Database
- **PostgreSQL**: Primary database for all services
- **Redis**: Caching and session storage

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **nginx**: Reverse proxy and load balancing

### Security
- **JWT**: Authentication tokens
- **OAuth 2.0**: Authorization framework
- **Rate limiting**: API protection
- **Data masking**: Sensitive information protection

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.12+
- PostgreSQL
- Redis

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Hasin-ai/Payment-Gateway-Microservice.git
   cd Payment-Gateway-Microservice
   ```

2. **Set up environment variables**
   ```bash
   # Copy environment template for each service
   cp admin-service/.env.example admin-service/.env
   cp audit-service/.env.example audit-service/.env
   cp exchange-rate-service/.env.example exchange-rate-service/.env
   cp gateway/.env.example gateway/.env
   cp notification-service/.env.example notification-service/.env
   cp payment-service/.env.example payment-service/.env
   cp transaction-service/.env.example transaction-service/.env
   cp user-service/.env.example user-service/.env
   ```

3. **Configure environment variables**
   Edit each `.env` file with your specific configuration:
   ```env
   # Database
   DATABASE_URL=postgresql://user:password@localhost:5432/dbname
   
   # Redis
   REDIS_URL=redis://localhost:6379
   
   # JWT
   JWT_SECRET_KEY=your-secret-key
   JWT_ALGORITHM=HS256
   
   # Payment Providers
   PAYPAL_CLIENT_ID=your-paypal-client-id
   PAYPAL_CLIENT_SECRET=your-paypal-client-secret
   SSLCOMMERZ_STORE_ID=your-sslcommerz-store-id
   SSLCOMMERZ_STORE_PASSWORD=your-sslcommerz-password
   
   # Notification
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```

4. **Start the services**
   ```bash
   # Start all services with Docker Compose
   docker-compose up -d
   
   # Or start individual services
   docker-compose up -d gateway user-service payment-service
   ```

5. **Initialize databases**
   ```bash
   # Run database migrations
   docker-compose exec audit-service alembic upgrade head
   docker-compose exec transaction-service alembic upgrade head
   ```

## 📖 API Documentation

Each service provides interactive API documentation:

- **Gateway**: http://localhost:8000/docs
- **User Service**: http://localhost:8001/docs
- **Payment Service**: http://localhost:8002/docs
- **Transaction Service**: http://localhost:8003/docs
- **Notification Service**: http://localhost:8004/docs
- **Audit Service**: http://localhost:8005/docs
- **Exchange Rate Service**: http://localhost:8006/docs
- **Admin Service**: http://localhost:8007/docs

## 🔧 Development

### Running Individual Services

```bash
# Navigate to service directory
cd user-service

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --reload --port 8001
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Testing

```bash
# Run tests for a specific service
cd audit-service
python -m pytest test_audit_service.py -v

# Run tests with coverage
python -m pytest --cov=app tests/
```

## 🔒 Security Features

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- API key authentication for service-to-service communication

### Data Protection
- Data encryption at rest and in transit
- Sensitive data masking in logs
- PCI DSS compliance considerations

### Rate Limiting
- IP-based rate limiting
- User-based rate limiting
- API endpoint specific limits

### Monitoring & Auditing
- Comprehensive audit logging
- Real-time monitoring
- Security event alerting

## 🏗️ Deployment

### Docker Deployment

```bash
# Build all services
docker-compose build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n payment-gateway
```

### Environment Configuration

| Environment | Gateway URL | Database | Redis | Monitoring |
|-------------|-------------|----------|-------|------------|
| Development | http://localhost:8000 | PostgreSQL (local) | Redis (local) | Console logs |
| Staging | https://staging-api.yourdomain.com | PostgreSQL (managed) | Redis (managed) | ELK Stack |
| Production | https://api.yourdomain.com | PostgreSQL (HA) | Redis (cluster) | Full monitoring |

## 📊 Monitoring & Analytics

### Health Checks
- Service health endpoints: `/health`
- Database connectivity checks
- External service dependency checks

### Metrics Collection
- Request/response metrics
- Database performance metrics
- Payment processing metrics
- Error rates and latency

### Logging
- Structured logging with JSON format
- Centralized log aggregation
- Log level configuration per service

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
