#!/bin/bash
# =============================================================================
# PredictBot Stack - Setup Script
# =============================================================================
# This script automates the initial setup of the PredictBot trading stack.
# 
# Usage:
#   chmod +x scripts/setup.sh
#   ./scripts/setup.sh
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# =============================================================================
# Main Setup
# =============================================================================

print_header "PredictBot Stack - Setup Script"

# -----------------------------------------------------------------------------
# Step 1: Check Prerequisites
# -----------------------------------------------------------------------------
print_header "Step 1: Checking Prerequisites"

# Check Docker
if command_exists docker; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    print_success "Docker installed: $DOCKER_VERSION"
else
    print_error "Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
    if docker compose version >/dev/null 2>&1; then
        COMPOSE_VERSION=$(docker compose version --short 2>/dev/null || echo "v2+")
    else
        COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
    fi
    print_success "Docker Compose installed: $COMPOSE_VERSION"
else
    print_error "Docker Compose is not installed"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check Git
if command_exists git; then
    GIT_VERSION=$(git --version | cut -d' ' -f3)
    print_success "Git installed: $GIT_VERSION"
else
    print_error "Git is not installed"
    echo "Please install Git: sudo apt-get install git"
    exit 1
fi

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python installed: $PYTHON_VERSION"
else
    print_warning "Python 3 not found - validation scripts may not work"
fi

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root is not recommended for security reasons"
fi

# -----------------------------------------------------------------------------
# Step 2: Initialize Git Submodules
# -----------------------------------------------------------------------------
print_header "Step 2: Initializing Git Submodules"

if [ -f ".gitmodules" ]; then
    print_info "Initializing submodules (this may take a few minutes)..."
    git submodule update --init --recursive
    print_success "Submodules initialized"
else
    print_warning "No .gitmodules file found - skipping submodule initialization"
fi

# -----------------------------------------------------------------------------
# Step 3: Create Directory Structure
# -----------------------------------------------------------------------------
print_header "Step 3: Creating Directory Structure"

# Create required directories
DIRS=("logs" "data" "config")
for dir in "${DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        print_success "Created directory: $dir"
    else
        print_info "Directory exists: $dir"
    fi
done

# Set permissions
chmod 755 logs data config
print_success "Directory permissions set"

# -----------------------------------------------------------------------------
# Step 4: Setup Configuration Files
# -----------------------------------------------------------------------------
print_header "Step 4: Setting Up Configuration Files"

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.template" ]; then
        cp .env.template .env
        chmod 600 .env
        print_success "Created .env from template"
        print_warning "Please edit .env with your API keys before starting"
    else
        print_error ".env.template not found"
    fi
else
    print_info ".env already exists"
fi

# Create config.yml if it doesn't exist
if [ ! -f "config/config.yml" ]; then
    if [ -f "config/config.example.yml" ]; then
        cp config/config.example.yml config/config.yml
        print_success "Created config/config.yml from example"
    else
        print_error "config/config.example.yml not found"
    fi
else
    print_info "config/config.yml already exists"
fi

# -----------------------------------------------------------------------------
# Step 5: Install Python Dependencies (for validation scripts)
# -----------------------------------------------------------------------------
print_header "Step 5: Installing Python Dependencies"

if command_exists python3 && command_exists pip3; then
    print_info "Installing PyYAML for validation scripts..."
    pip3 install --quiet pyyaml 2>/dev/null || pip3 install pyyaml
    print_success "Python dependencies installed"
else
    print_warning "Skipping Python dependencies (pip3 not found)"
fi

# -----------------------------------------------------------------------------
# Step 6: Validate Configuration
# -----------------------------------------------------------------------------
print_header "Step 6: Validating Configuration"

if command_exists python3; then
    # Validate secrets
    if [ -f "scripts/validate_secrets.py" ]; then
        print_info "Validating secrets..."
        if python3 scripts/validate_secrets.py --env .env 2>/dev/null; then
            print_success "Secrets validation passed"
        else
            print_warning "Secrets validation failed - please check .env file"
        fi
    fi
    
    # Validate config
    if [ -f "scripts/validate_config.py" ]; then
        print_info "Validating configuration..."
        if python3 scripts/validate_config.py --config config/config.yml 2>/dev/null; then
            print_success "Configuration validation passed"
        else
            print_warning "Configuration validation failed - please check config.yml"
        fi
    fi
else
    print_warning "Skipping validation (Python not available)"
fi

# -----------------------------------------------------------------------------
# Step 7: Build Docker Images (Optional)
# -----------------------------------------------------------------------------
print_header "Step 7: Docker Images"

echo -e "Would you like to build Docker images now? (y/n)"
read -r BUILD_IMAGES

if [ "$BUILD_IMAGES" = "y" ] || [ "$BUILD_IMAGES" = "Y" ]; then
    print_info "Building Docker images (this may take 10-15 minutes)..."
    
    if docker compose --profile full build; then
        print_success "Docker images built successfully"
    else
        print_error "Docker build failed - check the error messages above"
    fi
else
    print_info "Skipping Docker build"
    echo "You can build later with: docker compose --profile full build"
fi

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
print_header "Setup Complete!"

echo -e "
${GREEN}Next Steps:${NC}

1. ${YELLOW}Edit your configuration:${NC}
   nano .env                    # Add your API keys
   nano config/config.yml       # Adjust strategy parameters

2. ${YELLOW}Validate your configuration:${NC}
   python3 scripts/validate_secrets.py
   python3 scripts/validate_config.py

3. ${YELLOW}Build Docker images (if not done):${NC}
   docker compose --profile full build

4. ${YELLOW}Start in dry-run mode:${NC}
   docker compose --profile full up -d

5. ${YELLOW}Monitor logs:${NC}
   docker compose logs -f

${RED}IMPORTANT:${NC}
- Always start with DRY_RUN=1 in .env
- Never commit .env to version control
- See docs/security.md for security best practices

${BLUE}Documentation:${NC}
- Installation Guide: docs/installation.md
- API Setup: docs/api-setup.md
- Security: docs/security.md
"

print_success "Setup script completed!"
