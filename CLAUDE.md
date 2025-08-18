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

### Key Features
- CSV/Excel file upload and parsing
- Rule-based transaction categorization
- Dashboard with analytics and charts
- User authentication and management
- Export functionality

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
```

### Backend Commands
```bash
cd backend
python main.py       # Start FastAPI server (port 8000)
python scripts/setup_db.py  # Initialize database with sample data

# Testing and quality (when available)
pytest              # Run backend tests
black .             # Format Python code
isort .             # Sort imports
flake8 .            # Lint Python code
```

## Service URLs
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Demo Account
- Email: `demo@fingood.com`
- Password: `demo123`

## Database Schema
- **Users**: Authentication and user management
- **Transactions**: Financial transaction records with categorization
- **Categories**: Transaction categories with ML-based suggestions

## File Upload
- Supports CSV, XLSX, XLS formats
- Sample data available: `sample-data.csv`, `sample-data-debit-credit.csv`
- Upload limit: 10MB
- Processing includes validation and categorization

## Environment Setup
The backend requires a `.env` file with database URLs, secret keys, and API configurations. Default settings are in `backend/app/core/config.py`.

## Docker Configuration
- `docker-compose.yml`: Full stack deployment
- `docker-compose.backend.yml`: Backend services only (for development)
- `Dockerfile.frontend`: Frontend container build
- `backend/Dockerfile`: Backend container build

## Testing
Use the included sample CSV files to test the upload and categorization features. The application includes automatic API documentation at `/docs`.