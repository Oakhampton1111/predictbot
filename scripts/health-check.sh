#!/bin/bash
# =============================================================================
# PredictBot Stack - Health Check Script
# =============================================================================
# Comprehensive health check for all services.
#
# Usage:
#   ./scripts/health-check.sh           # Check all services
#   ./scripts/health-check.sh --json    # Output as JSON
#   ./scripts/health-check.sh --quiet   # Exit code only
#   ./scripts/health-check.sh --help    # Show help
#
# Exit Codes:
#   0 - All services healthy
#   1 - One or more services unhealthy
#   2 - Critical services down
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
OUTPUT_FORMAT="text"
QUIET=false
TIMEOUT=5

# Service definitions
declare -A SERVICES
declare -A SERVICE_URLS
declare -A SERVICE_STATUS
declare -A SERVICE_DETAILS

# =============================================================================
# Functions
# =============================================================================

print_banner() {
    if [ "$QUIET" = true ]; then
        return
    fi
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                     PredictBot Stack                              ║"
    echo "║                     Health Check                                  ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_help() {
    echo "PredictBot Stack - Health Check Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --json               Output results as JSON"
    echo "  --quiet              Suppress output, exit code only"
    echo "  --timeout SECONDS    HTTP request timeout (default: 5)"
    echo "  --help               Show this help message"
    echo ""
    echo "Exit Codes:"
    echo "  0 - All services healthy"
    echo "  1 - One or more services unhealthy"
    echo "  2 - Critical services down"
    echo ""
    echo "Examples:"
    echo "  $0                   # Standard health check"
    echo "  $0 --json            # JSON output for monitoring"
    echo "  $0 --quiet && echo OK  # Use in scripts"
}

log_info() {
    if [ "$QUIET" = false ] && [ "$OUTPUT_FORMAT" = "text" ]; then
        echo -e "${BLUE}[INFO]${NC} $1"
    fi
}

check_container_health() {
    local container_name="$1"
    local display_name="$2"
    
    cd "$PROJECT_DIR"
    
    # Check if container exists and is running
    local status=$(docker compose ps "$container_name" --format json 2>/dev/null | head -1)
    
    if [ -z "$status" ]; then
        SERVICE_STATUS["$display_name"]="not_found"
        SERVICE_DETAILS["$display_name"]="Container not found"
        return 1
    fi
    
    local state=$(echo "$status" | grep -o '"State":"[^"]*"' | cut -d'"' -f4)
    local health=$(echo "$status" | grep -o '"Health":"[^"]*"' | cut -d'"' -f4)
    
    if [ "$state" != "running" ]; then
        SERVICE_STATUS["$display_name"]="stopped"
        SERVICE_DETAILS["$display_name"]="Container not running (state: $state)"
        return 1
    fi
    
    if [ -n "$health" ]; then
        if [ "$health" = "healthy" ]; then
            SERVICE_STATUS["$display_name"]="healthy"
            SERVICE_DETAILS["$display_name"]="Running and healthy"
            return 0
        elif [ "$health" = "starting" ]; then
            SERVICE_STATUS["$display_name"]="starting"
            SERVICE_DETAILS["$display_name"]="Container starting up"
            return 0
        else
            SERVICE_STATUS["$display_name"]="unhealthy"
            SERVICE_DETAILS["$display_name"]="Health check failed"
            return 1
        fi
    else
        SERVICE_STATUS["$display_name"]="running"
        SERVICE_DETAILS["$display_name"]="Running (no health check)"
        return 0
    fi
}

check_http_health() {
    local url="$1"
    local display_name="$2"
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        SERVICE_STATUS["$display_name"]="healthy"
        SERVICE_DETAILS["$display_name"]="HTTP 200 OK"
        return 0
    elif [ "$response" = "000" ]; then
        SERVICE_STATUS["$display_name"]="unreachable"
        SERVICE_DETAILS["$display_name"]="Connection failed"
        return 1
    else
        SERVICE_STATUS["$display_name"]="unhealthy"
        SERVICE_DETAILS["$display_name"]="HTTP $response"
        return 1
    fi
}

