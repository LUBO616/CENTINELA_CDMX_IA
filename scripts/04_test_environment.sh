#!/bin/bash

# ============================================================================
# CENTINELA_CDMX_IA - Test Environment Script
# ============================================================================
# This script tests services and endpoints
# Usage:
#   ./scripts/04_test_environment.sh infra  # Test only infra (DB, n8n, schemas)
#   ./scripts/04_test_environment.sh all    # Test all including API endpoints
#   ./scripts/04_test_environment.sh        # Default: infra mode
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
    echo "  infra - Test only infrastructure (default)"
    echo "  all   - Test all services including APIs"
    exit 1
fi

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}CENTINELA_CDMX_IA - Environment Test (Mode: $MODE)${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test JSON endpoint
test_json_endpoint() {
    local name=$1
    local url=$2
    local expected_field=$3
    
    echo -n "Testing $name... "
    
    response=$(curl -s "$url" 2>/dev/null)
    
    if echo "$response" | jq -e ".$expected_field" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC} (JSON valid, field '$expected_field' exists)"
        ((++TESTS_PASSED))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (JSON invalid or field missing)"
        echo -e "${YELLOW}Response: $response${NC}"
        ((++TESTS_FAILED))
        return 1
    fi
}

# ----------------------------------------------------------------------------
# Test 1: Docker and Services Running
# ----------------------------------------------------------------------------
echo -e "${CYAN}[1/6] Testing Docker and Services${NC}"
echo ""

# Check Docker is running
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC} Docker is running"
    ((++TESTS_PASSED))
else
    echo -e "${RED}✗ FAIL${NC} Docker is not running"
    ((++TESTS_FAILED))
fi

# Check PostgreSQL container
if docker ps | grep -q centinela-db; then
    echo -e "${GREEN}✓ PASS${NC} PostgreSQL container is running"
    ((++TESTS_PASSED))
else
    echo -e "${RED}✗ FAIL${NC} PostgreSQL container is not running"
    ((++TESTS_FAILED))
fi

# Check n8n container
if docker ps | grep -q n8n-orchestrator; then
    echo -e "${GREEN}✓ PASS${NC} n8n container is running"
    ((++TESTS_PASSED))
else
    echo -e "${RED}✗ FAIL${NC} n8n container is not running"
    ((++TESTS_FAILED))
fi

echo ""

# ----------------------------------------------------------------------------
# Test 2: Database Connectivity and Schema
# ----------------------------------------------------------------------------
echo -e "${CYAN}[2/6] Testing Database Connectivity and Schema${NC}"
echo ""

# Test if we can connect to PostgreSQL
if docker exec centinela-db psql -U emergency_user -d centinela_demo -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC} PostgreSQL connection"
    ((++TESTS_PASSED))
else
    echo -e "${RED}✗ FAIL${NC} PostgreSQL connection"
    ((++TESTS_FAILED))
fi

# Test if schemas exist
schemas_result=$(docker exec centinela-db psql -U emergency_user -d centinela_demo -t -c "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name IN ('raw', 'core', 'analytics');" 2>/dev/null | tr -d ' ')
if [ "$schemas_result" = "3" ]; then
    echo -e "${GREEN}✓ PASS${NC} All 3 schemas exist (raw, core, analytics)"
    ((++TESTS_PASSED))
else
    echo -e "${RED}✗ FAIL${NC} Schemas missing (found: $schemas_result, expected: 3)"
    ((++TESTS_FAILED))
fi

