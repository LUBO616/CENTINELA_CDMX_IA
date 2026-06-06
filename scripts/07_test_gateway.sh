#!/bin/bash

# ============================================================================
# Test API Gateway - 911 AI Flow Demo
# ============================================================================
# Este script prueba el API Gateway que resuelve CORS para Lovable
# ============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_color() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Función para verificar respuesta
check_response() {
    local response=$1
    local expected=$2
    local test_name=$3
    
    if echo "$response" | grep -q "$expected"; then
        print_color "$GREEN" "✅ $test_name: PASSED"
        return 0
    else
        print_color "$RED" "❌ $test_name: FAILED"
        echo "Response: $response"
        return 1
    fi
}

print_color "$BLUE" "============================================"
print_color "$BLUE" "Testing API Gateway (Port 8010)"
print_color "$BLUE" "============================================"
echo ""

# Contador de tests
TOTAL_TESTS=0
PASSED_TESTS=0

# ============================================================================
# Test 1: Health Check
# ============================================================================
print_color "$YELLOW" "Test 1: Health Check"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

RESPONSE=$(curl -s http://localhost:8010/health)
if check_response "$RESPONSE" "healthy" "Gateway health check"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
fi
echo ""

# ============================================================================
# Test 2: POST /911-call - Bajo Riesgo
# ============================================================================
print_color "$YELLOW" "Test 2: POST /911-call - Bajo Riesgo (Bache)"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

RESPONSE=$(curl -s -X POST http://localhost:8010/911-call \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Hay un bache grande en la calle principal",
    "location_hint": "Colonia Centro",
    "solid_consent": true
  }')

if check_response "$RESPONSE" "call_id" "POST /911-call (low risk)"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
    RISK_LEVEL=$(echo "$RESPONSE" | jq -r '.risk_level' 2>/dev/null)
    BRANCH=$(echo "$RESPONSE" | jq -r '.branch' 2>/dev/null)
    print_color "$GREEN" "  Risk Level: $RISK_LEVEL"
    print_color "$GREEN" "  Branch: $BRANCH"
fi
echo ""

# ============================================================================
# Test 3: POST /911-call - Crítico P0
# ============================================================================
print_color "$YELLOW" "Test 3: POST /911-call - Crítico P0 (Incendio)"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

RESPONSE=$(curl -s -X POST http://localhost:8010/911-call \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Hay un incendio en mi edificio y mi hijo está atrapado",
    "location_hint": "Colonia Roma",
    "solid_consent": true
  }')

if check_response "$RESPONSE" "call_id" "POST /911-call (critical P0)"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
    RISK_LEVEL=$(echo "$RESPONSE" | jq -r '.risk_level' 2>/dev/null)
    BRANCH=$(echo "$RESPONSE" | jq -r '.branch' 2>/dev/null)
    HUMAN_REQ=$(echo "$RESPONSE" | jq -r '.human_required' 2>/dev/null)
    P0_SIGNALS=$(echo "$RESPONSE" | jq -r '.p0_signals | join(", ")' 2>/dev/null)
    print_color "$GREEN" "  Risk Level: $RISK_LEVEL"
    print_color "$GREEN" "  Branch: $BRANCH"
    print_color "$GREEN" "  Human Required: $HUMAN_REQ"
    print_color "$GREEN" "  P0 Signals: $P0_SIGNALS"
fi
echo ""

# ============================================================================
# Test 4: GET /analytics/summary
# ============================================================================
print_color "$YELLOW" "Test 4: GET /analytics/summary"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

RESPONSE=$(curl -s http://localhost:8010/analytics/summary)
if check_response "$RESPONSE" "total_incidents" "GET /analytics/summary"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TOTAL=$(echo "$RESPONSE" | jq -r '.total_incidents' 2>/dev/null)
    CRITICAL=$(echo "$RESPONSE" | jq -r '.by_branch.critical' 2>/dev/null)
    print_color "$GREEN" "  Total Incidents: $TOTAL"
    print_color "$GREEN" "  Critical: $CRITICAL"
fi
echo ""

# ============================================================================
# Test 5: GET /analytics/predictions
# ============================================================================
print_color "$YELLOW" "Test 5: GET /analytics/predictions"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

RESPONSE=$(curl -s http://localhost:8010/analytics/predictions)
if check_response "$RESPONSE" "volume_forecast" "GET /analytics/predictions"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
    PREDICTED=$(echo "$RESPONSE" | jq -r '.volume_forecast.predicted_calls' 2>/dev/null)
    print_color "$GREEN" "  Predicted Calls: $PREDICTED"
fi
echo ""

# ============================================================================
# Test 6: CORS Headers
# ============================================================================
print_color "$YELLOW" "Test 6: CORS Headers"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

RESPONSE=$(curl -s -I -X OPTIONS http://localhost:8010/911-call \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST")

if echo "$RESPONSE" | grep -q "access-control-allow-origin"; then
    print_color "$GREEN" "✅ CORS Headers: PASSED"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo "$RESPONSE" | grep -i "access-control"
else
    print_color "$RED" "❌ CORS Headers: FAILED"
fi
echo ""

# ============================================================================
# Test 7: Error Handling - Invalid Payload
# ============================================================================
print_color "$YELLOW" "Test 7: Error Handling - Invalid Payload"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

RESPONSE=$(curl -s -X POST http://localhost:8010/911-call \
  -H "Content-Type: application/json" \
  -d '{"invalid": "payload"}')

if echo "$RESPONSE" | grep -q "detail"; then
    print_color "$GREEN" "✅ Error Handling: PASSED"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
else
    print_color "$RED" "❌ Error Handling: FAILED"
fi
echo ""

# ============================================================================
# Resumen
# ============================================================================
print_color "$BLUE" "============================================"
print_color "$BLUE" "Test Summary"
print_color "$BLUE" "============================================"
echo ""
print_color "$GREEN" "Passed: $PASSED_TESTS / $TOTAL_TESTS"

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    print_color "$GREEN" "✅ All tests passed!"
    exit 0
else
    FAILED=$((TOTAL_TESTS - PASSED_TESTS))
    print_color "$RED" "❌ $FAILED test(s) failed"
    exit 1
fi

# Made with Bob
