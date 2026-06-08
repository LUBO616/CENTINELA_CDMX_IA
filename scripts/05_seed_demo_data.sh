#!/bin/bash

# ============================================================================
# CENTINELA_CDMX_IA - Seed Demo Data Script
# ============================================================================
# This script seeds the system with demo data for the 3 test scenarios
# Usage:
#   ./scripts/05_seed_demo_data.sh direct  # Use APIs directly (default)
#   ./scripts/05_seed_demo_data.sh n8n     # Use n8n webhook
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

# Parse mode argument
MODE="${1:-direct}"

if [ "$MODE" != "direct" ] && [ "$MODE" != "n8n" ]; then
    echo -e "${RED}Error: Invalid mode '$MODE'${NC}"
    echo "Usage: $0 [direct|n8n]"
    echo "  direct - Use APIs directly (default)"
    echo "  n8n    - Use n8n webhook"
    exit 1
fi

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}CENTINELA_CDMX_IA - Seeding Demo Data (Mode: $MODE)${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# ----------------------------------------------------------------------------
# Mode: Direct API Calls
# ----------------------------------------------------------------------------
if [ "$MODE" = "direct" ]; then
    # Function to send test call via direct API
    send_direct_call() {
        local scenario=$1
        local transcript=$2
        local metadata=$3
        
        echo -e "${CYAN}Processing: $scenario${NC}"
        
        # Step 1: Ingest
        echo -n "  [1/3] Ingesting... "
        ingest_response=$(curl -s -X POST http://localhost:8001/raw-conversations \
            -H "Content-Type: application/json" \
            -d "{
                \"transcript\": \"$transcript\",
                \"metadata\": $metadata
            }" 2>/dev/null)
        
        if echo "$ingest_response" | jq -e '.call_id' > /dev/null 2>&1; then
            CALL_ID=$(echo "$ingest_response" | jq -r '.call_id')
            TRACE_ID=$(echo "$ingest_response" | jq -r '.trace_id')
            echo -e "${GREEN}✓${NC} (${CALL_ID:0:8}...)"
        else
            echo -e "${RED}✗ Failed${NC}"
            echo "$ingest_response"
            return 1
        fi
        
        # Step 2: Triage (preserve trace_id from ingest)
        echo -n "  [2/3] Triaging... "
        triage_response=$(curl -s -X POST http://localhost:8002/triage \
            -H "Content-Type: application/json" \
            -d "{
                \"transcript\": \"$transcript\",
                \"call_id\": \"$CALL_ID\",
                \"trace_id\": \"$TRACE_ID\",
                \"consent\": true,
                \"location_hint\": \"Demo Location\"
            }" 2>/dev/null)
        
        if echo "$triage_response" | jq -e '.risk_level' > /dev/null 2>&1; then
            RISK_LEVEL=$(echo "$triage_response" | jq -r '.risk_level')
            BRANCH=$(echo "$triage_response" | jq -r '.branch')
            CATEGORY=$(echo "$triage_response" | jq -r '.case_category')
            HUMAN_REQ=$(echo "$triage_response" | jq -r '.human_required')
            P0_SIGNALS=$(echo "$triage_response" | jq -c '.p0_signals')
            TRACE_ID=$(echo "$triage_response" | jq -r '.trace_id')
            echo -e "${GREEN}✓${NC} (risk: $RISK_LEVEL, branch: $BRANCH)"
        else
            echo -e "${RED}✗ Failed${NC}"
            echo "$triage_response"
            return 1
        fi
        
        # Step 3: Analytics
        echo -n "  [3/3] Recording... "
        analytics_response=$(curl -s -X POST http://localhost:8003/incidents \
            -H "Content-Type: application/json" \
            -d "{
                \"call_id\": \"$CALL_ID\",
                \"trace_id\": \"$TRACE_ID\",
                \"risk_level\": $RISK_LEVEL,
                \"branch\": \"$BRANCH\",
                \"case_category\": \"$CATEGORY\",
                \"human_required\": $HUMAN_REQ,
                \"p0_signals\": $P0_SIGNALS,
                \"location_hint\": \"Demo Location\"
            }" 2>/dev/null)
        
        if echo "$analytics_response" | jq -e '.incident_id' > /dev/null 2>&1; then
            INCIDENT_ID=$(echo "$analytics_response" | jq -r '.incident_id')
            echo -e "${GREEN}✓${NC} (${INCIDENT_ID:0:8}...)"
        else
            echo -e "${RED}✗ Failed${NC}"
            echo "$analytics_response"
            return 1
        fi
        
        echo -e "${GREEN}✓ Complete${NC}"
        echo ""
        return 0
    }
    
    # Scenario 1: Low Risk
    echo -e "${MAGENTA}[1/6] Scenario 1: Low Risk - Public Services${NC}"
    send_direct_call \
        "Low Risk - Pothole Report" \
        "Hola, buenos días. Quiero reportar un bache muy grande en la calle Reforma esquina con Insurgentes. No es una emergencia pero está causando problemas al tráfico. Mi nombre es Juan Pérez y mi teléfono es 5512345678. Gracias." \
        '{"source": "demo_seed", "scenario": "low_risk_public_services"}'
    
    # Scenario 2: Medium Risk
    echo -e "${MAGENTA}[2/6] Scenario 2: Medium Risk - Traffic Accident${NC}"
    send_direct_call \
        "Medium Risk - Traffic Accident" \
        "Hay un accidente de tránsito en Insurgentes con Reforma. Son como tres o cuatro carros chocados. No veo heridos graves pero hay mucho tráfico. Creo que necesitan grúas y tránsito. Estoy en la esquina esperando." \
        '{"source": "demo_seed", "scenario": "medium_risk_validation"}'
    
    # Scenario 3: Critical P0
    echo -e "${MAGENTA}[3/6] Scenario 3: Critical P0 - Child in Danger${NC}"
    send_direct_call \
        "Critical P0 - Child Bleeding" \
        "¡Auxilio! ¡Por favor ayuda! Hay un niño que se cayó de las escaleras y está sangrando mucho de la cabeza. Tiene como 8 años. Está consciente pero sangra mucho. Estamos en el edificio de la calle Madero número 45 en la Colonia Centro. ¡Por favor vengan rápido!" \
        '{"source": "demo_seed", "scenario": "critical_p0_child_danger"}'
    
    # Additional cases
    echo -e "${MAGENTA}[4/6] Additional: Gender Violence${NC}"
    send_direct_call \
        "Gender Violence" \
        "Mi vecina está gritando y se escuchan golpes. Creo que su esposo la está golpeando. Esto pasa seguido. Estoy en el departamento 302 del edificio Juárez 123." \
        '{"source": "demo_seed", "scenario": "gender_violence"}'
    
    echo -e "${MAGENTA}[5/6] Additional: Medical Emergency - Elderly${NC}"
    send_direct_call \
        "Medical Emergency - Elderly" \
        "Mi abuela de 85 años se cayó y no puede levantarse. Le duele mucho la cadera. Está consciente pero con mucho dolor. Necesitamos una ambulancia." \
        '{"source": "demo_seed", "scenario": "medical_elderly"}'
    
    echo -e "${MAGENTA}[6/6] Additional: Fire Emergency${NC}"
    send_direct_call \
        "Fire Emergency" \
        "¡Hay un incendio en el edificio de enfrente! Se ve mucho humo saliendo del tercer piso. Creo que hay gente adentro. Estamos en la calle Hidalgo 234." \
        '{"source": "demo_seed", "scenario": "fire_emergency"}'

# ----------------------------------------------------------------------------
# Mode: n8n Webhook
# ----------------------------------------------------------------------------
else
    # Check if n8n is available
    if ! curl -s http://localhost:5678/healthz > /dev/null 2>&1; then
        echo -e "${RED}Error: n8n is not accessible at http://localhost:5678${NC}"
        echo -e "${YELLOW}Make sure n8n is running and workflow is active${NC}"
        exit 1
    fi
    
    # Get credentials from .env
    if [ -f "$PROJECT_ROOT/.env" ]; then
        source "$PROJECT_ROOT/.env"
        N8N_USER=${N8N_BASIC_AUTH_USER:-admin}
        N8N_PASSWORD=${N8N_BASIC_AUTH_PASSWORD:-changeme}
    else
        N8N_USER="admin"
        N8N_PASSWORD="changeme"
    fi
    
    # Base64 encode credentials for Basic Auth
    AUTH_HEADER="Authorization: Basic $(echo -n "$N8N_USER:$N8N_PASSWORD" | base64)"
    
    # Webhook URL
    WEBHOOK_URL="http://localhost:5678/webhook/911-call"
    
    # Function to send test call via webhook
    send_webhook_call() {
        local scenario=$1
        local data=$2
        
        echo -e "${CYAN}Sending: $scenario${NC}"
        
        response=$(curl -s -w "\n%{http_code}" \
            -X POST \
            -H "Content-Type: application/json" \
            -H "$AUTH_HEADER" \
            -d "$data" \
            "$WEBHOOK_URL" 2>/dev/null)
        
        http_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | head -n-1)
        
        if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
            echo -e "${GREEN}✓ Success${NC} (HTTP $http_code)"
            echo -e "${YELLOW}Response:${NC}"
            echo "$body" | jq '.' 2>/dev/null || echo "$body"
            return 0
        else
            echo -e "${RED}✗ Failed${NC} (HTTP $http_code)"
            echo -e "${YELLOW}Response:${NC}"
            echo "$body"
            return 1
        fi
    }
    
    # Scenario 1
    echo -e "${MAGENTA}[1/6] Scenario 1: Low Risk - Public Services${NC}"
    scenario1_data='{
      "transcript": "Hola, buenos días. Quiero reportar un bache muy grande en la calle Reforma esquina con Insurgentes. No es una emergencia pero está causando problemas al tráfico. Mi nombre es Juan Pérez y mi teléfono es 5512345678. Gracias.",
      "metadata": {
        "source": "demo_seed",
        "timestamp": "2026-06-06T10:30:00Z",
        "scenario": "low_risk_public_services"
      }
    }'
    send_webhook_call "Low Risk - Public Services" "$scenario1_data"
    echo ""
    sleep 2
    
    # Scenario 2
    echo -e "${MAGENTA}[2/6] Scenario 2: Medium Risk - Traffic Accident${NC}"
    scenario2_data='{
      "transcript": "Hay un accidente de tránsito en Insurgentes con Reforma. Son como tres o cuatro carros chocados. No veo heridos graves pero hay mucho tráfico. Creo que necesitan grúas y tránsito. Estoy en la esquina esperando.",
      "metadata": {
        "source": "demo_seed",
        "timestamp": "2026-06-06T11:45:00Z",
        "scenario": "medium_risk_validation"
      }
    }'
    send_webhook_call "Medium Risk - Traffic Accident" "$scenario2_data"
    echo ""
    sleep 2
    
    # Scenario 3
    echo -e "${MAGENTA}[3/6] Scenario 3: Critical P0 - Child in Danger${NC}"
    scenario3_data='{
      "transcript": "¡Auxilio! ¡Por favor ayuda! Hay un niño que se cayó de las escaleras y está sangrando mucho de la cabeza. Tiene como 8 años. Está consciente pero sangra mucho. Estamos en el edificio de la calle Madero número 45 en la Colonia Centro. ¡Por favor vengan rápido!",
      "metadata": {
        "source": "demo_seed",
        "timestamp": "2026-06-06T14:20:00Z",
        "scenario": "critical_p0_child_danger"
      }
    }'
    send_webhook_call "Critical P0 - Child in Danger" "$scenario3_data"
    echo ""
    sleep 2
    
    # Additional cases
    echo -e "${MAGENTA}[4/6] Additional: Gender Violence${NC}"
    gv_data='{
      "transcript": "Mi vecina está gritando y se escuchan golpes. Creo que su esposo la está golpeando. Esto pasa seguido. Estoy en el departamento 302 del edificio Juárez 123.",
      "metadata": {
        "source": "demo_seed",
        "timestamp": "2026-06-06T15:30:00Z",
        "scenario": "gender_violence"
      }
    }'
    send_webhook_call "Gender Violence" "$gv_data"
    echo ""
    sleep 2
    
    echo -e "${MAGENTA}[5/6] Additional: Medical Emergency - Elderly${NC}"
    elderly_data='{
      "transcript": "Mi abuela de 85 años se cayó y no puede levantarse. Le duele mucho la cadera. Está consciente pero con mucho dolor. Necesitamos una ambulancia.",
      "metadata": {
        "source": "demo_seed",
        "timestamp": "2026-06-06T16:00:00Z",
        "scenario": "medical_elderly"
      }
    }'
    send_webhook_call "Medical Emergency - Elderly" "$elderly_data"
    echo ""
    sleep 2
    
    echo -e "${MAGENTA}[6/6] Additional: Fire Emergency${NC}"
    fire_data='{
      "transcript": "¡Hay un incendio en el edificio de enfrente! Se ve mucho humo saliendo del tercer piso. Creo que hay gente adentro. Estamos en la calle Hidalgo 234.",
      "metadata": {
        "source": "demo_seed",
        "timestamp": "2026-06-06T17:15:00Z",
        "scenario": "fire_emergency"
      }
    }'
    send_webhook_call "Fire Emergency" "$fire_data"
    echo ""
