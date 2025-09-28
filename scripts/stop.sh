#!/bin/bash
# ================================================
# Azimuth Core - Local Personal Finance Planner
# Linux/Mac Stop Script
# ================================================

echo ""
echo "===================================================="
echo "  Azimuth Core - Local Personal Finance Planner"
echo "  Stopping all services..."
echo "===================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Configuration
BACKEND_PORT=8001
FRONTEND_PORT=5173
OLLAMA_PORT=11434

# Kill frontend processes
print_info "Stopping frontend service..."
pkill -f "npm run dev" 2>/dev/null
pkill -f "vite" 2>/dev/null

# Kill any Node.js processes on frontend port
if command -v lsof > /dev/null; then
    FRONTEND_PIDS=$(lsof -ti:$FRONTEND_PORT 2>/dev/null)
    if [ ! -z "$FRONTEND_PIDS" ]; then
        echo "$FRONTEND_PIDS" | xargs kill -9 2>/dev/null
    fi
fi

print_success "Frontend service stopped"

# Kill backend processes
print_info "Stopping backend service..."
pkill -f "uvicorn.*app.main:app" 2>/dev/null
pkill -f "python.*main.py" 2>/dev/null

# Kill any Python processes on backend port
if command -v lsof > /dev/null; then
    BACKEND_PIDS=$(lsof -ti:$BACKEND_PORT 2>/dev/null)
    if [ ! -z "$BACKEND_PIDS" ]; then
        echo "$BACKEND_PIDS" | xargs kill -9 2>/dev/null
    fi
fi

print_success "Backend service stopped"

# Check Ollama service
print_info "Checking Ollama service..."
if pgrep -f "ollama serve" > /dev/null; then
    echo "Ollama is running. Do you want to stop it? (y/N)"
    read -r choice
    case "$choice" in
        y|Y|yes|YES)
            echo "Stopping Ollama..."
            pkill -f "ollama serve" 2>/dev/null
            
            # Kill any processes on Ollama port
            if command -v lsof > /dev/null; then
                OLLAMA_PIDS=$(lsof -ti:$OLLAMA_PORT 2>/dev/null)
                if [ ! -z "$OLLAMA_PIDS" ]; then
                    echo "$OLLAMA_PIDS" | xargs kill -9 2>/dev/null
                fi
            fi
            
            print_success "Ollama stopped"
            ;;
        *)
            print_success "Ollama left running"
            ;;
    esac
else
    print_success "Ollama is not running"
fi

# Clean up any remaining processes on our ports
print_info "Cleaning up remaining processes..."

# Function to kill processes on a specific port
kill_port() {
    local port=$1
    local service_name=$2
    
    if command -v lsof > /dev/null; then
        local pids=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$pids" ]; then
            echo "Killing remaining $service_name processes on port $port..."
            echo "$pids" | xargs kill -9 2>/dev/null
        fi
    elif command -v netstat > /dev/null; then
        # Alternative for systems without lsof
        local pids=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | grep -v '-')
        if [ ! -z "$pids" ]; then
            echo "Killing remaining $service_name processes on port $port..."
            echo "$pids" | xargs kill -9 2>/dev/null
        fi
    fi
}

kill_port $FRONTEND_PORT "frontend"
kill_port $BACKEND_PORT "backend"

# Clean up any orphaned Python/Node processes related to our app
pkill -f "azimuth" 2>/dev/null
pkill -f "main:app" 2>/dev/null

# Clean up log files (optional)
if [ -d "logs" ]; then
    print_info "Cleaning up log files..."
    rm -f logs/*.log 2>/dev/null
fi

# Clean up any temporary files
rm -f .azimuth-*.pid 2>/dev/null

echo ""
echo "===================================================="
print_success "All Azimuth Core services stopped!"
echo "===================================================="
echo ""
echo "Services that were stopped:"
echo "• Frontend (Vue.js development server)"
echo "• Backend (FastAPI server)"
echo "• Associated Node.js and Python processes"
echo ""
echo "Note: Ollama may still be running if you chose to keep it."
echo "You can manually stop it with: pkill -f 'ollama serve'"
echo ""
echo "To restart Azimuth Core, run: ./scripts/start.sh"
echo ""