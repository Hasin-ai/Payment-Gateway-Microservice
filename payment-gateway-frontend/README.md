# Payment Gateway Frontend

A modern, responsive frontend application for the Payment Gateway microservices system, built with Next.js 14, TypeScript, and Tailwind CSS.

## Features

### 🌟 Core Functionality
- **User Authentication**: Secure login/register with JWT tokens
- **International Payments**: Send USD payments using local BDT payment methods
- **Payment Requests**: Create payment links for receiving international payments
- **Real-time Exchange Rates**: Live USD to BDT conversion with transparent fees
- **Transaction Management**: Complete transaction history and status tracking
- **Multi-channel Notifications**: Email, SMS, and in-app notifications

### 👥 User Stories Implementation

#### Sarah's Story (Freelancer Receiving Payments)
- Create payment requests for international clients
- Generate secure payment links with automatic currency conversion
- Real-time notifications for payment status updates
- Receive BDT equivalent after currency conversion

#### Rashid's Story (Business Sending Payments)
- Send international payments to suppliers
- Pay in local BDT using bKash, Nagad, or credit cards
- Automatic USD conversion and PayPal payout to recipients
- Payment limits management and compliance tracking

### 🔧 Technical Features
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **State Management**: Zustand for efficient state management
- **API Integration**: Complete integration with all 8 microservices
- **Real-time Updates**: Live exchange rates and transaction status
- **Error Handling**: Comprehensive error handling and user feedback
- **Security**: JWT authentication with automatic token refresh
- **Performance**: Optimized with Next.js 14 App Router

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI + shadcn/ui
- **State Management**: Zustand
- **HTTP Client**: Fetch API with custom wrapper
- **Forms**: React Hook Form + Zod validation
- **Notifications**: Sonner toast notifications
- **Icons**: Lucide React

## Project Structure

```
payment-gateway-frontend/
├── app/                          # Next.js App Router pages
│   ├── admin/                    # Admin dashboard
│   ├── dashboard/                # User dashboard
│   ├── login/                    # Authentication pages
│   ├── register/
│   ├── send/                     # Send international payments
│   ├── receive/                  # Create payment requests
│   ├── transactions/             # Transaction history
│   ├── rates/                    # Exchange rates
│   ├── profile/                  # User profile
│   ├── notifications/            # Notification center
│   ├── payment/                  # Payment success/failure pages
│   │   ├── success/
│   │   └── cancelled/
│   ├── layout.tsx                # Root layout
│   ├── page.tsx                  # Landing page
│   └── globals.css               # Global styles
├── components/                   # Reusable components
│   ├── layout/                   # Layout components
│   │   └── dashboard-layout.tsx  # Main dashboard layout
│   ├── ui/                       # UI components (shadcn/ui)
│   ├── providers.tsx             # App providers
│   └── theme-provider.tsx        # Theme provider
├── lib/                          # Utilities and configurations
│   ├── api.ts                    # API client and types
│   ├── store.ts                  # Zustand store
│   └── utils.ts                  # Utility functions
├── hooks/                        # Custom hooks
├── middleware.ts                 # Next.js middleware for auth
├── next.config.mjs               # Next.js configuration
├── tailwind.config.ts            # Tailwind CSS configuration
└── package.json                  # Dependencies
```

## API Integration

The frontend integrates with all backend microservices through the Nginx load balancer:

### Service Endpoints
- **Gateway**: `http://localhost:8080/health` - System health checks
- **User Service**: `http://localhost:8080/api/users/*` - Authentication and user management
- **Transaction Service**: `http://localhost:8080/api/transactions/*` - Transaction operations
- **Payment Service**: `http://localhost:8080/api/payments/*` - Payment processing
- **Exchange Rate Service**: `http://localhost:8080/api/exchange-rate/*` - Currency conversion
- **Notification Service**: `http://localhost:8080/api/notifications/*` - Multi-channel notifications
- **Audit Service**: `http://localhost:8080/api/audit/*` - Activity logging
- **Admin Service**: `http://localhost:8080/api/admin/*` - Administrative functions

### Key API Features
- **Circuit Breaker Pattern**: Automatic failover and recovery
- **JWT Authentication**: Secure token-based authentication
- **Real-time Data**: Live exchange rates and transaction updates
- **Error Handling**: Comprehensive error responses and user feedback
- **Rate Limiting**: Built-in rate limiting for API protection

## Getting Started

