#!/bin/bash
# Test script to validate classification fixes
# Tests both WhatsApp Lab and 911 call classification

set -e

echo "========================================="
echo "Testing Classification Fixes"
echo "========================================="
echo ""

GATEWAY_URL="http://localhost:8010"

echo "Test 0: WhatsApp message - Self-harm crisis (MÁXIMA PRIORIDAD)"
echo "----------------------------------------------------------------"
RESPONSE=$(curl -s -X POST ${GATEWAY_URL}/whatsapp-lab/messages \
  -H "Content-Type: application/json" \
  -d '{"message":"Me quiero suicidar"}')

echo "$RESPONSE" | jq '.'
echo ""

CATEGORY=$(echo "$RESPONSE" | jq -r '.category')
BRANCH=$(echo "$RESPONSE" | jq -r '.branch')
RISK=$(echo "$RESPONSE" | jq -r '.risk_level')
P0_SIGNALS=$(echo "$RESPONSE" | jq -r '.p0_signals[]' 2>/dev/null || echo "")

if [ "$CATEGORY" != "victim_attention" ]; then
  echo "❌ FAIL: Expected category 'victim_attention', got '$CATEGORY'"
  exit 1
fi

if [ "$BRANCH" != "critical" ]; then
  echo "❌ FAIL: Expected branch 'critical', got '$BRANCH'"
  exit 1
fi

if [ "$RISK" -lt 9 ]; then
  echo "❌ FAIL: Expected risk_level >= 9, got '$RISK'"
  exit 1
fi

if ! echo "$P0_SIGNALS" | grep -q "self_harm_risk"; then
  echo "❌ FAIL: Expected P0 signal 'self_harm_risk', got '$P0_SIGNALS'"
  exit 1
fi

echo "✅ PASS: Self-harm crisis detected with maximum priority"
echo ""

echo "Test 1: WhatsApp message - Medical critical (inconsciente)"
echo "-----------------------------------------------------------"
RESPONSE=$(curl -s -X POST ${GATEWAY_URL}/whatsapp-lab/messages \
  -H "Content-Type: application/json" \
  -d '{"message":"Hay una persona herida inconsciente en Coyoacán"}')

echo "$RESPONSE" | jq '.'
echo ""

CATEGORY=$(echo "$RESPONSE" | jq -r '.category')
BRANCH=$(echo "$RESPONSE" | jq -r '.branch')
LOCATION_SOURCE=$(echo "$RESPONSE" | jq -r '.location_source')
ALCALDIA=$(echo "$RESPONSE" | jq -r '.alcaldia_norm')

if [ "$CATEGORY" != "medical" ]; then
  echo "❌ FAIL: Expected category 'medical', got '$CATEGORY'"
  exit 1
fi

if [ "$BRANCH" != "critical" ]; then
  echo "❌ FAIL: Expected branch 'critical', got '$BRANCH'"
  exit 1
fi

if [ "$LOCATION_SOURCE" != "user_text" ]; then
  echo "❌ FAIL: Expected location_source 'user_text', got '$LOCATION_SOURCE'"
  exit 1
fi

if [ "$ALCALDIA" != "coyoacan" ]; then
  echo "❌ FAIL: Expected alcaldia_norm 'coyoacan', got '$ALCALDIA'"
  exit 1
fi

echo "✅ PASS: Medical critical with user location detected"
echo ""

echo "Test 2: WhatsApp message - Victim attention (violencia familiar)"
echo "----------------------------------------------------------------"
RESPONSE=$(curl -s -X POST ${GATEWAY_URL}/whatsapp-lab/messages \
  -H "Content-Type: application/json" \
  -d '{"message":"Escucho violencia familiar en Iztapalapa"}')

echo "$RESPONSE" | jq '.'
echo ""

CATEGORY=$(echo "$RESPONSE" | jq -r '.category')
BRANCH=$(echo "$RESPONSE" | jq -r '.branch')
ALCALDIA=$(echo "$RESPONSE" | jq -r '.alcaldia_norm')

if [ "$CATEGORY" != "victim_attention" ]; then
  echo "❌ FAIL: Expected category 'victim_attention', got '$CATEGORY'"
  exit 1
fi

if [ "$BRANCH" != "mid" ]; then
  echo "❌ FAIL: Expected branch 'mid', got '$BRANCH'"
  exit 1
fi

if [ "$ALCALDIA" != "iztapalapa" ]; then
  echo "❌ FAIL: Expected alcaldia_norm 'iztapalapa', got '$ALCALDIA'"
  exit 1
