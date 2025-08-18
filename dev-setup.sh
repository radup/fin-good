#!/bin/bash

# Development setup script - Both frontend and backend run locally for hot reloading
echo "🚀 Setting up development environment..."
echo "📦 Database services (PostgreSQL, Redis) will run in Docker"
echo "⚡ Frontend and Backend will run locally for hot reloading"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js and try again."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm and try again."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Install frontend dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
    echo "✅ Frontend dependencies installed"
else
    echo "✅ Frontend dependencies already installed"
fi

# Check and install backend dependencies
if [ ! -d "backend/venv" ]; then
    echo "📦 Setting up Python virtual environment for backend..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
    echo "✅ Backend dependencies installed"
else
    echo "✅ Backend virtual environment already exists"
fi

# Start database services in Docker (PostgreSQL, Redis only)
echo "🐳 Starting database services in Docker..."
docker-compose -f docker-compose.db-only.yml up -d

# Wait for database to be ready
echo "⏳ Waiting for database services to be ready..."
until docker-compose -f docker-compose.db-only.yml exec postgres pg_isready -U postgres > /dev/null 2>&1; do
    echo "   Waiting for PostgreSQL..."
    sleep 2
done
until docker-compose -f docker-compose.db-only.yml exec redis redis-cli ping > /dev/null 2>&1; do
    echo "   Waiting for Redis..."
    sleep 2
done
echo "✅ Database services are ready!"

# Run database migrations
echo "🔄 Running database migrations..."
cd backend
source venv/bin/activate
DATABASE_URL=postgresql://postgres:development123@localhost:5432/fingood alembic upgrade head
cd ..

echo "⚡ Ready to start development servers locally!"
echo "🌐 Frontend will be available at: http://localhost:3000"
echo "🔧 Backend API will be available at: http://localhost:8000"
echo ""
echo "To start development:"
echo "  Terminal 1: npm run dev"
echo "  Terminal 2: cd backend && source venv/bin/activate && python main.py"
echo ""
echo "Or run: ./dev-start.sh to start both automatically"
