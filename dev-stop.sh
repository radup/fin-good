#!/bin/bash

echo "🛑 Stopping development environment..."

# Stop database services (PostgreSQL and Redis)
echo "🐳 Stopping database services..."
docker-compose -f docker-compose.db-only.yml down

echo "✅ Development environment stopped!"
echo ""
echo "To start again, run: ./dev-setup.sh"
