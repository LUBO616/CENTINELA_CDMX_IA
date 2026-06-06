#!/bin/bash
# Test script for WhatsApp Lab functionality
# Tests message-only format with auto-enrichment

set -e

GATEWAY_URL="http://localhost:8010"
ENDPOINT="${GATEWAY_URL}/whatsapp-lab/messages"

echo "=========================================="
echo "Testing WhatsApp Lab - Message-Only Format"
echo "Auto-Enrichment: Phone, Location, Time, Alcaldía, Coordinates"
echo "=========================================="
echo ""

# Test 1: Incendio with location in text (Centro)
echo "Test 1: Incendio (Protection Civil - Critical)"
echo "Location: Centro (should be detected from text)"
echo "----------------------------------------------"
RESPONSE=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hay un incendio en mi edificio en la colonia Centro"
  }')

echo "Response:"
echo "$RESPONSE" | jq '.'
echo ""

CATEGORY=$(echo "$RESPONSE" | jq -r '.category')
BRANCH=$(echo "$RESPONSE" | jq -r '.branch')

if [ "$CATEGORY" = "protection_civil" ] && [ "$BRANCH" = "critical" ]; then
  echo "✅ Test 1 PASSED: Correctly classified as protection_civil/critical"
else
  echo "❌ Test 1 FAILED: Expected protection_civil/critical, got $CATEGORY/$BRANCH"
fi
echo ""

# Test 2: Bache without location (should generate synthetic)
echo "Test 2: Bache (Public Services - Low)"
echo "Location: None in text (should generate synthetic 911 geolocation)"
echo "----------------------------------------------"
RESPONSE=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hay un bache muy grande en la calle Reforma"
  }')

echo "Response:"
echo "$RESPONSE" | jq '.'
echo ""

CATEGORY=$(echo "$RESPONSE" | jq -r '.category')
BRANCH=$(echo "$RESPONSE" | jq -r '.branch')

if [ "$CATEGORY" = "public_services" ] && [ "$BRANCH" = "low" ]; then
  echo "✅ Test 2 PASSED: Correctly classified as public_services/low"
else
  echo "❌ Test 2 FAILED: Expected public_services/low, got $CATEGORY/$BRANCH"
fi
echo ""

# Test 3: Herido inconsciente (Medical Critical with P0)
echo "Test 3: Herido inconsciente (Medical - Critical with P0)"
echo "Location: Coyoacán (should be detected from text)"
echo "----------------------------------------------"
RESPONSE=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hay una persona herida inconsciente en Coyoacán"
  }')

echo "Response:"
echo "$RESPONSE" | jq '.'
echo ""

CATEGORY=$(echo "$RESPONSE" | jq -r '.category')
BRANCH=$(echo "$RESPONSE" | jq -r '.branch')
P0_COUNT=$(echo "$RESPONSE" | jq -r '.p0_signals | length')

if [ "$CATEGORY" = "medical" ] && [ "$BRANCH" = "critical" ] && [ "$P0_COUNT" -gt 0 ]; then
  echo "✅ Test 3 PASSED: Correctly classified as medical/critical with P0 signals"
else
  echo "❌ Test 3 FAILED: Expected medical/critical with P0, got $CATEGORY/$BRANCH (P0: $P0_COUNT)"
fi
echo ""

# Test 4: Robo con arma (Security - Critical)
echo "Test 4: Robo con arma (Security - Critical)"
echo "Location: Polanco (should be detected from text)"
echo "----------------------------------------------"
RESPONSE=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Me están asaltando con un arma en Polanco"
  }')

echo "Response:"
echo "$RESPONSE" | jq '.'
echo ""

CATEGORY=$(echo "$RESPONSE" | jq -r '.category')
BRANCH=$(echo "$RESPONSE" | jq -r '.branch')
HUMAN_REQUIRED=$(echo "$RESPONSE" | jq -r '.human_required')

if [ "$CATEGORY" = "security" ] && [ "$BRANCH" = "critical" ] && [ "$HUMAN_REQUIRED" = "true" ]; then
  echo "✅ Test 4 PASSED: Correctly classified as security/critical requiring human"
else
  echo "❌ Test 4 FAILED: Expected security/critical/human, got $CATEGORY/$BRANCH/$HUMAN_REQUIRED"
fi
echo ""

