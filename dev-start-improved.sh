#!/bin/bash

# Enhanced Development Environment Starter for FinGood
# Features: Smart container management, port cleanup, health checks, log streaming

set -e  # Exit on any error

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8000
FRONTEND_PORT=3000
LOG_DIR="logs/dev"
MAX_WAIT_TIME=60

# Create log directory
mkdir -p "$LOG_DIR"

# Process management
BACKEND_PID=""
FRONTEND_PID=""

echo -e "${BLUE}🚀 Starting FinGood Development Environment${NC}"
echo "================================================="

# Function to print colored messages
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Enhanced cleanup function
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down development environment...${NC}"
    
    # Kill frontend process
    if [ -n "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        log_info "Stopping frontend server (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID 2>/dev/null
        wait $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Kill backend process
    if [ -n "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        log_info "Stopping backend server (PID: $BACKEND_PID)"
        kill $BACKEND_PID 2>/dev/null
        wait $BACKEND_PID 2>/dev/null || true
    fi
    
    # Kill any remaining processes on our ports
    kill_port_processes $BACKEND_PORT
    kill_port_processes $FRONTEND_PORT
    
    log_success "Development environment stopped"
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM EXIT

# Function to kill processes on a specific port
kill_port_processes() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null || echo "")
    
    if [ -n "$pids" ]; then
        log_warning "Killing processes on port $port: $pids"
        echo $pids | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

# Function to check if a port is available
is_port_available() {
    ! lsof -i:$1 >/dev/null 2>&1
}

# Function to wait for a service with timeout
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_wait=${3:-$MAX_WAIT_TIME}
    local count=0
    
    log_info "Waiting for $service_name to be ready..."
    
    while [ $count -lt $max_wait ]; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            log_success "$service_name is ready!"
            return 0
        fi
        
        sleep 2
        count=$((count + 2))
        echo -n "."
    done
    
    echo ""
    log_error "$service_name failed to start within ${max_wait}s"
    return 1
}

# Function to check Docker availability
check_docker() {
    log_info "Checking Docker availability..."
    
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker not found. Please install Docker."
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon not running. Please start Docker Desktop."
        exit 1
    fi
    
    log_success "Docker is available and running"
}

# Function to manage database containers
manage_database_containers() {
    log_info "Managing database containers..."
    
    # Check if containers exist
    local postgres_exists=$(docker ps -a --filter "name=fingood-postgres" --format "{{.Names}}" 2>/dev/null)
    local redis_exists=$(docker ps -a --filter "name=fingood-redis" --format "{{.Names}}" 2>/dev/null)
    
    # Check if containers are healthy
    local postgres_healthy=$(docker ps --filter "name=fingood-postgres" --filter "health=healthy" --format "{{.Names}}" 2>/dev/null)
    local redis_healthy=$(docker ps --filter "name=fingood-redis" --filter "health=healthy" --format "{{.Names}}" 2>/dev/null)
    
    # If containers exist but aren't healthy, restart them
    if [ -n "$postgres_exists" ] && [ -z "$postgres_healthy" ]; then
        log_warning "PostgreSQL container exists but isn't healthy. Restarting..."
        docker stop fingood-postgres 2>/dev/null || true
        docker rm fingood-postgres 2>/dev/null || true
    fi
    
    if [ -n "$redis_exists" ] && [ -z "$redis_healthy" ]; then
        log_warning "Redis container exists but isn't healthy. Restarting..."
        docker stop fingood-redis 2>/dev/null || true
        docker rm fingood-redis 2>/dev/null || true
    fi
    
    # Start containers if not healthy
    if [ -z "$postgres_healthy" ] || [ -z "$redis_healthy" ]; then
        log_info "Starting database services..."
        docker-compose -f docker-compose.db-only.yml up -d
        
        # Wait for health checks
        log_info "Waiting for database health checks..."
        local timeout=60
        local count=0
        
        while [ $count -lt $timeout ]; do
            local pg_health=$(docker ps --filter "name=fingood-postgres" --filter "health=healthy" --format "{{.Names}}" 2>/dev/null)
            local redis_health=$(docker ps --filter "name=fingood-redis" --filter "health=healthy" --format "{{.Names}}" 2>/dev/null)
            
            if [ -n "$pg_health" ] && [ -n "$redis_health" ]; then
                log_success "Database services are healthy"
                return 0
            fi
            
            sleep 2
            count=$((count + 2))
            echo -n "."
        done
        
        echo ""
        log_error "Database services failed to become healthy"
        exit 1
    else
        log_success "Database containers are already healthy"
    fi
}

# Function to verify environment setup
verify_environment() {
    log_info "Verifying environment setup..."
    
    # Check .env file
    if [ ! -f ".env" ]; then
        log_warning ".env file not found. Creating default..."
        cat > .env << 'EOF'
POSTGRES_PASSWORD=development123
SECRET_KEY=development-secret-key-change-in-production-minimum-32-characters
COMPLIANCE_SECRET_KEY=compliance-development-secret-key-change-in-production-32-chars
CSRF_SECRET_KEY=csrf_dev_secure_key_2024_min_32_chars_long
EOF
    fi
    
    # Check backend virtual environment
    if [ ! -d "backend/venv" ]; then
        log_error "Backend virtual environment not found. Please run ./dev-setup.sh first."
        exit 1
    fi
    
    # Check frontend dependencies
    if [ ! -d "node_modules" ]; then
        log_error "Frontend dependencies not found. Please run ./dev-setup.sh first."
        exit 1
    fi
    
    log_success "Environment setup verified"
}

# Function to start backend server with logging
start_backend() {
    log_info "Starting backend server..."
    
    # Kill any existing processes on backend port
    kill_port_processes $BACKEND_PORT
    
    # Ensure port is available
    if ! is_port_available $BACKEND_PORT; then
        log_error "Port $BACKEND_PORT is still in use after cleanup"
        exit 1
    fi
    
    # Start backend with logging
    cd backend
    source venv/bin/activate
    
    DATABASE_URL=postgresql://postgres:development123@localhost:5432/fingood \
    REDIS_URL=redis://:secure_dev_password_2024@localhost:6379/0 \
    SECRET_KEY=CziCeepOcIQXoOSmRFTR6JLPWkZ1Zr3y9slo0FLS3Tk \
    COMPLIANCE_SECRET_KEY=compliance_dev_secure_key_2024_min_32_chars_long \
    CSRF_SECRET_KEY=csrf_dev_secure_key_2024_min_32_chars_long \
    ENFORCE_HTTPS=false \
    COOKIE_SECURE=false \
    python main.py > "../$LOG_DIR/backend.log" 2>&1 &
    
    BACKEND_PID=$!
    cd ..
    
    # Wait for backend to be ready
    if ! wait_for_service "http://localhost:$BACKEND_PORT/health" "Backend server" 30; then
        log_error "Backend server failed to start. Check logs: $LOG_DIR/backend.log"
        if [ -f "$LOG_DIR/backend.log" ]; then
            echo "Last 20 lines from backend log:"
            tail -20 "$LOG_DIR/backend.log"
        fi
        exit 1
    fi
    
    log_success "Backend server started (PID: $BACKEND_PID)"
}

# Function to start frontend server with logging
start_frontend() {
    log_info "Starting frontend server..."
    
    # Kill any existing processes on frontend port
    kill_port_processes $FRONTEND_PORT
    
    # Ensure port is available
    if ! is_port_available $FRONTEND_PORT; then
        log_error "Port $FRONTEND_PORT is still in use after cleanup"
        exit 1
    fi
    
    # Start frontend with logging
    npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    
    # Wait for frontend to be ready
    if ! wait_for_service "http://localhost:$FRONTEND_PORT" "Frontend server" 30; then
        log_error "Frontend server failed to start. Check logs: $LOG_DIR/frontend.log"
        if [ -f "$LOG_DIR/frontend.log" ]; then
            echo "Last 20 lines from frontend log:"
            tail -20 "$LOG_DIR/frontend.log"
        fi
        exit 1
    fi
    
    log_success "Frontend server started (PID: $FRONTEND_PID)"
}

# Function to run comprehensive health checks
run_health_checks() {
    log_info "Running comprehensive health checks..."
    
    local health_failed=false
    
    # Backend health check
    if ! curl -s -f "http://localhost:$BACKEND_PORT/health" >/dev/null; then
        log_error "Backend health check failed"
        health_failed=true
    else
        log_success "Backend health check passed"
    fi
    
    # Frontend health check
    if ! curl -s -f "http://localhost:$FRONTEND_PORT" >/dev/null; then
        log_error "Frontend health check failed"
        health_failed=true
    else
        log_success "Frontend health check passed"
    fi
    
    # API documentation check
    if ! curl -s -f "http://localhost:$BACKEND_PORT/docs" >/dev/null; then
        log_warning "API documentation endpoint not responding"
    else
        log_success "API documentation accessible"
    fi
    
    # Database connectivity check
    if ! docker exec fingood-postgres pg_isready -U postgres >/dev/null 2>&1; then
        log_error "PostgreSQL connectivity check failed"
        health_failed=true
    else
        log_success "PostgreSQL connectivity check passed"
    fi
    
    # Redis connectivity check
    if ! docker exec fingood-redis redis-cli -a secure_dev_password_2024 ping >/dev/null 2>&1; then
        log_error "Redis connectivity check failed"
        health_failed=true
    else
        log_success "Redis connectivity check passed"
    fi
    
    # Analytics Engine import check
    cd backend
    source venv/bin/activate
    if ! python -c "from app.services.analytics_engine import AnalyticsEngine; print('Analytics Engine OK')" >/dev/null 2>&1; then
        log_error "Analytics Engine import check failed"
        health_failed=true
    else
        log_success "Analytics Engine import check passed"
    fi
    cd ..
    
    if [ "$health_failed" = true ]; then
        log_error "Some health checks failed. Check the logs for details."
        return 1
    fi
    
    log_success "All health checks passed!"
    return 0
}

# Function to start log monitoring
start_log_monitoring() {
    log_info "Starting log monitoring..."
    
    # Create log monitoring script
    cat > "$LOG_DIR/monitor.sh" << 'EOF'
#!/bin/bash
echo "=== Backend Logs ==="
tail -f logs/dev/backend.log &
BACKEND_TAIL_PID=$!

echo "=== Frontend Logs ==="
tail -f logs/dev/frontend.log &
FRONTEND_TAIL_PID=$!

# Cleanup function
cleanup_monitor() {
    kill $BACKEND_TAIL_PID $FRONTEND_TAIL_PID 2>/dev/null || true
    exit 0
}

trap cleanup_monitor SIGINT SIGTERM
wait
EOF
    
    chmod +x "$LOG_DIR/monitor.sh"
    log_success "Log monitoring available at: ./$LOG_DIR/monitor.sh"
}

# Function to display final status
display_status() {
    echo ""
    echo "================================================="
    log_success "🎉 FinGood Development Environment Ready!"
    echo "================================================="
    echo ""
    echo "📱 Services:"
    echo "   🌐 Frontend:    http://localhost:$FRONTEND_PORT"
    echo "   🔧 Backend:     http://localhost:$BACKEND_PORT"
    echo "   📚 API Docs:    http://localhost:$BACKEND_PORT/docs"
    echo "   📊 Analytics:   http://localhost:$BACKEND_PORT/api/v1/analytics/*"
    echo ""
    echo "🗄️  Database:"
    echo "   🐘 PostgreSQL:  localhost:5432 (fingood/postgres:development123)"
    echo "   📊 Redis:       localhost:6379 (password: secure_dev_password_2024)"
    echo ""
    echo "📋 Process Management:"
    echo "   Backend PID:    $BACKEND_PID"
    echo "   Frontend PID:   $FRONTEND_PID"
    echo ""
    echo "📝 Logs:"
    echo "   Backend:        $LOG_DIR/backend.log"
    echo "   Frontend:       $LOG_DIR/frontend.log"
    echo "   Monitor:        ./$LOG_DIR/monitor.sh"
    echo ""
    echo "💡 Commands:"
    echo "   Health Check:   curl http://localhost:$BACKEND_PORT/health"
    echo "   Stop All:       Ctrl+C or kill $BACKEND_PID $FRONTEND_PID"
    echo "   View Logs:      ./$LOG_DIR/monitor.sh"
    echo ""
    log_info "Press Ctrl+C to stop all services"
}

# Main execution flow
main() {
    check_docker
    verify_environment
    manage_database_containers
    start_backend
    start_frontend
    
    if run_health_checks; then
        start_log_monitoring
        display_status
        
        # Wait for processes to complete
        wait $BACKEND_PID $FRONTEND_PID
    else
        log_error "Health checks failed. Stopping services."
        exit 1
    fi
}

# Run main function
main "$@"