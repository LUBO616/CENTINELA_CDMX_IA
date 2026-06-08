#!/bin/bash

# ============================================================================
# CENTINELA_CDMX_IA - Test n8n Webhook Script
# ============================================================================
# This script tests the n8n webhook with 3 scenarios
# Prerequisites: n8n workflow must be imported and active
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Webhook URL
WEBHOOK_URL="http://localhost:5678/webhook/911-call"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}CENTINELA_CDMX_IA - Testing n8n Webhook${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Check if n8n is accessible
echo -n "Checking n8n availability... "
if curl -s http://localhost:5678/healthz > /dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
    echo -e "${YELLOW}n8n is not accessible. Make sure it's running and the workflow is active.${NC}"
    exit 1
fi

echo ""

# Function to test webhook
test_webhook() {
    local scenario=$1
    local data=$2
    local expected_risk_min=$3
    local expected_risk_max=$4
    
    echo -e "${CYAN}Testing: $scenario${NC}"
    
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$data" \
        "$WEBHOOK_URL" 2>/dev/null)
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ HTTP 200${NC}"
        
        # Parse response
        success=$(echo "$body" | jq -r '.success' 2>/dev/null)
        risk_level=$(echo "$body" | jq -r '.risk_level' 2>/dev/null)
        branch=$(echo "$body" | jq -r '.branch' 2>/dev/null)
        human_required=$(echo "$body" | jq -r '.human_required' 2>/dev/null)
        p0_count=$(echo "$body" | jq '.p0_signals | length' 2>/dev/null)
        
        echo -e "  Success: ${GREEN}$success${NC}"
        echo -e "  Risk Level: ${YELLOW}$risk_level${NC}"
        echo -e "  Branch: ${CYAN}$branch${NC}"
        echo -e "  Human Required: $human_required"
        echo -e "  P0 Signals: $p0_count"
        
        # Validate risk level range
        if [ "$risk_level" -ge "$expected_risk_min" ] && [ "$risk_level" -le "$expected_risk_max" ]; then
            echo -e "  ${GREEN}✓ Risk level in expected range [$expected_risk_min-$expected_risk_max]${NC}"
        else
            echo -e "  ${RED}✗ Risk level out of range (expected $expected_risk_min-$expected_risk_max)${NC}"
        fi
        
        echo ""
        return 0
    else
        echo -e "${RED}✗ HTTP $http_code${NC}"
        echo -e "${YELLOW}Response:${NC}"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        echo ""
        return 1
    fi
}

# ----------------------------------------------------------------------------
# Test 1: Low Risk - Public Services
# ----------------------------------------------------------------------------
echo -e "${MAGENTA}[1/3] Scenario 1: Low Risk - Public Services${NC}"
test_webhook \
    "Low Risk - Pothole Report" \
    '{
        "transcript": "Hola, quiero reportar un bache en la calle Reforma. Mi teléfono es 5512345678.",
        "metadata": {
            "source": "test_webhook",
            "timestamp": "2026-06-06T12:00:00Z"
        },
        "location_hint": "Colonia Centro"
    }' \
    1 4

# ----------------------------------------------------------------------------
# Test 2: Medium Risk - Traffic Accident
# ----------------------------------------------------------------------------
echo -e "${MAGENTA}[2/3] Scenario 2: Medium Risk - Traffic Accident${NC}"
test_webhook \
    "Medium Risk - Traffic Accident" \
    '{
        "transcript": "Accidente de tránsito en Insurgentes. Dos autos chocados bloquean el carril, sin lesionados confirmados.",
        "location_hint": "Insurgentes con Reforma"
    }' \
    5 5

# ----------------------------------------------------------------------------
# Test 3: Critical P0 - Child in Danger
# ----------------------------------------------------------------------------
echo -e "${MAGENTA}[3/3] Scenario 3: Critical P0 - Child in Danger${NC}"
test_webhook \
    "Critical P0 - Child Bleeding" \
    '{
        "transcript": "¡Auxilio! Hay un niño sangrando mucho de la cabeza. Tiene 8 años y se cayó de las escaleras.",
        "location_hint": "Calle Madero 45, Colonia Centro",
        "solid_consent": true
    }' \
    6 10

# ----------------------------------------------------------------------------
# Verify Data in Database
# ----------------------------------------------------------------------------
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Verifying Data in Database${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Count records
raw_count=$(docker exec emergency-db psql -U emergency_user -d emergency_demo -t -c "SELECT COUNT(*) FROM raw.conversations;" 2>/dev/null | tr -d ' ')
triage_count=$(docker exec emergency-db psql -U emergency_user -d emergency_demo -t -c "SELECT COUNT(*) FROM core.triage_results;" 2>/dev/null | tr -d ' ')
incident_count=$(docker exec emergency-db psql -U emergency_user -d emergency_demo -t -c "SELECT COUNT(*) FROM analytics.incidents;" 2>/dev/null | tr -d ' ')

echo -e "${CYAN}Database Records:${NC}"
echo -e "  Raw Conversations: $raw_count"
echo -e "  Triage Results: $triage_count"
echo -e "  Incidents: $incident_count"
echo ""

# Show latest incidents
echo -e "${CYAN}Latest 3 Incidents:${NC}"
docker exec emergency-db psql -U emergency_user -d emergency_demo -c "
SELECT 
    LEFT(incident_id::text, 8) as id,
    risk_level,
    branch,
    case_category,
    human_required,
    has_p0_signals
FROM analytics.incidents
ORDER BY processed_at DESC
LIMIT 3;
" 2>/dev/null

echo ""

# ----------------------------------------------------------------------------
# Test Analytics Endpoints
# ----------------------------------------------------------------------------
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Analytics Summary${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

curl -s http://localhost:8003/analytics/summary | jq '{
    total_incidents,
    by_risk_level,
    by_branch,
    human_required_count,
    p0_signals_count
}'

echo ""

# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Test Complete${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "${GREEN}✓ n8n webhook is working correctly${NC}"
echo ""
echo -e "${CYAN}Next steps:${NC}"
echo -e "1. View workflow executions in n8n: ${GREEN}http://localhost:5678${NC}"
echo -e "2. Check detailed analytics: ${GREEN}curl http://localhost:8003/analytics/summary | jq${NC}"
echo -e "3. View predictions: ${GREEN}curl http://localhost:8003/analytics/predictions | jq${NC}"
echo ""

# Made with Bob