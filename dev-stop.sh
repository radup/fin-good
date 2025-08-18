#!/bin/bash

echo "🛑 Stopping development environment..."

# Stop backend services
echo "🐳 Stopping Docker services..."
docker-compose -f docker-compose.backend.yml down

echo "✅ Development environment stopped!"
echo ""
echo "To start again, run: ./dev-setup.sh"
