#!/bin/bash

# ============================================================================
# 911 AI Flow Demo - Pre-flight Check Script
# ============================================================================
# This script verifies that all prerequisites are met before starting the system
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}911 AI Flow Demo - Pre-flight Check${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Track overall status
CHECKS_PASSED=0
CHECKS_FAILED=0

# Function to print check result
check_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        ((++CHECKS_PASSED))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        echo -e "${YELLOW}  → $3${NC}"
        ((++CHECKS_FAILED))
    fi
}

# ----------------------------------------------------------------------------
# Check 1: Docker Installation
# ----------------------------------------------------------------------------
echo -e "${BLUE}[1/10]${NC} Checking Docker installation..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d ' ' -f3 | cut -d ',' -f1)
    check_result 0 "Docker is installed (version $DOCKER_VERSION)"
else
    check_result 1 "Docker is not installed" "Install Docker: https://docs.docker.com/engine/install/"
fi

# ----------------------------------------------------------------------------
# Check 2: Docker Compose Installation
# ----------------------------------------------------------------------------
echo -e "${BLUE}[2/10]${NC} Checking Docker Compose installation..."
if docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version --short)
    check_result 0 "Docker Compose is installed (version $COMPOSE_VERSION)"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | cut -d ' ' -f3 | cut -d ',' -f1)
    check_result 0 "Docker Compose is installed (version $COMPOSE_VERSION)"
else
    check_result 1 "Docker Compose is not installed" "Install Docker Compose: https://docs.docker.com/compose/install/"
fi

# ----------------------------------------------------------------------------
# Check 3: Docker Service Running
# ----------------------------------------------------------------------------
echo -e "${BLUE}[3/10]${NC} Checking Docker service status..."
if docker info &> /dev/null; then
    check_result 0 "Docker service is running"
else
    check_result 1 "Docker service is not running" "Start Docker service: sudo systemctl start docker"
fi

# ----------------------------------------------------------------------------
# Check 4: Port Availability
# ----------------------------------------------------------------------------
echo -e "${BLUE}[4/10]${NC} Checking port availability..."
REQUIRED_PORTS=(5432 5678 8001 8002 8003)
PORTS_AVAILABLE=true

for port in "${REQUIRED_PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":$port "; then
        echo -e "${YELLOW}  ⚠ Port $port is already in use${NC}"
        PORTS_AVAILABLE=false
    fi
done

if [ "$PORTS_AVAILABLE" = true ]; then
    check_result 0 "All required ports are available (5432, 5678, 8001-8003)"
else
    check_result 1 "Some required ports are in use" "Stop services using these ports or change port configuration in .env"
fi

# ----------------------------------------------------------------------------
# Check 5: Environment File
# ----------------------------------------------------------------------------
echo -e "${BLUE}[5/10]${NC} Checking environment configuration..."
if [ -f "$PROJECT_ROOT/.env" ]; then
    check_result 0 ".env file exists"
    
    # Check for default passwords
    if grep -q "changeme\|CHANGE_THIS" "$PROJECT_ROOT/.env"; then
        echo -e "${YELLOW}  ⚠ Warning: Default passwords detected in .env file${NC}"
        echo -e "${YELLOW}  → Update passwords before production deployment${NC}"
    fi
else
    check_result 1 ".env file not found" "Copy .env.example to .env: cp .env.example .env"
fi

# ----------------------------------------------------------------------------
# Check 6: Project Structure
# ----------------------------------------------------------------------------
echo -e "${BLUE}[6/10]${NC} Checking project structure..."
REQUIRED_DIRS=(
    "services/api-ingest"
    "services/api-triage"
    "services/api-analytics"
    "database"
    "n8n/workflows"
    "scripts"
    "docs"
)

STRUCTURE_OK=true
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$PROJECT_ROOT/$dir" ]; then
        echo -e "${YELLOW}  ⚠ Missing directory: $dir${NC}"
        STRUCTURE_OK=false
    fi
done

if [ "$STRUCTURE_OK" = true ]; then
    check_result 0 "Project structure is complete"
else
    check_result 1 "Project structure is incomplete" "Ensure all required directories exist"
fi

# ----------------------------------------------------------------------------
# Check 7: Database Initialization Script
# ----------------------------------------------------------------------------
echo -e "${BLUE}[7/10]${NC} Checking database initialization..."
if [ -f "$PROJECT_ROOT/database/init.sql" ]; then
    check_result 0 "Database initialization script exists"
else
    check_result 1 "Database initialization script not found" "Ensure database/init.sql exists"
fi

# ----------------------------------------------------------------------------
# Check 8: Docker Compose File
# ----------------------------------------------------------------------------
echo -e "${BLUE}[8/10]${NC} Checking Docker Compose configuration..."
if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    check_result 0 "docker-compose.yml exists"
    
    # Validate Docker Compose file
    if docker compose -f "$PROJECT_ROOT/docker-compose.yml" config &> /dev/null; then
        check_result 0 "docker-compose.yml is valid"
    else
        check_result 1 "docker-compose.yml has syntax errors" "Run: docker compose config"
    fi
else
    check_result 1 "docker-compose.yml not found" "Ensure docker-compose.yml exists in project root"
fi

# ----------------------------------------------------------------------------
# Check 9: Disk Space
# ----------------------------------------------------------------------------
echo -e "${BLUE}[9/10]${NC} Checking available disk space..."
AVAILABLE_SPACE=$(df -BG "$PROJECT_ROOT" | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -gt 5 ]; then
    check_result 0 "Sufficient disk space available (${AVAILABLE_SPACE}GB free)"
else
    check_result 1 "Low disk space (${AVAILABLE_SPACE}GB free)" "At least 5GB recommended for Docker images and data"
fi

# ----------------------------------------------------------------------------
# Check 10: Network Connectivity
# ----------------------------------------------------------------------------
echo -e "${BLUE}[10/10]${NC} Checking network connectivity..."
if ping -c 1 8.8.8.8 &> /dev/null; then
    check_result 0 "Network connectivity is available"
else
    check_result 1 "No network connectivity" "Check internet connection (required for pulling Docker images)"
fi

# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Pre-flight Check Summary${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo -e "${GREEN}Checks Passed: $CHECKS_PASSED${NC}"
echo -e "${RED}Checks Failed: $CHECKS_FAILED${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! System is ready to start.${NC}"
    echo -e "${BLUE}Next step: Run ./scripts/01_start.sh to start the system${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please resolve the issues above before starting.${NC}"
    echo -e "${YELLOW}Tip: Review the error messages and follow the suggested actions.${NC}"
    exit 1
fi

# Made with Bob