check_postgres() {
    cd "$PROJECT_DIR"
    
    if docker compose exec -T postgres pg_isready -U predictbot &>/dev/null; then
        SERVICE_STATUS["PostgreSQL"]="healthy"
        SERVICE_DETAILS["PostgreSQL"]="Accepting connections"
        return 0
    else
        SERVICE_STATUS["PostgreSQL"]="unhealthy"
        SERVICE_DETAILS["PostgreSQL"]="Not accepting connections"
        return 1
    fi
}

check_redis() {
    cd "$PROJECT_DIR"
    
    local response=$(docker compose exec -T redis redis-cli ping 2>/dev/null || echo "")
    
    if [ "$response" = "PONG" ]; then
        SERVICE_STATUS["Redis"]="healthy"
        SERVICE_DETAILS["Redis"]="PONG response received"
        return 0
    else
        SERVICE_STATUS["Redis"]="unhealthy"
        SERVICE_DETAILS["Redis"]="No PONG response"
        return 1
    fi
}

print_status_icon() {
    local status="$1"
    case "$status" in
        healthy|running)
            echo -e "${GREEN}✓${NC}"
            ;;
        starting)
            echo -e "${YELLOW}○${NC}"
            ;;
        unhealthy|stopped|unreachable|not_found)
            echo -e "${RED}✗${NC}"
            ;;
        *)
            echo -e "${YELLOW}?${NC}"
            ;;
    esac
}

print_text_results() {
    echo ""
    echo "Service Health Status"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Core Services
    echo -e "${BLUE}Core Services:${NC}"
    for service in "PostgreSQL" "Redis" "Orchestrator"; do
        local status="${SERVICE_STATUS[$service]:-unknown}"
        local details="${SERVICE_DETAILS[$service]:-No details}"
        local icon=$(print_status_icon "$status")
        printf "  %s %-20s %s\n" "$icon" "$service" "($details)"
    done
    echo ""
    
    # Trading Modules
    echo -e "${BLUE}Trading Modules:${NC}"
    for service in "Polymarket Arb" "Polymarket MM" "Polymarket Spike" "Kalshi AI" "Manifold MM"; do
        local status="${SERVICE_STATUS[$service]:-not_found}"
        local details="${SERVICE_DETAILS[$service]:-Not deployed}"
        local icon=$(print_status_icon "$status")
        printf "  %s %-20s %s\n" "$icon" "$service" "($details)"
    done
    echo ""
    
    # AI Stack
    echo -e "${BLUE}AI Stack:${NC}"
    for service in "MCP Server" "Polyseer" "AI Orchestrator" "Ollama"; do
        local status="${SERVICE_STATUS[$service]:-not_found}"
        local details="${SERVICE_DETAILS[$service]:-Not deployed}"
        local icon=$(print_status_icon "$status")
        printf "  %s %-20s %s\n" "$icon" "$service" "($details)"
    done
    echo ""
    
    # Monitoring
    echo -e "${BLUE}Monitoring:${NC}"
    for service in "Prometheus" "Grafana" "Loki"; do
        local status="${SERVICE_STATUS[$service]:-not_found}"
        local details="${SERVICE_DETAILS[$service]:-Not deployed}"
        local icon=$(print_status_icon "$status")
        printf "  %s %-20s %s\n" "$icon" "$service" "($details)"
    done
    echo ""
    
    # Admin
    echo -e "${BLUE}Admin:${NC}"
    for service in "Admin Portal"; do
        local status="${SERVICE_STATUS[$service]:-not_found}"
        local details="${SERVICE_DETAILS[$service]:-Not deployed}"
        local icon=$(print_status_icon "$status")
        printf "  %s %-20s %s\n" "$icon" "$service" "($details)"
    done
    echo ""
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

print_json_results() {
    echo "{"
    echo "  \"timestamp\": \"$(date -Iseconds)\","
    echo "  \"overall_status\": \"$OVERALL_STATUS\","
    echo "  \"services\": {"
    
    local first=true
    for service in "${!SERVICE_STATUS[@]}"; do
        if [ "$first" = true ]; then
            first=false
        else
            echo ","
        fi
        local status="${SERVICE_STATUS[$service]}"
        local details="${SERVICE_DETAILS[$service]}"
        echo -n "    \"$service\": {\"status\": \"$status\", \"details\": \"$details\"}"
    done
    
    echo ""
    echo "  }"
    echo "}"
}

calculate_overall_status() {
    local critical_down=false
    local any_unhealthy=false
    
    # Check critical services
    for service in "PostgreSQL" "Redis" "Orchestrator"; do
        local status="${SERVICE_STATUS[$service]:-not_found}"
        if [ "$status" != "healthy" ] && [ "$status" != "running" ] && [ "$status" != "starting" ]; then
            critical_down=true
        fi
    done
    
    # Check all services
    for service in "${!SERVICE_STATUS[@]}"; do
        local status="${SERVICE_STATUS[$service]}"
        if [ "$status" = "unhealthy" ] || [ "$status" = "stopped" ] || [ "$status" = "unreachable" ]; then
            any_unhealthy=true
        fi
    done
    
    if [ "$critical_down" = true ]; then
        OVERALL_STATUS="critical"
        return 2
    elif [ "$any_unhealthy" = true ]; then
        OVERALL_STATUS="degraded"
        return 1
    else
        OVERALL_STATUS="healthy"
        return 0
    fi
}

print_summary() {
    if [ "$QUIET" = true ]; then
        return
    fi
    
    local healthy_count=0
    local total_count=0
    
    for service in "${!SERVICE_STATUS[@]}"; do
        total_count=$((total_count + 1))
        local status="${SERVICE_STATUS[$service]}"
        if [ "$status" = "healthy" ] || [ "$status" = "running" ]; then
            healthy_count=$((healthy_count + 1))
        fi
    done
    
    echo ""
    case "$OVERALL_STATUS" in
        healthy)
            echo -e "${GREEN}Overall Status: HEALTHY${NC} ($healthy_count/$total_count services)"
            ;;
        degraded)
            echo -e "${YELLOW}Overall Status: DEGRADED${NC} ($healthy_count/$total_count services)"
            ;;
        critical)
            echo -e "${RED}Overall Status: CRITICAL${NC} ($healthy_count/$total_count services)"
            ;;
    esac
    echo ""
}