# Test if tables exist
tables_result=$(docker exec centinela-db psql -U emergency_user -d centinela_demo -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema IN ('raw', 'core', 'analytics') AND table_type = 'BASE TABLE';" 2>/dev/null | tr -d ' ')
if [ "$tables_result" = "4" ]; then
    echo -e "${GREEN}✓ PASS${NC} All 4 tables exist"
    ((++TESTS_PASSED))
else
    echo -e "${RED}✗ FAIL${NC} Tables missing (found: $tables_result, expected: 4)"
    ((++TESTS_FAILED))
fi

# Test if views exist
views_result=$(docker exec centinela-db psql -U emergency_user -d centinela_demo -t -c "SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'analytics';" 2>/dev/null | tr -d ' ')
if [ "$views_result" = "3" ]; then
    echo -e "${GREEN}✓ PASS${NC} All 3 analytics views exist"
    ((++TESTS_PASSED))
else
    echo -e "${RED}✗ FAIL${NC} Views missing (found: $views_result, expected: 3)"
    ((++TESTS_FAILED))
fi

echo ""

# ----------------------------------------------------------------------------
# Test 3: n8n Accessibility
# ----------------------------------------------------------------------------
echo -e "${CYAN}[3/6] Testing n8n Accessibility${NC}"
echo ""

# Test n8n health endpoint
if curl -s http://localhost:5678/healthz > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC} n8n is accessible"
    ((++TESTS_PASSED))
else
    echo -e "${RED}✗ FAIL${NC} n8n is not accessible"
    ((++TESTS_FAILED))
fi

echo ""

# ----------------------------------------------------------------------------
# API Tests (only in 'all' mode)
# ----------------------------------------------------------------------------
if [ "$MODE" = "all" ]; then
    # ------------------------------------------------------------------------
    # Test 4: API Health Endpoints
    # ------------------------------------------------------------------------
    echo -e "${CYAN}[4/6] Testing API Health Endpoints${NC}"
    echo ""

    test_json_endpoint "api-ingest health" "http://localhost:8001/health" "status"
    test_json_endpoint "api-triage health" "http://localhost:8002/health" "status"
    test_json_endpoint "api-analytics health" "http://localhost:8003/health" "status"

    echo ""

    # ------------------------------------------------------------------------
    # Test 5: Complete Flow (Ingest → Triage → Analytics)
    # ------------------------------------------------------------------------
    echo -e "${CYAN}[5/6] Testing Complete Flow (Ingest → Triage → Analytics)${NC}"
    echo ""

    # Step 1: Create conversation with api-ingest
    echo -n "Testing POST /raw-conversations... "
    ingest_response=$(curl -s -X POST http://localhost:8001/raw-conversations \
        -H "Content-Type: application/json" \
        -d '{
            "transcript": "Hay un incendio en mi edificio, necesito ayuda urgente. Mi teléfono es 5512345678.",
            "metadata": {"source": "test_environment"}
        }' 2>/dev/null)
    
    if echo "$ingest_response" | jq -e '.call_id' > /dev/null 2>&1; then
        CALL_ID=$(echo "$ingest_response" | jq -r '.call_id')
        TRACE_ID=$(echo "$ingest_response" | jq -r '.trace_id')
        echo -e "${GREEN}✓ PASS${NC} (call_id: ${CALL_ID:0:8}...)"
        ((++TESTS_PASSED))
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo -e "${YELLOW}Response: $ingest_response${NC}"
        ((++TESTS_FAILED))
        CALL_ID=""
    fi

    # Step 2: Classify with api-triage (only if ingest succeeded)
    if [ -n "$CALL_ID" ]; then
        echo -n "Testing POST /triage... "
        triage_response=$(curl -s -X POST http://localhost:8002/triage \
            -H "Content-Type: application/json" \
            -d "{
                \"transcript\": \"Hay un incendio en mi edificio, necesito ayuda urgente\",
                \"call_id\": \"$CALL_ID\",
                \"trace_id\": \"$TRACE_ID\",
                \"consent\": true,
                \"location_hint\": \"Colonia Centro\"
            }" 2>/dev/null)
        
        if echo "$triage_response" | jq -e '.risk_level' > /dev/null 2>&1; then
            RISK_LEVEL=$(echo "$triage_response" | jq -r '.risk_level')
            BRANCH=$(echo "$triage_response" | jq -r '.branch')
            CATEGORY=$(echo "$triage_response" | jq -r '.case_category')
            HUMAN_REQ=$(echo "$triage_response" | jq -r '.human_required')
            P0_SIGNALS=$(echo "$triage_response" | jq -c '.p0_signals')
            TRIAGE_TRACE_ID=$(echo "$triage_response" | jq -r '.trace_id')
            echo -e "${GREEN}✓ PASS${NC} (risk: $RISK_LEVEL, branch: $BRANCH)"
            ((++TESTS_PASSED))
        else
            echo -e "${RED}✗ FAIL${NC}"
            echo -e "${YELLOW}Response: $triage_response${NC}"
            ((++TESTS_FAILED))
            RISK_LEVEL=""
        fi
    else
        echo -e "${YELLOW}⊘ SKIP${NC} POST /triage (ingest failed)"
        ((++TESTS_FAILED))
    fi

    # Step 3: Store in analytics (only if triage succeeded)
    if [ -n "$RISK_LEVEL" ]; then
        echo -n "Testing POST /incidents... "
        analytics_response=$(curl -s -X POST http://localhost:8003/incidents \
            -H "Content-Type: application/json" \
            -d "{
                \"call_id\": \"$CALL_ID\",
                \"trace_id\": \"$TRIAGE_TRACE_ID\",
                \"risk_level\": $RISK_LEVEL,
                \"branch\": \"$BRANCH\",
                \"case_category\": \"$CATEGORY\",
                \"human_required\": $HUMAN_REQ,
                \"p0_signals\": $P0_SIGNALS,
                \"location_hint\": \"Colonia Centro\"
            }" 2>/dev/null)
        
        if echo "$analytics_response" | jq -e '.incident_id' > /dev/null 2>&1; then
            INCIDENT_ID=$(echo "$analytics_response" | jq -r '.incident_id')
            echo -e "${GREEN}✓ PASS${NC} (incident_id: ${INCIDENT_ID:0:8}...)"
            ((++TESTS_PASSED))
        else
            echo -e "${RED}✗ FAIL${NC}"
            echo -e "${YELLOW}Response: $analytics_response${NC}"
            ((++TESTS_FAILED))
        fi
    else
        echo -e "${YELLOW}⊘ SKIP${NC} POST /incidents (triage failed)"
        ((++TESTS_FAILED))
    fi

    # Step 4: Verify GET endpoints
    echo -n "Testing GET /raw-conversations... "
    if curl -s "http://localhost:8001/raw-conversations?limit=10" | jq -e '.total' > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((++TESTS_PASSED))
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((++TESTS_FAILED))
    fi

    echo -n "Testing GET /incidents... "
    if curl -s "http://localhost:8003/incidents?limit=10" | jq -e '.total' > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((++TESTS_PASSED))
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((++TESTS_FAILED))
    fi

    echo ""

    # ------------------------------------------------------------------------
    # Test 6: Analytics Endpoints
    # ------------------------------------------------------------------------
    echo -e "${CYAN}[6/6] Testing Analytics Endpoints${NC}"
    echo ""

    test_json_endpoint "GET /analytics/summary" "http://localhost:8003/analytics/summary" "total_incidents"
    test_json_endpoint "GET /analytics/predictions" "http://localhost:8003/analytics/predictions" "volume_forecast"

    echo ""
else
    echo -e "${YELLOW}Skipping API tests (use './scripts/04_test_environment.sh all' to test APIs)${NC}"
    echo ""
fi

# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! Environment is working correctly.${NC}"
    echo ""
    if [ "$MODE" = "infra" ]; then
        echo -e "${CYAN}Next steps:${NC}"
        echo -e "1. Start all services: ${GREEN}./scripts/01_start.sh all${NC}"
        echo -e "2. Test all services: ${GREEN}./scripts/04_test_environment.sh all${NC}"
        echo -e "3. Access n8n at ${GREEN}http://localhost:5678${NC}"
    else
        echo -e "${CYAN}Next steps:${NC}"
        echo -e "1. Seed demo data: ${GREEN}./scripts/05_seed_demo_data.sh direct${NC}"
        echo -e "2. Access n8n at ${GREEN}http://localhost:5678${NC}"
        echo -e "3. View analytics: ${GREEN}curl http://localhost:8003/analytics/summary | jq${NC}"
    fi
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please check the errors above.${NC}"
    echo -e "${YELLOW}Tip: Check service logs with ./scripts/03_logs.sh${NC}"
    echo ""
    exit 1
fi

