#!/bin/bash
# =============================================================================
# PredictBot Stack - Backup Script
# =============================================================================
# Comprehensive backup script for database, configuration, and logs.
#
# Usage:
#   ./scripts/backup.sh                      # Create backup in default location
#   ./scripts/backup.sh --output /backup     # Specify output directory
#   ./scripts/backup.sh --include-logs       # Include log files
#   ./scripts/backup.sh --help               # Show help
#
# Backup Contents:
#   - PostgreSQL database dump
#   - Redis RDB snapshot
#   - Configuration files
#   - Environment file (sanitized)
#   - Logs (optional)
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
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="$PROJECT_DIR/backups"
BACKUP_NAME="predictbot_backup_$TIMESTAMP"
INCLUDE_LOGS=false
COMPRESS=true
RETENTION_DAYS=30
SANITIZE_ENV=true

# =============================================================================
# Functions
# =============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                     PredictBot Stack                              ║"
    echo "║                     Backup Utility                                ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_help() {
    echo "PredictBot Stack - Backup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --output DIR         Output directory (default: ./backups)"
    echo "  --name NAME          Backup name (default: predictbot_backup_TIMESTAMP)"
    echo "  --include-logs       Include log files in backup"
    echo "  --no-compress        Don't compress the backup"
    echo "  --no-sanitize        Don't sanitize sensitive data in .env backup"
    echo "  --retention DAYS     Delete backups older than N days (default: 30)"
    echo "  --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Basic backup"
    echo "  $0 --output /backup --include-logs   # Full backup to /backup"
    echo "  $0 --retention 7                     # Keep only 7 days of backups"
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
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check if services are running
    cd "$PROJECT_DIR"
    if ! docker compose ps postgres --format json 2>/dev/null | grep -q "running"; then
        log_warning "PostgreSQL is not running. Database backup will be skipped."
    fi
    
    if ! docker compose ps redis --format json 2>/dev/null | grep -q "running"; then
        log_warning "Redis is not running. Redis backup will be skipped."
    fi
}

create_backup_dir() {
    BACKUP_PATH="$OUTPUT_DIR/$BACKUP_NAME"
    
    log_info "Creating backup directory: $BACKUP_PATH"
    mkdir -p "$BACKUP_PATH"
    mkdir -p "$BACKUP_PATH/database"
    mkdir -p "$BACKUP_PATH/config"
    
    if [ "$INCLUDE_LOGS" = true ]; then
        mkdir -p "$BACKUP_PATH/logs"
    fi
}

backup_postgres() {
    log_info "Backing up PostgreSQL database..."
    
    cd "$PROJECT_DIR"
    
    # Check if postgres is running
    if ! docker compose ps postgres --format json 2>/dev/null | grep -q "running"; then
        log_warning "PostgreSQL is not running. Skipping database backup."
        return
    fi
    
    # Get database credentials from .env
    source "$PROJECT_DIR/.env" 2>/dev/null || true
    
    # Perform backup
    docker compose exec -T postgres pg_dump \
        -U predictbot \
        -d predictbot \
        --format=custom \
        --file=/tmp/predictbot_backup.dump 2>/dev/null
    
    # Copy backup out of container
    docker compose cp postgres:/tmp/predictbot_backup.dump "$BACKUP_PATH/database/postgres.dump"
    
    # Also create a plain SQL backup for portability
    docker compose exec -T postgres pg_dump \
        -U predictbot \
        -d predictbot \
        --format=plain \
        > "$BACKUP_PATH/database/postgres.sql" 2>/dev/null
    
    # Clean up temp file in container
    docker compose exec -T postgres rm -f /tmp/predictbot_backup.dump 2>/dev/null || true
    
    log_success "PostgreSQL backup completed"
}

backup_redis() {
    log_info "Backing up Redis data..."
    
    cd "$PROJECT_DIR"
    
    # Check if redis is running
    if ! docker compose ps redis --format json 2>/dev/null | grep -q "running"; then
        log_warning "Redis is not running. Skipping Redis backup."
        return
    fi
    
    # Trigger Redis save
    docker compose exec -T redis redis-cli BGSAVE 2>/dev/null || true
    sleep 2
    
    # Copy RDB file
    docker compose cp redis:/data/dump.rdb "$BACKUP_PATH/database/redis.rdb" 2>/dev/null || {
        log_warning "Could not copy Redis dump file"
    }
    
    log_success "Redis backup completed"
}

backup_config() {
    log_info "Backing up configuration files..."
    
    # Copy config directory
    if [ -d "$PROJECT_DIR/config" ]; then
        cp -r "$PROJECT_DIR/config" "$BACKUP_PATH/config/"
    fi
    
    # Copy docker-compose files
    cp "$PROJECT_DIR/docker-compose.yml" "$BACKUP_PATH/config/" 2>/dev/null || true
    cp "$PROJECT_DIR/docker-compose.prod.yml" "$BACKUP_PATH/config/" 2>/dev/null || true
    cp "$PROJECT_DIR/docker-compose.override.yml" "$BACKUP_PATH/config/" 2>/dev/null || true
    
    # Copy .env file (sanitized or full)
    if [ "$SANITIZE_ENV" = true ]; then
        log_info "Creating sanitized .env backup..."
        # Replace sensitive values with placeholders
        sed -E \
            -e 's/(PASSWORD=).*/\1<REDACTED>/' \
            -e 's/(SECRET=).*/\1<REDACTED>/' \
            -e 's/(API_KEY=).*/\1<REDACTED>/' \
            -e 's/(PRIVATE_KEY=).*/\1<REDACTED>/' \
            -e 's/(WEBHOOK_URL=).*/\1<REDACTED>/' \
            "$PROJECT_DIR/.env" > "$BACKUP_PATH/config/.env.sanitized"
    else
        cp "$PROJECT_DIR/.env" "$BACKUP_PATH/config/.env"
        log_warning ".env file backed up with sensitive data (use --sanitize for production)"
    fi
    
    # Copy .gitmodules
    cp "$PROJECT_DIR/.gitmodules" "$BACKUP_PATH/config/" 2>/dev/null || true
    
    log_success "Configuration backup completed"
}