### Prerequisites
- Node.js 18+ 
- npm or pnpm
- Docker and Docker Compose
- Backend services running (see [BACKEND_SETUP.md](./BACKEND_SETUP.md))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd payment-gateway-frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   pnpm install
   ```

3. **Start Backend Services**
   ```bash
   cd ../services
   docker-compose up -d --build
   ```
   
   Verify all services are running:
   ```bash
   docker-compose ps
   ```

4. **Environment Setup (Optional)**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local if needed
   ```

5. **Start development server**
   ```bash
   npm run dev
   # or
   pnpm dev
   ```

6. **Open in browser**
   Navigate to `http://localhost:3000`

7. **Test Backend Connectivity**
   Visit `http://localhost:3000/test-backend` to verify all services are accessible

### Build for Production

```bash
npm run build
npm start
```

## User Flows

### 1. Freelancer Receiving Payment (Sarah's Story)

1. **Register/Login**: Create account or sign in
2. **Create Payment Request**: 
   - Navigate to "Receive Payment"
   - Enter amount, currency, and client details
   - Generate secure payment link
3. **Share with Client**: Send payment link via email or copy link
4. **Receive Notification**: Get notified when client pays
5. **View Transaction**: Check transaction history and status

### 2. Business Sending Payment (Rashid's Story)

1. **Login**: Sign in to business account
2. **Send International Payment**:
   - Navigate to "Send Payment"
   - Enter recipient PayPal email and USD amount
   - Review BDT conversion and fees
3. **Choose Payment Method**: Select bKash, Nagad, or credit card
4. **Complete Payment**: Pay in BDT through selected method
5. **Track Status**: Monitor USD transfer to recipient

### 3. Admin Management

1. **Admin Login**: Sign in with admin credentials
2. **Dashboard Overview**: View system statistics and metrics
3. **User Management**: Manage user accounts and permissions
4. **System Monitoring**: Check service health and performance
5. **Analytics**: View transaction trends and reports

## Key Components

### Authentication Flow
- JWT-based authentication with automatic token refresh
- Protected routes with middleware
- Persistent login state with Zustand

### Payment Processing
- Real-time exchange rate calculation
- Payment method selection (bKash, Nagad, Cards)
- Secure payment gateway integration
- Transaction status tracking

### Notification System
- Multi-channel notifications (Email, SMS, In-app)
- Real-time notification updates
- Notification preferences management

### Admin Dashboard
- System health monitoring
- User management interface
- Transaction analytics
- Service status overview

## Responsive Design

The application is fully responsive and optimized for:
- **Desktop**: Full-featured dashboard experience
- **Tablet**: Optimized layout with collapsible sidebar
- **Mobile**: Touch-friendly interface with bottom navigation

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Route Protection**: Middleware-based route protection
- **Input Validation**: Client-side and server-side validation
- **CSRF Protection**: Built-in CSRF protection
- **Secure Headers**: Security headers for production deployment

## Performance Optimizations

- **Next.js 14**: Latest performance improvements
- **Code Splitting**: Automatic code splitting by routes
- **Image Optimization**: Next.js image optimization
- **Caching**: Efficient caching strategies
- **Bundle Analysis**: Optimized bundle sizes

## Development Guidelines

### Code Style
- TypeScript for type safety
- ESLint and Prettier for code formatting
- Consistent component structure
- Proper error handling

### Component Structure
```typescript
// Component template
"use client"

import { useState, useEffect } from "react"
import { ComponentProps } from "@/types"
import { useAppStore } from "@/lib/store"

export default function ComponentName({ prop }: ComponentProps) {
  // State and hooks
  const [state, setState] = useState()
  const { storeMethod } = useAppStore()

  // Effects
  useEffect(() => {
    // Effect logic
  }, [])

  // Event handlers
  const handleEvent = () => {
    // Handler logic
  }

  // Render
  return (
    <div>
      {/* Component JSX */}
    </div>
  )
}
```

### API Integration
```typescript
// API call pattern
try {
  setIsLoading(true)
  const result = await api.methodName(params)
  // Handle success
  toast.success("Operation successful")
} catch (error) {
  // Handle error
  setError(error.message)
  toast.error("Operation failed")
} finally {
  setIsLoading(false)
}
```

## Deployment

### Production Build
```bash
npm run build
npm start
```

### Docker Deployment
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Environment Variables
```env
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_APP_NAME=PayGateway
```

## Testing

### Unit Tests
```bash
npm run test
```

### E2E Tests
```bash
npm run test:e2e
```

### Type Checking
```bash
npm run type-check
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For support and questions:
- Check the documentation
- Review the API documentation
- Contact the development team

## License

This project is licensed under the MIT License.