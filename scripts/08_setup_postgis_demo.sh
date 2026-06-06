#!/bin/bash
# ============================================================================
# 911 AI Flow Demo - PostGIS Demo Setup Script
# ============================================================================
#
# Purpose: Orchestrate generation and loading of PostGIS demo data
#
# Steps:
# 1. Generate synthetic alcaldía polygons (GeoJSON)
# 2. Generate synthetic geocoded incidents (CSV)
# 3. Load all data into PostGIS and perform spatial join
#
# IDEMPOTENT: Safe to run multiple times
# - Regenerates all synthetic data files
# - Reloads PostGIS tables
# - Re-performs spatial join
#
# DISCLAIMER: All data is SYNTHETIC for educational purposes only
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

echo "======================================================================"
echo "911 AI Flow Demo - PostGIS Demo Setup"
echo "======================================================================"
echo ""
echo -e "${YELLOW}⚠️  DISCLAIMER: Generating SYNTHETIC demo data${NC}"
echo "   - NO real geographic boundaries"
echo "   - NO real emergency incidents"
echo "   - For educational purposes only"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 not found${NC}"
    echo "   Please install Python 3"
    exit 1
fi

# Check if required files exist
if [ ! -f "$PROJECT_ROOT/tools/generate_synthetic_geo.py" ]; then
    echo -e "${RED}❌ Error: tools/generate_synthetic_geo.py not found${NC}"
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/tools/generate_synthetic_incidents.py" ]; then
    echo -e "${RED}❌ Error: tools/generate_synthetic_incidents.py not found${NC}"
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/tools/load_postgis_demo_data.py" ]; then
    echo -e "${RED}❌ Error: tools/load_postgis_demo_data.py not found${NC}"
    exit 1
fi

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "   Please create .env from .env.example"
    exit 1
fi

# ============================================================================
# Step 1: Generate Synthetic Alcaldía Polygons
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 1/3: Generate Synthetic Alcaldía Polygons${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd "$PROJECT_ROOT"

if python3 tools/generate_synthetic_geo.py; then
    echo ""
    echo -e "${GREEN}✅ Alcaldía polygons generated successfully${NC}"
else
    echo ""
    echo -e "${RED}❌ Failed to generate alcaldía polygons${NC}"
    exit 1
fi

# Verify output file
if [ ! -f "$PROJECT_ROOT/data/geo/alcaldias_cdmx_synthetic.geojson" ]; then
    echo -e "${RED}❌ Error: GeoJSON file not created${NC}"
    exit 1
fi

echo ""

# ============================================================================
# Step 2: Generate Synthetic Geocoded Incidents
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 2/3: Generate Synthetic Geocoded Incidents${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if python3 tools/generate_synthetic_incidents.py; then
    echo ""
    echo -e "${GREEN}✅ Incidents generated successfully${NC}"
else
    echo ""
    echo -e "${RED}❌ Failed to generate incidents${NC}"
    exit 1
fi

# Verify output file
if [ ! -f "$PROJECT_ROOT/data/demo/incidentes_demo_geocoded.csv" ]; then
    echo -e "${RED}❌ Error: Incidents CSV file not created${NC}"
    exit 1
fi

echo ""

# ============================================================================
# Step 3: Load Data into PostGIS
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 3/3: Load Data into PostGIS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if python3 tools/load_postgis_demo_data.py; then
    echo ""
    echo -e "${GREEN}✅ Data loaded into PostGIS successfully${NC}"
else
    echo ""
    echo -e "${RED}❌ Failed to load data into PostGIS${NC}"
    exit 1
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo "======================================================================"
echo -e "${GREEN}✅ PostGIS Demo Setup Complete!${NC}"
echo "======================================================================"
echo ""
echo "📊 Generated files:"
echo "   - data/geo/alcaldias_cdmx_synthetic.geojson"
echo "   - data/demo/incidentes_demo_geocoded.csv"
echo ""
echo "🗄️  PostGIS tables populated:"
echo "   - geo.alcaldias_geom (16 alcaldías)"
echo "   - geo.synthetic_incident_points (≥160 incidents)"
echo "   - economia.digital_access_alcaldia (16 records)"
echo ""
echo "🔗 Spatial join performed:"
echo "   - All incidents assigned to alcaldías via ST_Contains"
echo ""
echo "🎯 Next steps:"
echo "   1. Validate: ./scripts/09_test_postgis_metrics.sh"
echo "   2. Generate metrics: python3 tools/generate_judge_metrics_postgis.py"
echo ""
echo -e "${YELLOW}⚠️  REMINDER: All data is SYNTHETIC for demo purposes only${NC}"
echo ""

# Made with Bob
