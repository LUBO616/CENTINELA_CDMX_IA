#!/bin/bash
# ============================================================================
# 911 AI Flow Demo - PostGIS Metrics Validation Script
# ============================================================================
#
# Purpose: Validate PostGIS installation and loaded demo data
#
# Tests:
# 1. PostGIS extension is installed and working
# 2. Schemas exist (geo, economia)
# 3. Tables are populated with correct counts
# 4. Spatial join was successful (no unassigned incidents)
# 5. ST_Covers query works correctly
# 6. Existing endpoints still work (health, analytics)
#
# DOES NOT test endpoints yet (Gate 6B)
# - No /judge/metrics/postgis validation
# - No /judge/geo/alcaldias validation
#
# Author: 911 AI Flow Demo Team
# License: Educational Use Only
# ============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# Database connection parameters
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-ai911_db}"
DB_USER="${POSTGRES_USER:-ai911_user}"
DB_PASSWORD="${POSTGRES_PASSWORD}"

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

echo "======================================================================"
echo "911 AI Flow Demo - PostGIS Metrics Validation"
echo "======================================================================"
echo ""
echo "🔍 Testing PostGIS installation and demo data"
echo ""

# ============================================================================
# Helper Functions
# ============================================================================

run_sql() {
    local query="$1"
    (cd "$PROJECT_ROOT" && docker compose exec -T -e PGPASSWORD="$DB_PASSWORD" postgres \
        psql -U "$DB_USER" -d "$DB_NAME" -t -A -c "$query" 2>/dev/null)
}

test_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((++TESTS_PASSED))
}

test_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((++TESTS_FAILED))
}

test_info() {
    echo -e "${BLUE}ℹ️  INFO${NC}: $1"
}

