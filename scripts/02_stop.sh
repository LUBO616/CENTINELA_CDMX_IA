#!/bin/bash

# ============================================================================
# CENTINELA_CDMX_IA - Stop Script
# ============================================================================
# This script stops all services and optionally removes volumes
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}CENTINELA_CDMX_IA - Stopping System${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Parse arguments
REMOVE_VOLUMES=false
REMOVE_IMAGES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--volumes)
            REMOVE_VOLUMES=true
            shift
            ;;
        -i|--images)
            REMOVE_IMAGES=true
            shift
            ;;
        -a|--all)
            REMOVE_VOLUMES=true
            REMOVE_IMAGES=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --volumes    Remove data volumes (WARNING: deletes all data)"
            echo "  -i, --images     Remove built images"
            echo "  -a, --all        Remove volumes and images"
            echo "  -h, --help       Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# ----------------------------------------------------------------------------
# Stop Services
# ----------------------------------------------------------------------------
echo -e "${CYAN}Stopping services...${NC}"
docker compose down

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Services stopped successfully${NC}"
else
    echo -e "${RED}✗ Error stopping services${NC}"
    exit 1
fi

echo ""

# ----------------------------------------------------------------------------
# Remove Volumes (if requested)
# ----------------------------------------------------------------------------
if [ "$REMOVE_VOLUMES" = true ]; then
    echo -e "${YELLOW}⚠ WARNING: This will delete all data (database, n8n workflows, etc.)${NC}"
    read -p "Are you sure you want to remove volumes? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        echo -e "${CYAN}Removing volumes...${NC}"
        docker compose down -v
        
        # Also remove named volumes explicitly
        docker volume rm emergency_postgres_data 2>/dev/null || true
        docker volume rm emergency_n8n_data 2>/dev/null || true
        
        echo -e "${GREEN}✓ Volumes removed${NC}"
    else
        echo -e "${YELLOW}Skipping volume removal${NC}"
    fi
    echo ""
fi

# ----------------------------------------------------------------------------
# Remove Images (if requested)
# ----------------------------------------------------------------------------
if [ "$REMOVE_IMAGES" = true ]; then
    echo -e "${CYAN}Removing built images...${NC}"
    
    # Remove service images
    docker rmi centinela-cdmx-ia-api-ingest 2>/dev/null || true
    docker rmi centinela-cdmx-ia-api-triage 2>/dev/null || true
    docker rmi centinela-cdmx-ia-api-analytics 2>/dev/null || true
    
    echo -e "${GREEN}✓ Images removed${NC}"
    echo ""
fi

# ----------------------------------------------------------------------------
# Display Status
# ----------------------------------------------------------------------------
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Current Status${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Check if any containers are still running
RUNNING_CONTAINERS=$(docker ps --filter "name=emergency\|api-\|n8n" --format "{{.Names}}" 2>/dev/null)

if [ -z "$RUNNING_CONTAINERS" ]; then
    echo -e "${GREEN}✓ No emergency demo containers are running${NC}"
else
    echo -e "${YELLOW}⚠ Some containers are still running:${NC}"
    echo "$RUNNING_CONTAINERS"
fi

echo ""

# Check volumes
VOLUMES=$(docker volume ls --filter "name=emergency" --format "{{.Name}}" 2>/dev/null)

if [ -z "$VOLUMES" ]; then
    echo -e "${GREEN}✓ No emergency demo volumes exist${NC}"
else
    echo -e "${CYAN}Existing volumes:${NC}"
    echo "$VOLUMES"
fi

echo ""

# ----------------------------------------------------------------------------
# Next Steps
# ----------------------------------------------------------------------------
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Next Steps${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "To start the system again:"
echo -e "  ${GREEN}./scripts/01_start.sh${NC}"
echo ""
echo -e "To remove all data (volumes):"
echo -e "  ${GREEN}./scripts/02_stop.sh --volumes${NC}"
echo ""
echo -e "To remove everything (volumes + images):"
echo -e "  ${GREEN}./scripts/02_stop.sh --all${NC}"
echo ""