# Test 5: Violencia Familiar (Victim Attention - BEFORE Security)
echo "Test 5: Violencia Familiar (Victim Attention - Mid)"
echo "Location: None (should generate synthetic)"
echo "IMPORTANT: Should classify as victim_attention BEFORE security"
echo "----------------------------------------------"
RESPONSE=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Escucho gritos y golpes en el departamento de al lado, creo que hay violencia familiar"
  }')

echo "Response:"
echo "$RESPONSE" | jq '.'
echo ""

CATEGORY=$(echo "$RESPONSE" | jq -r '.category')
BRANCH=$(echo "$RESPONSE" | jq -r '.branch')

if [ "$CATEGORY" = "victim_attention" ]; then
  echo "✅ Test 5 PASSED: Correctly classified as victim_attention (not security)"
else
  echo "❌ Test 5 FAILED: Expected victim_attention, got $CATEGORY"
fi
echo ""

# Test enrichment by checking recent messages
echo "=========================================="
echo "Testing Enrichment - Recent Messages"
echo "=========================================="
echo ""

RECENT=$(curl -s "${GATEWAY_URL}/whatsapp-lab/messages/recent?limit=5")
echo "Recent messages (showing enriched data):"
echo "$RECENT" | jq '.'
echo ""

# Validate enrichment fields
echo "Validating enrichment fields..."
FIRST_MSG=$(echo "$RECENT" | jq -r '.[0]')

FROM_REDACTED=$(echo "$FIRST_MSG" | jq -r '.from_number_redacted')
LOCATION_HINT=$(echo "$FIRST_MSG" | jq -r '.location_hint')
LOCATION_SOURCE=$(echo "$FIRST_MSG" | jq -r '.location_source')
INCIDENT_TIME=$(echo "$FIRST_MSG" | jq -r '.incident_time')
ALCALDIA=$(echo "$FIRST_MSG" | jq -r '.alcaldia_norm')
LAT=$(echo "$FIRST_MSG" | jq -r '.latitude')
LON=$(echo "$FIRST_MSG" | jq -r '.longitude')

echo "Enrichment check for most recent message:"
echo "  from_number_redacted: $FROM_REDACTED"
echo "  location_hint: $LOCATION_HINT"
echo "  location_source: $LOCATION_SOURCE"
echo "  incident_time: $INCIDENT_TIME"
echo "  alcaldia_norm: $ALCALDIA"
echo "  latitude: $LAT"
echo "  longitude: $LON"
echo ""

if [ "$FROM_REDACTED" != "null" ] && [ "$LOCATION_HINT" != "null" ] && [ "$INCIDENT_TIME" != "null" ]; then
  echo "✅ Enrichment PASSED: All required fields present"
else
  echo "❌ Enrichment FAILED: Missing required fields"
fi
echo ""

# Test Summary endpoint
echo "=========================================="
echo "Testing Summary Endpoint"
echo "=========================================="
echo ""

SUMMARY=$(curl -s "${GATEWAY_URL}/whatsapp-lab/summary")
echo "Summary Response:"
echo "$SUMMARY" | jq '.'
echo ""

TOTAL_MESSAGES=$(echo "$SUMMARY" | jq -r '.total_messages')
if [ "$TOTAL_MESSAGES" -ge 5 ]; then
  echo "✅ Summary endpoint working: $TOTAL_MESSAGES total messages"
else
  echo "⚠️  Summary shows $TOTAL_MESSAGES messages (expected at least 5)"
fi
echo ""

echo "=========================================="
echo "All Tests Completed"
echo "=========================================="
echo ""
echo "Summary:"
echo "- 5 message classification tests (message-only format)"
echo "- Auto-enrichment validation"
echo "- Summary endpoint tested"
echo "- Recent messages endpoint tested"
echo ""
echo "Validation Checklist:"
echo "✓ All messages should have from_number_redacted: ***5678"
echo "✓ All messages should have incident_time (current timestamp)"
echo "✓ Messages with 'Centro', 'Coyoacán', 'Polanco' → location_source: user_text"
echo "✓ Messages without location → location_source: synthetic_911_geolocation"
echo "✓ All messages should have alcaldia_norm"
echo "✓ All messages should have latitude/longitude"
echo "✓ 'inconsciente' should trigger medical_critical P0"
echo "✓ 'violencia familiar' should classify as victim_attention (not security)"
echo "✓ 'arma' should trigger security critical"
echo ""
echo "Check the responses above for detailed results."

# Made with Bob