# ============================================================================
# Test 1: PostGIS Extension
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Test 1: PostGIS Extension${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

POSTGIS_VERSION=$(run_sql "SELECT postgis_version();")
if [ -n "$POSTGIS_VERSION" ]; then
    test_pass "PostGIS extension installed"
    test_info "Version: $POSTGIS_VERSION"
else
    test_fail "PostGIS extension not found"
fi

echo ""

# ============================================================================
# Test 2: Schemas Exist
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Test 2: Schemas Exist${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

GEO_SCHEMA=$(run_sql "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'geo';")
if [ "$GEO_SCHEMA" = "1" ]; then
    test_pass "Schema 'geo' exists"
else
    test_fail "Schema 'geo' not found"
fi

ECONOMIA_SCHEMA=$(run_sql "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'economia';")
if [ "$ECONOMIA_SCHEMA" = "1" ]; then
    test_pass "Schema 'economia' exists"
else
    test_fail "Schema 'economia' not found"
fi

echo ""

# ============================================================================
# Test 3: Tables Populated
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Test 3: Tables Populated${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Test alcaldias_geom
ALCALDIA_COUNT=$(run_sql "SELECT COUNT(*) FROM geo.alcaldias_geom;")
if [ "$ALCALDIA_COUNT" = "16" ]; then
    test_pass "geo.alcaldias_geom has 16 records"
else
    test_fail "geo.alcaldias_geom has $ALCALDIA_COUNT records (expected 16)"
fi

# Test synthetic_incident_points
INCIDENT_COUNT=$(run_sql "SELECT COUNT(*) FROM geo.synthetic_incident_points;")
if [ "$INCIDENT_COUNT" -ge 160 ]; then
    test_pass "geo.synthetic_incident_points has $INCIDENT_COUNT records (≥160)"
else
    test_fail "geo.synthetic_incident_points has $INCIDENT_COUNT records (expected ≥160)"
fi

# Test digital_access_alcaldia
DIGITAL_COUNT=$(run_sql "SELECT COUNT(*) FROM economia.digital_access_alcaldia;")
if [ "$DIGITAL_COUNT" = "16" ]; then
    test_pass "economia.digital_access_alcaldia has 16 records"
else
    test_fail "economia.digital_access_alcaldia has $DIGITAL_COUNT records (expected 16)"
fi

echo ""

# ============================================================================
# Test 4: Spatial Join Success
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Test 4: Spatial Join Success${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

UNJOINED_COUNT=$(run_sql "SELECT COUNT(*) FROM geo.synthetic_incident_points WHERE alcaldia_joined IS NULL;")
if [ "$UNJOINED_COUNT" = "0" ]; then
    test_pass "All incidents assigned to alcaldías (0 unassigned)"
else
    test_fail "$UNJOINED_COUNT incidents not assigned to any alcaldía"
fi

JOINED_COUNT=$(run_sql "SELECT COUNT(*) FROM geo.synthetic_incident_points WHERE alcaldia_joined IS NOT NULL;")
test_info "Incidents with alcaldía: $JOINED_COUNT"

echo ""

# ============================================================================
# Test 5: ST_Covers Query Works
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Test 5: ST_Covers Query Works${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Test ST_Covers with a sample query
ST_CONTAINS_COUNT=$(run_sql "
    SELECT COUNT(*) 
    FROM geo.synthetic_incident_points p
    JOIN geo.alcaldias_geom a ON ST_Covers(a.geom, p.geom)
;")

if [ "$ST_CONTAINS_COUNT" -gt 0 ]; then
    test_pass "ST_Covers query works ($ST_CONTAINS_COUNT matches)"
else
    test_fail "ST_Covers query returned 0 matches"
fi

echo ""

# ============================================================================
# Test 6: Incident Distribution
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Test 6: Incident Distribution${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Get branch distribution
BRANCH_DIST=$(run_sql "
    SELECT branch, COUNT(*) 
    FROM geo.synthetic_incident_points 
    GROUP BY branch 
    ORDER BY branch;
")

echo "Branch distribution:"
echo "$BRANCH_DIST" | while IFS='|' read -r branch count; do
    if [ -n "$branch" ]; then
        test_info "$branch: $count incidents"
    fi
done

# Get P0 count
P0_COUNT=$(run_sql "SELECT COUNT(*) FROM geo.synthetic_incident_points WHERE p0_signals IS NOT NULL AND p0_signals != '';")
test_info "Incidents with P0 signals: $P0_COUNT"

echo ""

# ============================================================================
# Test 7: Existing Endpoints Still Work
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Test 7: Existing Endpoints Still Work${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Test gateway health
GATEWAY_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8010/health 2>/dev/null || echo "000")
if [ "$GATEWAY_HEALTH" = "200" ]; then
    test_pass "Gateway health endpoint responds (200)"
else
    test_fail "Gateway health endpoint failed (HTTP $GATEWAY_HEALTH)"
fi

# Test analytics summary
ANALYTICS_SUMMARY=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8010/analytics/summary 2>/dev/null || echo "000")
if [ "$ANALYTICS_SUMMARY" = "200" ]; then
    test_pass "Analytics summary endpoint responds (200)"
else
    test_fail "Analytics summary endpoint failed (HTTP $ANALYTICS_SUMMARY)"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo "======================================================================"
echo "Test Results Summary"
echo "======================================================================"
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
    echo ""
    echo "   Total tests: $TOTAL_TESTS"
    echo "   Passed: $TESTS_PASSED"
    echo "   Failed: $TESTS_FAILED"
    echo ""
    echo "🎯 PostGIS demo data is ready!"
    echo ""
    echo "Next steps:"
    echo "   1. Generate judge metrics: python3 tools/generate_judge_metrics_postgis.py"
    echo "   2. Add endpoints to api-analytics (Gate 6B)"
    echo "   3. Add proxies to api-gateway (Gate 6B)"
    echo ""
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "   Total tests: $TOTAL_TESTS"
    echo "   Passed: $TESTS_PASSED"
    echo "   Failed: $TESTS_FAILED"
    echo ""
    echo "Please review the failures above and fix issues."
    echo ""
    exit 1
fi

# Made with Bob
