#!/bin/bash

# ============================================================================
# 911 AI Flow Demo - Start Script
# ============================================================================
# This script starts services using Docker Compose
# Usage:
#   ./scripts/01_start.sh infra  # Start only postgres + n8n
#   ./scripts/01_start.sh all    # Start all services including APIs
#   ./scripts/01_start.sh        # Default: infra mode
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

# Parse mode argument
MODE="${1:-infra}"

if [ "$MODE" != "infra" ] && [ "$MODE" != "all" ]; then
    echo -e "${RED}Error: Invalid mode '$MODE'${NC}"
    echo "Usage: $0 [infra|all]"
    echo "  infra - Start only PostgreSQL and n8n (default)"
    echo "  all   - Start all services including APIs"
    exit 1
fi

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}911 AI Flow Demo - Starting System (Mode: $MODE)${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# ----------------------------------------------------------------------------
# Run Pre-flight Checks
# ----------------------------------------------------------------------------
echo -e "${CYAN}Running pre-flight checks...${NC}"
if [ -f "$SCRIPT_DIR/00_precheck.sh" ]; then
    bash "$SCRIPT_DIR/00_precheck.sh"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Pre-flight checks failed. Aborting startup.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Warning: Pre-flight check script not found. Proceeding anyway...${NC}"
fi

echo ""

# ----------------------------------------------------------------------------
# Change to Project Root
# ----------------------------------------------------------------------------
cd "$PROJECT_ROOT"

# ----------------------------------------------------------------------------
# Check for .env File
# ----------------------------------------------------------------------------
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}No .env file found. Creating from .env.example...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env file${NC}"
        echo -e "${YELLOW}⚠ Please review and update .env with your configuration${NC}"
        echo -e "${YELLOW}⚠ Especially change default passwords!${NC}"
        echo ""
        read -p "Press Enter to continue or Ctrl+C to abort..."
    else
        echo -e "${RED}Error: .env.example not found${NC}"
        exit 1
    fi
fi

# ----------------------------------------------------------------------------
# Pull Docker Images
# ----------------------------------------------------------------------------
echo -e "${CYAN}Pulling Docker images...${NC}"
if [ "$MODE" = "all" ]; then
    docker compose --profile services pull
else
    docker compose pull
fi

echo ""

# ----------------------------------------------------------------------------
# Build Custom Images (only in 'all' mode)
# ----------------------------------------------------------------------------
if [ "$MODE" = "all" ]; then
    echo -e "${CYAN}Building custom service images...${NC}"
    docker compose --profile services build
    echo ""
fi

# ----------------------------------------------------------------------------
# Start Services
# ----------------------------------------------------------------------------
echo -e "${CYAN}Starting services...${NC}"
if [ "$MODE" = "all" ]; then
    docker compose --profile services up -d
else
    docker compose up -d
fi

echo ""

# ----------------------------------------------------------------------------
# Wait for Services to be Healthy
# ----------------------------------------------------------------------------
echo -e "${CYAN}Waiting for services to be healthy...${NC}"
echo -e "${YELLOW}This may take 1-2 minutes...${NC}"
echo ""

MAX_WAIT=120
WAIT_INTERVAL=5
ELAPSED=0

# Function to check service health
check_service_health() {
    local service=$1
    local status=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "unknown")
    echo "$status"
}

# Services to check based on mode
if [ "$MODE" = "all" ]; then
    SERVICES=("emergency-db" "n8n-orchestrator" "api-ingest" "api-triage" "api-analytics")
else
    SERVICES=("emergency-db" "n8n-orchestrator")
fi

while [ $ELAPSED -lt $MAX_WAIT ]; do
    ALL_HEALTHY=true
    
    for service in "${SERVICES[@]}"; do
        health=$(check_service_health "$service")
        
        if [ "$health" = "healthy" ]; then
            echo -e "${GREEN}✓${NC} $service: healthy"
        elif [ "$health" = "starting" ]; then
            echo -e "${YELLOW}⏳${NC} $service: starting..."
            ALL_HEALTHY=false
        elif [ "$health" = "unhealthy" ]; then
            echo -e "${RED}✗${NC} $service: unhealthy"
            ALL_HEALTHY=false
        else
            echo -e "${YELLOW}?${NC} $service: $health"
            ALL_HEALTHY=false
        fi
    done
    
    if [ "$ALL_HEALTHY" = true ]; then
        break
    fi
    
    sleep $WAIT_INTERVAL
    ELAPSED=$((ELAPSED + WAIT_INTERVAL))
    echo ""
