#!/bin/bash
# =============================================================================
# PredictBot Stack - Ollama Setup Script
# =============================================================================
# This script sets up Ollama with the required models for the AI orchestrator.
#
# Usage:
#   ./scripts/setup_ollama.sh
#
# Prerequisites:
#   - Docker must be running
#   - Ollama container must be started (docker-compose --profile ai up -d ollama)
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OLLAMA_HOST="${OLLAMA_HOST:-localhost}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"
OLLAMA_URL="http://${OLLAMA_HOST}:${OLLAMA_PORT}"

# Models to pull
MODELS=(
    "llama3.2:3b"      # Fast, lightweight model for routine tasks
    "llama3.1:8b"      # Medium model for balanced performance
    "qwen2.5:32b"      # Large model for complex reasoning (optional, requires significant VRAM)
)

# Optional models (uncomment to include)
# MODELS+=(
#     "mistral:7b"       # Alternative medium model
#     "codellama:13b"    # Code-focused model
# )

echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}  PredictBot - Ollama Setup${NC}"
echo -e "${BLUE}=============================================${NC}"
echo ""

# Function to check if Ollama is running
check_ollama() {
    echo -e "${YELLOW}Checking Ollama availability at ${OLLAMA_URL}...${NC}"
    
    for i in {1..30}; do
        if curl -s "${OLLAMA_URL}/api/tags" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Ollama is running${NC}"
            return 0
        fi
        echo -e "  Waiting for Ollama to start... (attempt $i/30)"
        sleep 2
    done
    
    echo -e "${RED}✗ Ollama is not responding at ${OLLAMA_URL}${NC}"
    echo -e "${YELLOW}Please ensure Ollama is running:${NC}"
    echo -e "  docker-compose --profile ai up -d ollama"
    exit 1
}

# Function to pull a model
pull_model() {
    local model=$1
    echo ""
    echo -e "${BLUE}Pulling model: ${model}${NC}"
    
    # Check if model already exists
    if curl -s "${OLLAMA_URL}/api/tags" | grep -q "\"name\":\"${model}\""; then
        echo -e "${GREEN}✓ Model ${model} already exists${NC}"
        return 0
    fi
    
    # Pull the model
    echo -e "${YELLOW}Downloading ${model}... (this may take a while)${NC}"
    
    response=$(curl -s -X POST "${OLLAMA_URL}/api/pull" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"${model}\", \"stream\": false}" \
        --max-time 3600)
    
    if echo "$response" | grep -q "error"; then
        echo -e "${RED}✗ Failed to pull ${model}${NC}"
        echo -e "  Error: $(echo "$response" | grep -o '"error":"[^"]*"')"
        return 1
    fi
    
    echo -e "${GREEN}✓ Successfully pulled ${model}${NC}"
    return 0
}

# Function to verify models
verify_models() {
    echo ""
    echo -e "${BLUE}Verifying installed models...${NC}"
    
    local installed_models=$(curl -s "${OLLAMA_URL}/api/tags" | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
    
    echo ""
    echo -e "${GREEN}Installed models:${NC}"
    for model in $installed_models; do
        echo -e "  • ${model}"
    done
    
    echo ""
    echo -e "${YELLOW}Checking required models:${NC}"
    local all_present=true
    for model in "${MODELS[@]}"; do
        if echo "$installed_models" | grep -q "^${model}$"; then
            echo -e "  ${GREEN}✓${NC} ${model}"
        else
            echo -e "  ${RED}✗${NC} ${model} (missing)"
            all_present=false
        fi
    done
    
    if [ "$all_present" = true ]; then
        echo ""
        echo -e "${GREEN}All required models are installed!${NC}"
        return 0
    else
        echo ""
        echo -e "${YELLOW}Some models are missing. They will be pulled on first use.${NC}"
        return 1
    fi
}

# Function to test a model
test_model() {
    local model=$1
    echo ""
    echo -e "${BLUE}Testing model: ${model}${NC}"
    
    response=$(curl -s -X POST "${OLLAMA_URL}/api/generate" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"${model}\",
            \"prompt\": \"Say 'Hello from PredictBot!' in exactly those words.\",
            \"stream\": false,
            \"options\": {
                \"num_predict\": 20
            }
        }" \
        --max-time 60)
    
    if echo "$response" | grep -q "Hello"; then
        echo -e "${GREEN}✓ Model ${model} is working correctly${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Model ${model} response may need verification${NC}"
        echo -e "  Response: $(echo "$response" | head -c 100)..."
        return 1
    fi
}

# Main execution
main() {
    # Check if running in Docker context
    if [ -n "$DOCKER_CONTEXT" ]; then
        OLLAMA_HOST="ollama"
    fi
    
    # Check Ollama availability
    check_ollama
    
    # Pull each model
    echo ""
    echo -e "${BLUE}Pulling required models...${NC}"
    
    failed_models=()
    for model in "${MODELS[@]}"; do
        if ! pull_model "$model"; then
            failed_models+=("$model")
        fi
    done
    
    # Verify installation
    verify_models
    
    # Test the primary model
    if curl -s "${OLLAMA_URL}/api/tags" | grep -q '"name":"llama3.2:3b"'; then
        test_model "llama3.2:3b"
    fi
    
    # Summary
    echo ""
    echo -e "${BLUE}=============================================${NC}"
    echo -e "${BLUE}  Setup Complete${NC}"
    echo -e "${BLUE}=============================================${NC}"
    
    if [ ${#failed_models[@]} -eq 0 ]; then
        echo -e "${GREEN}All models installed successfully!${NC}"
    else
        echo -e "${YELLOW}Some models failed to install:${NC}"
        for model in "${failed_models[@]}"; do
            echo -e "  • ${model}"
        done
        echo -e "${YELLOW}You can retry pulling them manually:${NC}"
        echo -e "  curl -X POST ${OLLAMA_URL}/api/pull -d '{\"name\": \"MODEL_NAME\"}'"
    fi
    
    echo ""
    echo -e "${GREEN}Ollama is ready for use with PredictBot AI Orchestrator${NC}"
    echo -e "  API URL: ${OLLAMA_URL}"
    echo ""
}

# Run main function
main "$@"
