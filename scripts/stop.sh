#!/bin/bash
# =============================================================================
# PredictBot Stack - Stop Script
# =============================================================================
# Graceful shutdown script with options to preserve data.
#
# Usage:
#   ./scripts/stop.sh                  # Stop all services
#   ./scripts/stop.sh --remove-volumes # Stop and remove volumes (data loss!)
#   ./scripts/stop.sh --profile full   # Stop specific profile
#   ./scripts/stop.sh --help           # Show help
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
PROFILE=""
REMOVE_VOLUMES=false
REMOVE_ORPHANS=true
TIMEOUT=30
FORCE=false

# =============================================================================
# Functions
# =============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                     PredictBot Stack                              ║"
    echo "║                     Stopping Services                             ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_help() {
    echo "PredictBot Stack - Stop Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --profile PROFILE    Stop specific profile only"
    echo "  --remove-volumes     Remove Docker volumes (WARNING: data loss!)"
    echo "  --no-remove-orphans  Don't remove orphan containers"
    echo "  --timeout SECONDS    Timeout for graceful shutdown (default: 30)"
    echo "  --force              Force stop without confirmation"
    echo "  --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # Stop all services gracefully"
    echo "  $0 --profile monitoring      # Stop only monitoring services"
    echo "  $0 --remove-volumes --force  # Stop and remove all data"
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

confirm_action() {
    if [ "$FORCE" = true ]; then
        return 0
    fi
    
    local message="$1"
    echo -e "${YELLOW}$message${NC}"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Operation cancelled"
        exit 0
    fi
}

get_running_containers() {
    cd "$PROJECT_DIR"
    docker compose ps -q 2>/dev/null | wc -l | tr -d ' '
}

show_current_status() {
    log_info "Current running containers:"
    cd "$PROJECT_DIR"
    docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || echo "No containers running"
    echo ""
}

stop_services() {
    cd "$PROJECT_DIR"
    
    local running=$(get_running_containers)
    
    if [ "$running" = "0" ]; then
        log_info "No containers are currently running"
        return
    fi
    
    log_info "Stopping $running container(s)..."
    
    # Build command
    local CMD="docker compose"
    
    if [ -n "$PROFILE" ]; then
        CMD="$CMD --profile $PROFILE"
    fi
    
    CMD="$CMD down"
    
    if [ "$REMOVE_VOLUMES" = true ]; then
        CMD="$CMD -v"
    fi
    
    if [ "$REMOVE_ORPHANS" = true ]; then
        CMD="$CMD --remove-orphans"
    fi
    
    CMD="$CMD -t $TIMEOUT"
    
    # Execute
    eval $CMD
    
    log_success "Services stopped"
}

cleanup_resources() {
    if [ "$REMOVE_VOLUMES" = true ]; then
        log_info "Volumes have been removed"
    fi
    
    # Clean up any dangling resources
    log_info "Cleaning up dangling resources..."
    docker system prune -f --filter "label=com.docker.compose.project=predictbot-stack" 2>/dev/null || true
}

show_final_status() {
    echo ""
    log_info "Final Status:"
    
    cd "$PROJECT_DIR"
    local remaining=$(get_running_containers)
    
    if [ "$remaining" = "0" ]; then
        log_success "All PredictBot containers stopped"
    else
        log_warning "$remaining container(s) still running"
        docker compose ps --format "table {{.Name}}\t{{.Status}}"
    fi
    
    # Show volume status
    echo ""
    log_info "Data Volumes:"
    docker volume ls --filter "name=predictbot" --format "table {{.Name}}\t{{.Driver}}" 2>/dev/null || echo "No volumes found"
    
    echo ""
    log_info "To restart services, run: ./scripts/start.sh"
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
        --remove-volumes)
            REMOVE_VOLUMES=true
            shift
            ;;
        --no-remove-orphans)
            REMOVE_ORPHANS=false
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
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

# Show current status
show_current_status

# Confirm if removing volumes
if [ "$REMOVE_VOLUMES" = true ]; then
    confirm_action "WARNING: This will delete all data including database, logs, and cached data!"
fi

# Stop services
stop_services

# Cleanup
cleanup_resources

# Show final status
show_final_status

log_success "PredictBot Stack stopped successfully!"
