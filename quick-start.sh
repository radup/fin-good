#!/bin/bash

# FinGood Quick Start Script
# This script sets up and runs the entire FinGood application

set -e

echo "🚀 FinGood Quick Start"
echo "======================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose found"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads
mkdir -p logs

# Start the services
echo "🐳 Starting services with Docker Compose..."
docker-compose up -d postgres redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Setup database
echo "🗄️  Setting up database..."
python scripts/setup_db.py

# Start backend
echo "🔧 Starting backend..."
docker-compose up -d backend

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 5

# Start frontend
echo "🎨 Starting frontend..."
docker-compose up -d frontend

echo ""
echo "🎉 FinGood is starting up!"
echo ""
echo "📊 Services:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "👤 Demo Account:"
echo "  - Email: demo@fingood.com"
echo "  - Password: demo123"
echo ""
echo "📝 To view logs:"
echo "  - All services: docker-compose logs -f"
echo "  - Backend only: docker-compose logs -f backend"
echo "  - Frontend only: docker-compose logs -f frontend"
echo ""
echo "🛑 To stop: docker-compose down"
echo ""
echo "⏳ Services are starting... Please wait a moment before accessing."
