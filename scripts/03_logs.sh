#!/bin/bash

# ============================================================================
# 911 AI Flow Demo - Logs Script
# ============================================================================
# This script displays logs from services
# ============================================================================

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

# Change to project root
cd "$PROJECT_ROOT"

# Parse arguments
SERVICE=""
FOLLOW=false
TAIL_LINES=100

show_help() {
    echo "Usage: $0 [OPTIONS] [SERVICE]"
    echo ""
    echo "Display logs from Docker services"
    echo ""
    echo "Services:"
    echo "  postgres      PostgreSQL database"
    echo "  api-ingest    API Ingest service"
    echo "  api-triage    API Triage service"
    echo "  api-analytics API Analytics service"
    echo "  n8n           n8n orchestrator"
    echo "  all           All services (default)"
    echo ""
    echo "Options:"
    echo "  -f, --follow       Follow log output (like tail -f)"
    echo "  -n, --lines NUM    Number of lines to show (default: 100)"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Show last 100 lines from all services"
    echo "  $0 -f                 # Follow all services"
    echo "  $0 api-ingest         # Show logs from api-ingest"
    echo "  $0 -f api-triage      # Follow api-triage logs"
    echo "  $0 -n 500 postgres    # Show last 500 lines from postgres"
    echo ""
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -n|--lines)
            TAIL_LINES="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        postgres|api-ingest|api-triage|api-analytics|n8n|all)
            SERVICE="$1"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option or service: $1${NC}"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Default to all services if none specified
if [ -z "$SERVICE" ]; then
    SERVICE="all"
fi

# Map service names to container names
case $SERVICE in
    postgres)
        CONTAINER="emergency-db"
        ;;
    api-ingest)
        CONTAINER="api-ingest"
        ;;
    api-triage)
        CONTAINER="api-triage"
        ;;
    api-analytics)
        CONTAINER="api-analytics"
        ;;
    n8n)
        CONTAINER="n8n-orchestrator"
        ;;
    all)
        CONTAINER=""
        ;;
esac

# Display header
echo -e "${BLUE}============================================================================${NC}"
if [ "$SERVICE" = "all" ]; then
    echo -e "${BLUE}Logs from All Services${NC}"
else
    echo -e "${BLUE}Logs from: $SERVICE${NC}"
fi
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Build docker compose logs command
CMD="docker compose logs --tail=$TAIL_LINES"

if [ "$FOLLOW" = true ]; then
    CMD="$CMD -f"
fi

if [ -n "$CONTAINER" ]; then
    CMD="$CMD $CONTAINER"
fi

# Execute command
eval $CMD

# Made with Bob
