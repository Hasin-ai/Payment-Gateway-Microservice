# Payment Gateway Microservices

This repository contains a modular, microservices-based payment gateway system. It is designed for scalability, maintainability, and ease of integration with various payment providers and business logic components.

## Project Structure

- **payment-gateway-frontend/**: Next.js frontend for user and admin interfaces, including authentication, payment, transaction history, and more.
- **services/**: Contains all backend microservices, each in its own folder:
  - **admin-service/**: Admin management and related APIs.
  - **audit-service/**: Audit logging and tracking.
  - **exchange-rate-service/**: Currency exchange rate management.
  - **gateway/**: API gateway for routing and aggregation.
  - **notification-service/**: Email/SMS/push notification delivery.
  - **payment-service/**: Payment processing logic and provider integration.
  - **transaction-service/**: Transaction management and history.
  - **user-service/**: User management and authentication.

## Key Features

- **Microservices Architecture**: Each service is independently deployable and scalable.
- **API Gateway**: Centralized routing, authentication, and aggregation.
- **Frontend**: Modern Next.js app with Tailwind CSS for UI.
- **Notifications**: Pluggable notification system for user and admin alerts.
- **Audit Logging**: Comprehensive tracking of system events.
- **Exchange Rates**: Real-time currency conversion support.
- **Admin Tools**: Admin dashboard and management APIs.
- **Dockerized**: All services and frontend are containerized for easy deployment.

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Node.js (for frontend development)
- Python 3.8+ (for backend services)

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Hasin-ai/Payment-Gateway-Microservice.git
   cd Payment-Gateway-Microservice
   ```
2. **Start all services with Docker Compose:**
   ```bash
   cd services
   docker-compose up --build
   ```
3. **Start the frontend:**
   ```bash
   cd ../payment-gateway-frontend
   pnpm install
   pnpm dev
   ```

## Documentation

- See each service's `README.md` for details on endpoints, environment variables, and setup.
- See `API_DOCUMENTATION.md` in relevant folders for API details.
- See `PROJECT_STRUCTURE.md` for a detailed breakdown of the architecture.

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Push to your fork and open a Pull Request


---

For more details, see the documentation files in each service and the frontend folder.
