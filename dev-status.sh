#!/bin/bash

echo "🔍 Development Environment Status"
echo "=================================="

# Check Docker services
echo ""
echo "🐳 Docker Services:"
if docker ps --filter "name=fingood" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q fingood; then
    docker ps --filter "name=fingood" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo "❌ No FinGood containers running"
fi

# Check frontend
echo ""
echo "⚡ Frontend (Next.js):"
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Running at http://localhost:3000"
else
    echo "❌ Not running"
fi

# Check backend
echo ""
echo "🔧 Backend (FastAPI):"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Running at http://localhost:8000"
    echo "📚 API Docs: http://localhost:8000/docs"
else
    echo "❌ Not running"
fi

# Check database
echo ""
echo "🗄️  Database (PostgreSQL):"
if docker exec fingood-postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL not ready"
fi

# Check Redis
echo ""
echo "🔴 Redis:"
if docker exec fingood-redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis not ready"
fi

echo ""
echo "🎯 Quick Actions:"
echo "  Start development: ./dev-setup.sh"
echo "  Start servers: ./dev-start.sh (enhanced with health checks)"
echo "  Stop services: ./dev-stop.sh"
echo "  View logs: docker-compose -f docker-compose.db-only.yml logs -f"