backup_logs() {
    if [ "$INCLUDE_LOGS" = false ]; then
        return
    fi
    
    log_info "Backing up log files..."
    
    # Copy logs from volume
    cd "$PROJECT_DIR"
    
    # Create temporary container to access volume
    docker run --rm \
        -v predictbot-stack_predictbot-logs:/logs:ro \
        -v "$BACKUP_PATH/logs":/backup \
        alpine \
        sh -c "cp -r /logs/* /backup/ 2>/dev/null || true"
    
    # Also export recent Docker logs
    log_info "Exporting Docker container logs..."
    for container in $(docker compose ps -q 2>/dev/null); do
        name=$(docker inspect --format '{{.Name}}' "$container" | sed 's/\///')
        docker logs "$container" > "$BACKUP_PATH/logs/${name}.log" 2>&1 || true
    done
    
    log_success "Log backup completed"
}

create_manifest() {
    log_info "Creating backup manifest..."
    
    cat > "$BACKUP_PATH/manifest.json" << EOF
{
    "backup_name": "$BACKUP_NAME",
    "timestamp": "$(date -Iseconds)",
    "version": "1.0.0",
    "contents": {
        "postgres": $([ -f "$BACKUP_PATH/database/postgres.dump" ] && echo "true" || echo "false"),
        "redis": $([ -f "$BACKUP_PATH/database/redis.rdb" ] && echo "true" || echo "false"),
        "config": true,
        "logs": $INCLUDE_LOGS
    },
    "sizes": {
        "postgres": "$(du -sh "$BACKUP_PATH/database/postgres.dump" 2>/dev/null | cut -f1 || echo "0")",
        "redis": "$(du -sh "$BACKUP_PATH/database/redis.rdb" 2>/dev/null | cut -f1 || echo "0")",
        "config": "$(du -sh "$BACKUP_PATH/config" 2>/dev/null | cut -f1 || echo "0")",
        "logs": "$(du -sh "$BACKUP_PATH/logs" 2>/dev/null | cut -f1 || echo "0")"
    },
    "host": "$(hostname)",
    "docker_version": "$(docker --version | cut -d' ' -f3 | tr -d ',')"
}
EOF
    
    log_success "Manifest created"
}

compress_backup() {
    if [ "$COMPRESS" = false ]; then
        return
    fi
    
    log_info "Compressing backup..."
    
    cd "$OUTPUT_DIR"
    tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
    rm -rf "$BACKUP_NAME"
    
    BACKUP_PATH="${OUTPUT_DIR}/${BACKUP_NAME}.tar.gz"
    
    log_success "Backup compressed: ${BACKUP_NAME}.tar.gz"
}

cleanup_old_backups() {
    if [ "$RETENTION_DAYS" -le 0 ]; then
        return
    fi
    
    log_info "Cleaning up backups older than $RETENTION_DAYS days..."
    
    # Find and delete old backups
    find "$OUTPUT_DIR" -name "predictbot_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    find "$OUTPUT_DIR" -type d -name "predictbot_backup_*" -mtime +$RETENTION_DAYS -exec rm -rf {} + 2>/dev/null || true
    
    log_success "Old backups cleaned up"
}

print_summary() {
    echo ""
    log_info "Backup Summary:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Backup Name:     $BACKUP_NAME"
    echo "  Location:        $BACKUP_PATH"
    
    if [ "$COMPRESS" = true ]; then
        echo "  Size:            $(du -sh "$BACKUP_PATH" 2>/dev/null | cut -f1)"
    else
        echo "  Size:            $(du -sh "$BACKUP_PATH" 2>/dev/null | cut -f1)"
    fi
    
    echo "  Contents:"
    echo "    • PostgreSQL:  $([ -f "$OUTPUT_DIR/${BACKUP_NAME}.tar.gz" ] || [ -f "$BACKUP_PATH/database/postgres.dump" ] && echo "✓" || echo "✗")"
    echo "    • Redis:       $([ -f "$OUTPUT_DIR/${BACKUP_NAME}.tar.gz" ] || [ -f "$BACKUP_PATH/database/redis.rdb" ] && echo "✓" || echo "✗")"
    echo "    • Config:      ✓"
    echo "    • Logs:        $([ "$INCLUDE_LOGS" = true ] && echo "✓" || echo "✗")"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    log_info "To restore from this backup:"
    echo "  1. Stop services:  ./scripts/stop.sh"
    echo "  2. Extract backup: tar -xzf ${BACKUP_NAME}.tar.gz"
    echo "  3. Restore DB:     docker compose exec -T postgres psql -U predictbot < postgres.sql"
    echo "  4. Start services: ./scripts/start.sh"
    echo ""
}

# =============================================================================
# Parse Arguments
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --name)
            BACKUP_NAME="$2"
            shift 2
            ;;
        --include-logs)
            INCLUDE_LOGS=true
            shift
            ;;
        --no-compress)
            COMPRESS=false
            shift
            ;;
        --no-sanitize)
            SANITIZE_ENV=false
            shift
            ;;
        --retention)
            RETENTION_DAYS="$2"
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
create_backup_dir
backup_postgres
backup_redis
backup_config
backup_logs
create_manifest
compress_backup
cleanup_old_backups
print_summary

log_success "Backup completed successfully!"
