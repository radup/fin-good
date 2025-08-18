#!/bin/bash

# Development setup script - Frontend runs locally, backend in Docker
echo "🚀 Setting up development environment..."
echo "📦 Backend and database will run in Docker"
echo "⚡ Frontend will run locally for hot reloading"

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

echo "✅ Prerequisites check passed"

# Install frontend dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
    echo "✅ Frontend dependencies installed"
else
    echo "✅ Frontend dependencies already installed"
fi

# Start backend services in Docker (database, redis, backend)
echo "🐳 Starting backend services in Docker..."
docker-compose -f docker-compose.backend.yml up -d

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
until curl -s http://localhost:8000/health > /dev/null 2>&1; do
    echo "   Waiting for backend..."
    sleep 2
done
echo "✅ Backend is ready!"

# Start frontend locally
echo "⚡ Starting frontend locally for hot reloading..."
echo "🌐 Frontend will be available at: http://localhost:3000"
echo "🔧 Backend API will be available at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Start frontend with hot reloading
npm run dev