fi

# ----------------------------------------------------------------------------
# Verify Data in Database
# ----------------------------------------------------------------------------
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Verifying Data in Database${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Count raw conversations
raw_count=$(docker exec centinela-db psql -U emergency_user -d centinela_demo -t -c "SELECT COUNT(*) FROM raw.conversations;" 2>/dev/null | tr -d ' ')
echo -e "${CYAN}Raw Conversations:${NC} $raw_count"

# Count triage results
triage_count=$(docker exec centinela-db psql -U emergency_user -d centinela_demo -t -c "SELECT COUNT(*) FROM core.triage_results;" 2>/dev/null | tr -d ' ')
echo -e "${CYAN}Triage Results:${NC} $triage_count"

# Count incidents
incident_count=$(docker exec centinela-db psql -U emergency_user -d centinela_demo -t -c "SELECT COUNT(*) FROM analytics.incidents;" 2>/dev/null | tr -d ' ')
echo -e "${CYAN}Incidents:${NC} $incident_count"

echo ""

# Show risk distribution
echo -e "${CYAN}Risk Level Distribution:${NC}"
docker exec centinela-db psql -U emergency_user -d centinela_demo -c "
SELECT 
    risk_level,
    COUNT(*) as count,
    branch
FROM analytics.incidents
GROUP BY risk_level, branch
ORDER BY risk_level;
" 2>/dev/null

echo ""

# Show category distribution
echo -e "${CYAN}Category Distribution:${NC}"
docker exec centinela-db psql -U emergency_user -d centinela_demo -c "
SELECT 
    case_category,
    COUNT(*) as count
FROM analytics.incidents
WHERE case_category IS NOT NULL
GROUP BY case_category
ORDER BY count DESC;
" 2>/dev/null

echo ""

# ----------------------------------------------------------------------------
# Test Analytics Endpoints
# ----------------------------------------------------------------------------
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Testing Analytics Endpoints${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

echo -e "${CYAN}GET /analytics/summary${NC}"
curl -s http://localhost:8003/analytics/summary | jq '.'
echo ""

echo -e "${CYAN}GET /analytics/predictions${NC}"
curl -s http://localhost:8003/analytics/predictions | jq '.volume_forecast'
echo ""

# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Demo Data Seeding Complete${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "${GREEN}✓ Successfully seeded demo data using $MODE mode${NC}"
echo ""
echo -e "${CYAN}What was created:${NC}"
echo -e "  • 3 core test scenarios (low, medium, critical)"
echo -e "  • 3 additional test cases (gender violence, elderly, fire)"
echo -e "  • Raw conversations with PII redaction"
echo -e "  • Triage results with risk scoring"
echo -e "  • Analytics incidents and metrics"
echo ""
echo -e "${CYAN}Next steps:${NC}"
echo -e "1. View incidents: ${GREEN}curl http://localhost:8003/incidents | jq${NC}"
echo -e "2. View analytics: ${GREEN}curl http://localhost:8003/analytics/summary | jq${NC}"
if [ "$MODE" = "direct" ]; then
    echo -e "3. Try n8n mode: ${GREEN}./scripts/05_seed_demo_data.sh n8n${NC}"
else
    echo -e "3. Access n8n dashboard: ${GREEN}http://localhost:5678${NC}"
fi
echo -e "4. Check logs: ${GREEN}./scripts/03_logs.sh${NC}"
echo ""

