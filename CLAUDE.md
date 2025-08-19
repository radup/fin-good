# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FinGood is an AI-powered financial intelligence platform that automates transaction categorization and provides cash flow insights for small businesses. It's a full-stack application with a FastAPI backend and Next.js frontend.

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
- **API layer**: API client in `lib/api.ts`
- **Styling**: Tailwind CSS with global styles in `app/globals.css`

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
./dev-setup.sh   # Backend in Docker, frontend local with hot reload
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
python main.py       # Start FastAPI server (port 8000)
python scripts/setup_db.py  # Initialize database with sample data

# Testing (comprehensive test suite available)
pytest                    # Run all tests
pytest -m unit           # Run unit tests only
pytest -m integration    # Run integration tests
pytest -m security       # Run security tests
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
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

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

### Frontend Testing (TODO)
- Currently missing - should add React component tests
- Jest and Testing Library configured in package.json
- Playwright E2E tests configured

## File Upload Processing
- Supports CSV, XLSX, XLS formats
- Sample data: `sample-data.csv`, `sample-data-debit-credit.csv`
- Upload limit: 10MB with security scanning
- Processing pipeline: validation → parsing → categorization → storage
- Real-time progress via WebSocket updates

## Security Considerations
- All middleware disabled in main.py for development - **re-enable for production**
- Configuration validator enforces financial-grade security
- JWT tokens include jti for tracking and revocation
- All database operations use parameterized queries
- File uploads include malware scanning and quarantine