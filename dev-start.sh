#!/bin/bash

# Start both frontend and backend in parallel for development
echo "🚀 Starting development servers..."

# Function to cleanup background processes on exit
cleanup() {
    echo "🛑 Stopping development servers..."
    kill $FRONTEND_PID $BACKEND_PID 2>/dev/null
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if database services are running
echo "🔍 Checking if database services are running..."
if ! docker-compose -f docker-compose.db-only.yml ps | grep -q "Up"; then
    echo "⚠️  Database services are not running. Starting them now..."
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
else
    echo "✅ Database services are already running"
fi

# Check if services are set up
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating default .env file..."
    cp .env.example .env 2>/dev/null || echo "POSTGRES_PASSWORD=development123
SECRET_KEY=development-secret-key-change-in-production-minimum-32-characters
COMPLIANCE_SECRET_KEY=compliance-development-secret-key-change-in-production-32-chars" > .env
fi

# Check if backend virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "❌ Backend virtual environment not found. Please run ./dev-setup.sh first."
    exit 1
fi

# Check if frontend dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "❌ Frontend dependencies not found. Please run ./dev-setup.sh first."
    exit 1
fi

# Start backend in background
echo "🔧 Starting backend server (local for hot reloading)..."
cd backend
source venv/bin/activate
DATABASE_URL=postgresql://postgres:development123@localhost:5432/fingood \
REDIS_URL=redis://:secure_dev_password_2024@localhost:6379/0 \
SECRET_KEY=CziCeepOcIQXoOSmRFTR6JLPWkZ1Zr3y9slo0FLS3Tk \
COMPLIANCE_SECRET_KEY=compliance_dev_secure_key_2024_min_32_chars_long \
CSRF_SECRET_KEY=csrf_dev_secure_key_2024_min_32_chars_long \
ENFORCE_HTTPS=false \
COOKIE_SECURE=false \
python main.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Backend failed to start. Check the logs above for errors."
    exit 1
fi

# Start frontend in background
echo "🌐 Starting frontend server (local for hot reloading)..."
npm run dev &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 3

echo ""
echo "✅ Development servers started successfully!"
echo "🌐 Frontend: http://localhost:3000 (local - hot reloading enabled)"
echo "🔧 Backend: http://localhost:8000 (local - hot reloading enabled)"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🗄️  Database: PostgreSQL & Redis (Docker)"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for both processes
wait $FRONTEND_PID $BACKEND_PID