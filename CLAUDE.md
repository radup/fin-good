# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FinGood is an AI-powered financial intelligence platform that automates transaction categorization and provides cash flow insights for small businesses. It's a full-stack application with a FastAPI backend and Next.js frontend.

**Current Development Phase**: Advanced Feature Implementation (Phase 3-4) including budget analysis, multi-model forecasting, and enhanced analytics.

## Architecture

### Backend (FastAPI + PostgreSQL)
- **Location**: `backend/` directory
- **Entry point**: `backend/main.py`
- **API routes**: `backend/app/api/v1/` with endpoints for auth, transactions, categories, upload, analytics
- **Models**: SQLAlchemy models in `backend/app/models/`
- **Services**: Business logic in `backend/app/services/` (categorization, CSV parsing)
- **Database**: PostgreSQL with Redis for caching
- **Configuration**: `backend/app/core/config.py`

### Frontend (Next.js 14 + React)
- **Location**: Root directory (Next.js App Router)
- **Entry point**: `app/layout.tsx` and `app/page.tsx`
- **Components**: React components in `components/`
- **Hooks**: Custom React hooks in `hooks/` for API integration
- **API layer**: API client in `lib/api.ts` with comprehensive API modules
- **Styling**: Tailwind CSS with global styles in `app/globals.css`
- **State Management**: TanStack React Query for server state
- **Charts**: Recharts for data visualization

### Security Architecture
This is a **financial application** with enterprise-grade security:
- **JWT security**: Token blacklisting with `RevokedToken` model
- **Cookie-based auth**: HttpOnly, Secure, SameSite protections
- **CSRF protection**: Token-based validation
- **Input validation**: SQL injection and XSS prevention
- **Configuration security**: SECRET_KEY validation with entropy checks
- **Rate limiting**: Redis-backed per-user limits
- **Audit logging**: Financial-grade compliance tracking
- **Password security**: Bcrypt hashing with secure reset flows

## Development Commands

### Quick Start (Full Docker)
```bash
./quick-start.sh  # Starts all services in Docker
```

### Development Setup (Recommended)
```bash
./dev-setup.sh   # Database in Docker, backend/frontend local with hot reload
./dev-start.sh   # Start both frontend and backend development servers
```

### Development Scripts
```bash
./dev-status.sh  # Check status of all services
./dev-stop.sh    # Stop development environment
```

### Frontend Commands
```bash
npm run dev          # Start development server (port 3000)
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript type checking
npm test             # Run Jest tests
npm run test:watch   # Run Jest in watch mode
npm run test:e2e     # Run Playwright E2E tests
```

### Backend Commands
```bash
cd backend
python main.py       # Start FastAPI server (port 8001 by default, 8000 fallback)
python scripts/setup_db.py  # Initialize database with sample data

# Testing (comprehensive test suite available)
COMPLIANCE_SECRET_KEY="test-compliance-secret-key-at-least-32-chars-long" pytest  # Run all tests
pytest -m unit           # Run unit tests only
pytest -m integration    # Run integration tests
pytest -m security       # Run security tests
pytest -m financial     # Run financial data validation tests
pytest -m compliance    # Run regulatory compliance tests
pytest tests/unit/api/   # Run specific test directory
pytest -k "test_auth"    # Run specific test pattern
pytest --cov            # Run with coverage report

# Database migrations
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head     # Apply migrations
alembic downgrade -1     # Rollback one migration

# Code quality
black .             # Format Python code
isort .             # Sort imports
flake8 .            # Lint Python code
```

### Environment Setup Requirements

The backend requires specific environment variables for security:

```bash
# Required security keys (must be 32+ characters)
SECRET_KEY=<generated-with-secrets.token_urlsafe(32)>
CSRF_SECRET_KEY=<generated-with-secrets.token_urlsafe(32)>
COMPLIANCE_SECRET_KEY=<generated-with-secrets.token_urlsafe(32)>

# Database (production requires secure credentials)
DATABASE_URL=postgresql://username:password@host:port/database
REDIS_URL=redis://:password@host:port/db  # Note: colon before password for Redis auth
```

**Important**: The configuration validator in `backend/app/core/config.py` enforces security requirements and will reject weak keys.

## Service URLs
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001 (or 8000)
- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

## Demo Account
- Email: `demo@fingood.com`
- Password: `demo123`

## Key Architecture Patterns

### Authentication Flow
1. Login creates JWT token via `JWTManager` in `backend/app/core/security.py`
2. Token stored in HttpOnly cookie via `set_auth_cookie()`
3. Requests validated by `get_current_user_from_cookie()`
4. Token revocation tracked in `RevokedToken` model for security

### Transaction Processing
1. CSV upload via `TransactionTable` component with drag-drop
2. File validation in `backend/app/services/csv_parser.py`
3. Auto-categorization via `backend/app/services/categorization.py`
4. Real-time updates through WebSocket in `backend/app/core/websocket_manager.py`