done

echo ""

# ----------------------------------------------------------------------------
# Check Final Status
# ----------------------------------------------------------------------------
if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo -e "${RED}⚠ Timeout waiting for services to be healthy${NC}"
    echo -e "${YELLOW}Some services may still be starting. Check logs with: ./scripts/03_logs.sh${NC}"
else
    echo -e "${GREEN}✓ All services are healthy!${NC}"
fi

echo ""

# ----------------------------------------------------------------------------
# Display Service URLs
# ----------------------------------------------------------------------------
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Service URLs${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "${CYAN}PostgreSQL Database:${NC}"
echo -e "  Host: localhost:5432"
echo -e "  Database: emergency_demo"
echo -e "  User: emergency_user"
echo ""
echo -e "${CYAN}API Services:${NC}"
echo -e "  api-ingest:    ${GREEN}http://localhost:8001${NC}"
echo -e "  api-triage:    ${GREEN}http://localhost:8002${NC}"
echo -e "  api-analytics: ${GREEN}http://localhost:8003${NC}"
echo ""
echo -e "${CYAN}n8n Orchestrator:${NC}"
echo -e "  Dashboard: ${GREEN}http://localhost:5678${NC}"
echo -e "  Username: admin (from .env)"
echo -e "  Password: (check .env file)"
echo ""
echo -e "${CYAN}Health Endpoints:${NC}"
echo -e "  ${GREEN}http://localhost:8001/health${NC}"
echo -e "  ${GREEN}http://localhost:8002/health${NC}"
echo -e "  ${GREEN}http://localhost:8003/health${NC}"
echo ""

# ----------------------------------------------------------------------------
# Quick Health Check
# ----------------------------------------------------------------------------
if [ "$MODE" = "all" ]; then
    echo -e "${CYAN}Running quick health checks...${NC}"
    echo ""

    check_endpoint() {
        local url=$1
        local name=$2
        
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} $name is responding"
        else
            echo -e "${RED}✗${NC} $name is not responding yet"
        fi
    }

    check_endpoint "http://localhost:8001/health" "api-ingest"
    check_endpoint "http://localhost:8002/health" "api-triage"
    check_endpoint "http://localhost:8003/health" "api-analytics"

    echo ""
fi

# ----------------------------------------------------------------------------
# Next Steps
# ----------------------------------------------------------------------------
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Next Steps${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

if [ "$MODE" = "infra" ]; then
    echo -e "1. ${CYAN}Access n8n Dashboard:${NC}"
    echo -e "   Open ${GREEN}http://localhost:5678${NC} in your browser"
    echo ""
    echo -e "2. ${CYAN}Test Infrastructure:${NC}"
    echo -e "   Run: ${GREEN}./scripts/04_test_environment.sh infra${NC}"
    echo ""
    echo -e "3. ${CYAN}Start All Services:${NC}"
    echo -e "   Run: ${GREEN}./scripts/01_start.sh all${NC}"
    echo ""
else
    echo -e "1. ${CYAN}Access n8n Dashboard:${NC}"
    echo -e "   Open ${GREEN}http://localhost:5678${NC} in your browser"
    echo -e "   Import workflow from: n8n/workflows/911-ai-flow-demo-main.json"
    echo ""
    echo -e "2. ${CYAN}Test the System:${NC}"
    echo -e "   Run: ${GREEN}./scripts/04_test_environment.sh all${NC}"
    echo ""
    echo -e "3. ${CYAN}Seed Demo Data:${NC}"
    echo -e "   Run: ${GREEN}./scripts/05_seed_demo_data.sh${NC}"
    echo ""
fi

echo -e "4. ${CYAN}View Logs:${NC}"
echo -e "   Run: ${GREEN}./scripts/03_logs.sh${NC}"
echo ""
echo -e "5. ${CYAN}Stop the System:${NC}"
echo -e "   Run: ${GREEN}./scripts/02_stop.sh${NC}"
echo ""
echo -e "${GREEN}System is ready!${NC}"
echo ""

# Made with Bob