# =============================================================================
# Parse Arguments
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --json)
            OUTPUT_FORMAT="json"
            shift
            ;;
        --quiet)
            QUIET=true
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --help|-h)
            print_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            print_help
            exit 1
            ;;
    esac
done

# =============================================================================
# Main
# =============================================================================

print_banner

log_info "Checking service health..."

# Check Core Services
check_postgres || true
check_redis || true
check_container_health "orchestrator" "Orchestrator" || true

# Check Trading Modules
check_container_health "polymarket-arb" "Polymarket Arb" || true
check_container_health "polymarket-mm" "Polymarket MM" || true
check_container_health "polymarket-spike" "Polymarket Spike" || true
check_container_health "kalshi-ai" "Kalshi AI" || true
check_container_health "manifold-mm" "Manifold MM" || true

# Check AI Stack
check_container_health "mcp-server" "MCP Server" || true
check_container_health "polyseer" "Polyseer" || true
check_container_health "ai_orchestrator" "AI Orchestrator" || true
check_container_health "ollama" "Ollama" || true

# Check Monitoring
check_container_health "prometheus" "Prometheus" || true
check_container_health "grafana" "Grafana" || true
check_container_health "loki" "Loki" || true

# Check Admin
check_container_health "admin_portal" "Admin Portal" || true

# Calculate overall status
calculate_overall_status
EXIT_CODE=$?

# Output results
if [ "$OUTPUT_FORMAT" = "json" ]; then
    print_json_results
elif [ "$QUIET" = false ]; then
    print_text_results
    print_summary
fi

exit $EXIT_CODE