### Database Design
- **Users**: Authentication with OAuth support and password reset tokens
- **Transactions**: Financial records with vendor matching and confidence scores
- **RevokedTokens**: JWT security tracking for financial compliance
- **Categories**: Hierarchical categorization with ML suggestions

### Error Handling
- Centralized in `backend/app/core/error_handlers.py`
- Security-conscious responses that don't leak sensitive data
- Structured error responses with correlation IDs
- Comprehensive logging without exposing secrets

## Testing Strategy

### Backend Testing (32 test files)
- **Security tests**: JWT validation, configuration security, auth flows
- **Integration tests**: API endpoints, database operations
- **Unit tests**: Business logic, utilities, validators
- **Compliance tests**: Financial data integrity, audit trails

### Test Markers (use with pytest -m)
- `security`: Security-focused tests
- `unit`: Individual component tests
- `integration`: Component interaction tests
- `financial`: Financial data validation
- `compliance`: Regulatory compliance tests

### Frontend Testing
- **Jest unit tests**: `npm test`, `npm run test:watch`, `npm run test:coverage`
- **E2E tests**: `npm run test:e2e` (Playwright configured)
- **Test utilities**: Jest, Testing Library, Faker.js for test data
- **Accessibility testing**: jest-axe configured for a11y testing

## File Upload Processing
- Supports CSV, XLSX, XLS formats
- Sample data: `sample-data.csv`, `sample-data-debit-credit.csv`
- Upload limit: 10MB with security scanning
- Processing pipeline: validation → parsing → categorization → storage
- Real-time progress via WebSocket updates

## Advanced Features

### Multi-Model Forecasting System
- **Models**: Prophet, ARIMA, Neural Prophet, and ensemble methods
- **Endpoints**: `/api/v1/forecasting/` for comprehensive forecasting
- **Visualization**: Interactive charts with Recharts integration
- **Configuration**: `backend/app/services/multi_model_forecasting_engine.py`

### Budget Analysis System
- **Complete CRUD**: Budget creation, management, variance analysis
- **Performance metrics**: Budget adherence tracking, accuracy scoring
- **Scenario modeling**: What-if analysis and optimization
- **Demo page**: `/budget-analysis-demo` for testing functionality

### Enhanced Analytics & Intelligence
- **Bulk Operations API**: Transaction bulk categorization, updates, deletions
- **Duplicate Detection**: Advanced algorithms for transaction deduplication
- **Pattern Recognition**: ML-based pattern analysis for insights
- **Enhanced Categorization**: ML and rule-based hybrid approach

### Background Job System (RQ)
- **Job processing**: Redis Queue (RQ) for async transaction processing
- **Job types**: File processing, categorization, export generation, forecasting
- **Monitoring**: Job status tracking, retry logic, failure handling
- **Configuration**: `backend/app/core/background_jobs.py`

### Performance & Monitoring
- **Performance monitoring**: System resource tracking, request timing
- **Audit logging**: Financial-grade transaction audit trails
- **Compliance logging**: Regulatory compliance event tracking
- **Error monitoring**: Structured error reporting with sanitization
- **Rate limiting**: Redis-backed per-user request limits

### WebSocket Integration
- **Real-time updates**: Upload progress, categorization status
- **Connection management**: User authentication, batch tracking
- **Event streaming**: Transaction processing progress

## Demo Pages and Testing
All major features have dedicated demo pages for testing:
- `/budget-analysis-demo` - Budget creation, analysis, and visualization
- `/forecasting-demo` - Multi-model forecasting with interactive charts  
- `/categorization-performance-demo` - Categorization metrics and improvement
- `/auto-improvement-demo` - ML-based auto-improvement for categorization
- `/ai-explanation-demo` - AI-powered transaction explanations
- `/rate-limit-feedback-demo` - Rate limiting behavior testing

## Critical React Query Patterns

**IMPORTANT**: When working with API calls in React components, always extract the `.data` property from Axios responses:

```typescript
// ✅ CORRECT - Extract .data property
const { data: budgets, isLoading, error } = useQuery({
  queryKey: ['budgets'],
  queryFn: async () => {
    const response = await budgetAnalysisAPI.getBudgets()
    return response.data  // Extract .data from Axios response
  },
})

// ❌ INCORRECT - Using response directly
const { data: budgets, isLoading, error } = useQuery({
  queryKey: ['budgets'],
  queryFn: () => budgetAnalysisAPI.getBudgets(), // Returns Axios response object
})
```

This pattern applies to ALL API calls including mutations. The frontend expects arrays/objects but Axios returns `{ data: actualData, status, headers, ... }`.

## Security Considerations
- All middleware disabled in main.py for development - **re-enable for production**
- Configuration validator enforces financial-grade security
- JWT tokens include jti for tracking and revocation
- All database operations use parameterized queries
- File uploads include malware scanning and quarantine

# Important Instructions for Claude Code

Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.