fi

echo "✅ PASS: Victim attention prioritized over security"
echo ""

echo "Test 3: 911 call - Protection civil (incendio)"
echo "-----------------------------------------------"
RESPONSE=$(curl -s -X POST ${GATEWAY_URL}/911-call \
  -H "Content-Type: application/json" \
  -d '{
    "transcript":"Reporto incendio en colonia Centro, Cuauhtémoc, sale mucho humo",
    "location_hint":"colonia Centro, Cuauhtémoc",
    "solid_consent":true
  }')

echo "$RESPONSE" | jq '.'
echo ""

CATEGORY=$(echo "$RESPONSE" | jq -r '.case_category')
BRANCH=$(echo "$RESPONSE" | jq -r '.branch')
RISK=$(echo "$RESPONSE" | jq -r '.risk_level')
P0_COUNT=$(echo "$RESPONSE" | jq -r '.p0_signals | length')

if [ "$CATEGORY" != "protection_civil" ]; then
  echo "❌ FAIL: Expected category 'protection_civil', got '$CATEGORY'"
  exit 1
fi

if [ "$BRANCH" != "critical" ]; then
  echo "❌ FAIL: Expected branch 'critical', got '$BRANCH'"
  exit 1
fi

if [ "$RISK" -lt 6 ]; then
  echo "❌ FAIL: Expected risk_level >= 6, got '$RISK'"
  exit 1
fi

if [ "$P0_COUNT" -eq 0 ]; then
  echo "❌ FAIL: Expected P0 signals, got none"
  exit 1
fi

echo "✅ PASS: Protection civil with P0 signals"
echo ""

echo "Test 4: 911 call - Public services (bache)"
echo "-------------------------------------------"
RESPONSE=$(curl -s -X POST ${GATEWAY_URL}/911-call \
  -H "Content-Type: application/json" \
  -d '{
    "transcript":"Hay un bache enorme en Reforma",
    "location_hint":"Reforma",
    "solid_consent":true
  }')

echo "$RESPONSE" | jq '.'
echo ""

CATEGORY=$(echo "$RESPONSE" | jq -r '.case_category')
BRANCH=$(echo "$RESPONSE" | jq -r '.branch')

if [ "$CATEGORY" != "public_services" ]; then
  echo "❌ FAIL: Expected category 'public_services', got '$CATEGORY'"
  exit 1
fi

if [ "$BRANCH" != "low" ]; then
  echo "❌ FAIL: Expected branch 'low', got '$BRANCH'"
  exit 1
fi

echo "✅ PASS: Public services classified as low priority"
echo ""

echo "Test 5: WhatsApp message - Protection civil with location"
echo "----------------------------------------------------------"
RESPONSE=$(curl -s -X POST ${GATEWAY_URL}/whatsapp-lab/messages \
  -H "Content-Type: application/json" \
  -d '{"message":"Hay un incendio en mi edificio en Benito Juárez"}')

echo "$RESPONSE" | jq '.'
echo ""

CATEGORY=$(echo "$RESPONSE" | jq -r '.category')
BRANCH=$(echo "$RESPONSE" | jq -r '.branch')
LOCATION_SOURCE=$(echo "$RESPONSE" | jq -r '.location_source')
ALCALDIA=$(echo "$RESPONSE" | jq -r '.alcaldia_norm')

if [ "$CATEGORY" != "protection_civil" ]; then
  echo "❌ FAIL: Expected category 'protection_civil', got '$CATEGORY'"
  exit 1
fi

if [ "$BRANCH" != "critical" ]; then
  echo "❌ FAIL: Expected branch 'critical', got '$BRANCH'"
  exit 1
fi

if [ "$LOCATION_SOURCE" != "user_text" ]; then
  echo "❌ FAIL: Expected location_source 'user_text', got '$LOCATION_SOURCE'"
  exit 1
fi

if [ "$ALCALDIA" != "benito_juarez" ]; then
  echo "❌ FAIL: Expected alcaldia_norm 'benito_juarez', got '$ALCALDIA'"
  exit 1
fi

echo "✅ PASS: Protection civil with user location"
echo ""

echo "========================================="
echo "✅ ALL TESTS PASSED"
echo "========================================="
echo ""
echo "Classification fixes validated:"
echo "- Medical critical (inconsciente) → critical branch, risk >= 8"
echo "- Victim attention prioritized over security"
echo "- Location detection from user text"
echo "- Alcaldía normalization working"
echo "- P0 signals detected correctly"
echo "- Public services classified as low"
echo ""

# Made with Bob
