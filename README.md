# FinGood - AI-Powered Financial Intelligence

An intelligent financial management platform that automates transaction categorization and provides cash flow insights for small businesses.

## 🚀 Quick Start (Recommended)

The fastest way to get started is using Docker:

```bash
# Clone the repository
git clone <your-repo-url>
cd fin-good

# Run the quick start script
./quick-start.sh
```

This will:
- Start PostgreSQL and Redis containers
- Set up the database with sample data
- Start the FastAPI backend
- Start the Next.js frontend
- Create a demo account

## ⚡ Development Setup (Hot Reloading)

For development with hot reloading and faster iteration:

```bash
# Run the development setup script
./dev-setup.sh
```

This will:
- Start backend services (PostgreSQL, Redis, FastAPI) in Docker
- Run the Next.js frontend locally for hot reloading
- Install dependencies automatically
- Provide better development experience

### Development Scripts

```bash
# Start development environment
./dev-setup.sh

# Check status of all services
./dev-status.sh

# Stop development environment
./dev-stop.sh
```

**Benefits of local frontend development:**
- ⚡ Hot reloading for instant code changes
- 🔧 Better debugging with browser dev tools
- 📝 Faster iteration cycles
- 🎯 No Docker rebuilds needed for frontend changes
- 🎨 Proper Tailwind CSS processing with PostCSS

**Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Demo Account:**
- Email: `demo@fingood.com`
- Password: `demo123`

## 🏗️ Architecture

### Backend (FastAPI + PostgreSQL)
- **FastAPI**: High-performance async API with automatic docs
- **PostgreSQL**: Robust financial data storage with JSON support
- **Redis**: Caching for LLM responses and session management
- **SQLAlchemy**: ORM with migrations

### Frontend (Next.js + React)
- **Next.js 14**: Full-stack React with App Router
- **Tailwind CSS**: Utility-first styling
- **React Query**: Server state management
- **React Hook Form**: Form handling

### AI/ML Stack
- **scikit-learn**: Traditional ML models
- **Prophet**: Time series forecasting
- **Ollama**: Local LLM for natural language queries
- **Rule-based Engine**: Vendor name matching for categorization

## 📊 MVP Features (Week 1-2)

1. **CSV Upload & Validation**
   - Drag-and-drop interface
   - Real-time data validation
   - Flexible schema handling

2. **Rule-based Categorization**
   - Vendor name pattern matching
   - Manual override capability
   - Learning from user corrections

3. **Dashboard & Analytics**
   - Transaction overview
   - Category breakdown
   - Export functionality

4. **User Management**
   - OAuth authentication
   - Multi-tenant data isolation
   - Role-based access

## 🔄 Development Phases

- **Phase 0**: Data Foundation (CSV → QB → Xero)
- **Phase 1**: Smart Categorization MVP
- **Phase 2**: Cash Flow Forecasting
- **Phase 3**: Tax Intelligence
- **Phase 4**: Business Intelligence
- **Phase 5**: Treasury Optimization

## 📈 Success Metrics

- **Data Quality**: 95% successful parsing, <5% corruption
- **Categorization**: 80% accuracy, <20% manual corrections
- **User Engagement**: 90% 7-day retention, >5min sessions
- **Time Savings**: 2+ hours/month per user

## 🛠️ Manual Setup

If you prefer to run without Docker:

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
python ../scripts/setup_db.py

# Start the server
python main.py
```

### Frontend Setup
```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

## 🧪 Testing

### Sample Data
Use the included `sample-data.csv` file to test the application:

1. Start the application
2. Login with demo account
3. Upload `sample-data.csv`
4. View categorized transactions

### API Testing
The API includes automatic documentation at http://localhost:8000/docs

## 📝 Environment Variables

Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/fingood
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_HOSTS=["http://localhost:3000"]

# File upload
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=[".csv", ".xlsx", ".xls"]

# AI/ML
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment
For production deployment, consider:
- Using a production database (AWS RDS, Google Cloud SQL)
- Setting up proper SSL certificates
- Configuring environment variables
- Setting up monitoring and logging
- Using a CDN for static assets

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the sample data and setup scripts

## 🎯 Roadmap

### Week 1-2: Foundation
- [x] CSV upload and parsing
- [x] Rule-based categorization
- [x] Basic dashboard
- [x] User authentication

### Week 3-4: Intelligence
- [ ] ML-based categorization
- [ ] Cash flow forecasting
- [ ] Advanced analytics
- [ ] Export functionality

### Week 5-6: Integration
- [ ] QuickBooks Online integration
- [ ] Xero integration
- [ ] Advanced reporting
- [ ] Mobile responsiveness

### Week 7+: Scale
- [ ] Multi-user support
- [ ] Advanced ML models
- [ ] Tax estimation
- [ ] Business intelligence features
