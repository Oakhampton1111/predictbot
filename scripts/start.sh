#!/bin/bash
# =============================================================================
# PredictBot Stack - Start Script
# =============================================================================
# One-command startup script with profile selection and health checks.
#
# Usage:
#   ./scripts/start.sh                    # Start with default profile (full)
#   ./scripts/start.sh --profile minimal  # Start minimal services
#   ./scripts/start.sh --dry-run          # Force dry run mode
#   ./scripts/start.sh --help             # Show help
#
# Profiles:
#   full          - All services (default)
#   minimal       - Core services only (no monitoring)
#   arbitrage     - Arbitrage bot only
#   market-making - Market making bots
#   ai-trading    - AI trading + MCP + Polyseer
#   spike-trading - Spike trading bot
#   monitoring    - Monitoring stack only
#   admin         - Admin portal only
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
PROFILE="full"
DRY_RUN=""
BUILD=false
DETACH=true
WAIT_HEALTH=true
HEALTH_TIMEOUT=120

# =============================================================================
# Functions
# =============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                     PredictBot Stack                              ║"
    echo "║                     Starting Services                             ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_help() {
    echo "PredictBot Stack - Start Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --profile PROFILE    Docker Compose profile to use (default: full)"
    echo "  --dry-run            Force dry run mode (paper trading)"
    echo "  --build              Rebuild images before starting"
    echo "  --no-detach          Run in foreground (don't detach)"
    echo "  --no-health-check    Skip health check after startup"
    echo "  --timeout SECONDS    Health check timeout (default: 120)"
    echo "  --help               Show this help message"
    echo ""
    echo "Profiles:"
    echo "  full          - All services (default)"
    echo "  minimal       - Core + trading (no monitoring)"
    echo "  arbitrage     - Arbitrage bot only"
    echo "  market-making - Market making bots"
    echo "  ai-trading    - AI trading + MCP + Polyseer"
    echo "  spike-trading - Spike trading bot"
    echo "  monitoring    - Monitoring stack only"
    echo "  admin         - Admin portal only"
    echo "  ai            - AI stack (Ollama + AI Orchestrator)"
    echo ""
    echo "Examples:"
    echo "  $0                           # Start all services"
    echo "  $0 --profile minimal         # Start without monitoring"
    echo "  $0 --profile full --dry-run  # Start all in paper trading mode"
    echo "  $0 --build                   # Rebuild and start"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose v2."
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    # Check .env file
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        log_error ".env file not found. Please copy .env.template to .env and configure it."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

check_config() {
    log_info "Validating configuration..."
    
    # Run config validation if Python is available
    if command -v python3 &> /dev/null; then
        if [ -f "$PROJECT_DIR/scripts/validate_config.py" ]; then
            if ! python3 "$PROJECT_DIR/scripts/validate_config.py" --quiet 2>/dev/null; then
                log_warning "Configuration validation failed. Check config/config.yml"
            fi
        fi
        
        if [ -f "$PROJECT_DIR/scripts/validate_secrets.py" ]; then
            if ! python3 "$PROJECT_DIR/scripts/validate_secrets.py" --quiet 2>/dev/null; then
                log_warning "Secrets validation failed. Check .env file"
            fi
        fi
    fi
    
    # Check dry run status
    if [ -n "$DRY_RUN" ]; then
        log_info "Dry run mode: ENABLED (forced via --dry-run)"
    else
        DRY_RUN_VALUE=$(grep -E "^DRY_RUN=" "$PROJECT_DIR/.env" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [ "$DRY_RUN_VALUE" = "1" ] || [ "$DRY_RUN_VALUE" = "true" ]; then
            log_info "Dry run mode: ENABLED (from .env)"
        else
            log_warning "Dry run mode: DISABLED - Live trading is active!"
            echo -e "${YELLOW}Press Ctrl+C within 5 seconds to cancel...${NC}"
            sleep 5
        fi
    fi
}

create_network() {
    log_info "Ensuring Docker network exists..."
    
    if ! docker network inspect predictbot-network &> /dev/null; then
        docker network create predictbot-network
        log_success "Created Docker network: predictbot-network"
    fi
}

build_images() {
    if [ "$BUILD" = true ]; then
        log_info "Building Docker images..."
        cd "$PROJECT_DIR"
        docker compose --profile "$PROFILE" build
        log_success "Docker images built"
    fi
}

start_services() {
    log_info "Starting services with profile: $PROFILE"
    
    cd "$PROJECT_DIR"
    
    # Build command
    CMD="docker compose --profile $PROFILE up"
    
    if [ "$DETACH" = true ]; then
        CMD="$CMD -d"
    fi
    
    # Add dry run environment variable if specified
    if [ -n "$DRY_RUN" ]; then
        export DRY_RUN=1
    fi
    
    # Execute
    eval $CMD
    
    if [ "$DETACH" = true ]; then
        log_success "Services started in background"
    fi
}

wait_for_health() {
    if [ "$WAIT_HEALTH" = false ]; then
        return
    fi
    
    log_info "Waiting for services to become healthy (timeout: ${HEALTH_TIMEOUT}s)..."
    
    local start_time=$(date +%s)
    local all_healthy=false
    
    while [ $(($(date +%s) - start_time)) -lt $HEALTH_TIMEOUT ]; do
        # Check if all containers are healthy or running
        local unhealthy=$(docker compose --profile "$PROFILE" ps --format json 2>/dev/null | \
            grep -c '"Health":"unhealthy"' || echo "0")
        local starting=$(docker compose --profile "$PROFILE" ps --format json 2>/dev/null | \
            grep -c '"Health":"starting"' || echo "0")
        
        if [ "$unhealthy" = "0" ] && [ "$starting" = "0" ]; then
            all_healthy=true
            break
        fi
        
        echo -n "."
        sleep 5
    done
    
    echo ""
    
    if [ "$all_healthy" = true ]; then
        log_success "All services are healthy"
    else
        log_warning "Some services may not be fully healthy yet"
        log_info "Run './scripts/health-check.sh' for detailed status"
    fi
}

print_status() {
    echo ""
    log_info "Service Status:"
    echo ""
    
    cd "$PROJECT_DIR"
    docker compose --profile "$PROFILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    log_info "Access Points:"
    echo "  • Admin Portal:    http://localhost:3003"
    echo "  • Grafana:         http://localhost:3002"
    echo "  • Prometheus:      http://localhost:9090"
    echo "  • Orchestrator:    http://localhost:8080"
    echo "  • AI Orchestrator: http://localhost:8081"
    echo ""
    log_info "Useful Commands:"
    echo "  • View logs:       docker compose logs -f"
    echo "  • Stop services:   ./scripts/stop.sh"
    echo "  • Health check:    ./scripts/health-check.sh"
    echo ""
}

# =============================================================================
# Parse Arguments
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            PROFILE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="1"
            shift
            ;;
        --build)
            BUILD=true
            shift
            ;;
        --no-detach)
            DETACH=false
            shift
            ;;
        --no-health-check)
            WAIT_HEALTH=false
            shift
            ;;
        --timeout)
            HEALTH_TIMEOUT="$2"
            shift 2
            ;;
        --help|-h)
            print_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            print_help
            exit 1
            ;;
    esac
done

# =============================================================================
# Main
# =============================================================================

print_banner
check_prerequisites
check_config
create_network
build_images
start_services

if [ "$DETACH" = true ]; then
    wait_for_health
    print_status
fi

log_success "PredictBot Stack started successfully!"
