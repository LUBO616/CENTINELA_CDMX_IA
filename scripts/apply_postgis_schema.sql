-- ============================================================================
-- 911 AI Flow Demo - PostGIS Schema Setup
-- ============================================================================
-- 
-- Purpose: Create PostGIS extension, schemas, and tables for geospatial analysis
-- 
-- IDEMPOTENT: Safe to run multiple times
-- - Uses IF NOT EXISTS for all CREATE statements
-- - Does NOT drop or truncate existing data
-- - Only creates missing structures
-- 
-- Schemas:
-- - geo: Geospatial data (alcaldías polygons, incident points)
-- - economia: Economic/equity data (digital access index)
-- 
-- DISCLAIMER: Contains SYNTHETIC demo data only
-- - NO real geographic boundaries
-- - NO real emergency incidents
-- - For educational purposes only
-- 
-- Author: 911 AI Flow Demo Team
-- License: Educational Use Only
-- ============================================================================

-- Enable PostGIS extension
-- This adds spatial data types (geometry, geography) and functions (ST_*)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Verify PostGIS is available
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis') THEN
        RAISE EXCEPTION 'PostGIS extension not available';
    END IF;
END $$;

-- ============================================================================
-- Schema: geo
-- Purpose: Geospatial data for territorial analysis
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS geo;

-- Table: alcaldias_geom
-- Purpose: Store synthetic alcaldía polygons for spatial queries
-- SRID: 4326 (WGS84 - standard lat/lon coordinate system)
CREATE TABLE IF NOT EXISTS geo.alcaldias_geom (
    id SERIAL PRIMARY KEY,
    alcaldia VARCHAR(100) NOT NULL,           -- Original name with accents
    alcaldia_norm VARCHAR(100) NOT NULL,      -- Normalized name (snake_case)
    geom GEOMETRY(MultiPolygon, 4326) NOT NULL, -- Polygon geometry
    synthetic BOOLEAN DEFAULT true,           -- Flag: synthetic data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(alcaldia_norm)
);

-- Spatial index for fast ST_Contains queries
CREATE INDEX IF NOT EXISTS idx_alcaldias_geom_gist 
ON geo.alcaldias_geom USING GIST(geom);

-- Regular index for alcaldia lookups
CREATE INDEX IF NOT EXISTS idx_alcaldias_norm 
ON geo.alcaldias_geom(alcaldia_norm);

-- Table: synthetic_incident_points
-- Purpose: Store synthetic incident locations as points
CREATE TABLE IF NOT EXISTS geo.synthetic_incident_points (
    id SERIAL PRIMARY KEY,
    incident_id VARCHAR(50) NOT NULL,         -- INC-XXXXXX format
    call_id UUID NOT NULL,                    -- Original call UUID
    branch VARCHAR(20) NOT NULL,              -- low|mid|critical
    risk_level INTEGER NOT NULL,              -- 1-10
    case_category VARCHAR(50),                -- security, medical, etc.
    human_required BOOLEAN DEFAULT false,     -- Requires human operator
    p0_signals TEXT,                          -- Comma-separated P0 signals
    alcaldia VARCHAR(100),                    -- Original alcaldia from CSV
    alcaldia_joined VARCHAR(100),             -- Alcaldia from spatial join (ST_Contains)
    geom GEOMETRY(Point, 4326) NOT NULL,      -- Point geometry (lat, lon)
    created_at TIMESTAMP NOT NULL,            -- Incident timestamp
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(incident_id)
);

-- Spatial index for point queries
CREATE INDEX IF NOT EXISTS idx_incident_points_gist 
ON geo.synthetic_incident_points USING GIST(geom);

-- Regular indexes for common queries
CREATE INDEX IF NOT EXISTS idx_incident_branch 
ON geo.synthetic_incident_points(branch);

CREATE INDEX IF NOT EXISTS idx_incident_risk 
ON geo.synthetic_incident_points(risk_level);

CREATE INDEX IF NOT EXISTS idx_incident_alcaldia_joined 
ON geo.synthetic_incident_points(alcaldia_joined);

CREATE INDEX IF NOT EXISTS idx_incident_created_at 
ON geo.synthetic_incident_points(created_at);

-- ============================================================================
-- Schema: economia
-- Purpose: Economic and equity metrics data
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS economia;

-- Table: digital_access_alcaldia
-- Purpose: Store digital access index by alcaldía for equity analysis
CREATE TABLE IF NOT EXISTS economia.digital_access_alcaldia (
    id SERIAL PRIMARY KEY,
    alcaldia_norm VARCHAR(100) NOT NULL,      -- Normalized alcaldia name
    digital_access_index NUMERIC(4,2) NOT NULL, -- 0.00 to 1.00
    percentile INTEGER,                       -- Percentile rank (0-100)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(alcaldia_norm)
);

-- Index for alcaldia lookups
CREATE INDEX IF NOT EXISTS idx_digital_access_alcaldia 
ON economia.digital_access_alcaldia(alcaldia_norm);

-- ============================================================================
-- Validation Views
-- Purpose: Quick validation queries for data quality
-- ============================================================================

-- View: geo.validation_summary
-- Purpose: Summary of loaded geospatial data
CREATE OR REPLACE VIEW geo.validation_summary AS
SELECT
    'alcaldias_geom' AS table_name,
    COUNT(*) AS row_count,
    COUNT(DISTINCT alcaldia_norm) AS unique_alcaldias,
    MIN(created_at) AS earliest_record,
    MAX(created_at) AS latest_record
FROM geo.alcaldias_geom
UNION ALL
SELECT
    'synthetic_incident_points' AS table_name,
    COUNT(*) AS row_count,
    COUNT(DISTINCT alcaldia_joined) AS unique_alcaldias,
    MIN(created_at) AS earliest_record,
    MAX(created_at) AS latest_record
FROM geo.synthetic_incident_points;

-- View: geo.spatial_join_validation
-- Purpose: Validate that all incidents have been spatially joined to an alcaldía
CREATE OR REPLACE VIEW geo.spatial_join_validation AS
SELECT
    COUNT(*) AS total_incidents,
    COUNT(alcaldia_joined) AS incidents_with_alcaldia,
    COUNT(*) - COUNT(alcaldia_joined) AS incidents_without_alcaldia,
    ROUND(100.0 * COUNT(alcaldia_joined) / NULLIF(COUNT(*), 0), 2) AS join_success_rate
FROM geo.synthetic_incident_points;

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON SCHEMA geo IS 'Geospatial data for territorial equity analysis (SYNTHETIC demo data only)';
COMMENT ON SCHEMA economia IS 'Economic and equity metrics data (SYNTHETIC demo data only)';

COMMENT ON TABLE geo.alcaldias_geom IS 'Synthetic alcaldía polygons for spatial queries (NOT official boundaries)';
COMMENT ON TABLE geo.synthetic_incident_points IS 'Synthetic incident locations as points (NOT real emergencies)';
COMMENT ON TABLE economia.digital_access_alcaldia IS 'Digital access index by alcaldía (SYNTHETIC data for equity analysis)';

COMMENT ON COLUMN geo.alcaldias_geom.geom IS 'MultiPolygon geometry in SRID 4326 (WGS84)';
COMMENT ON COLUMN geo.synthetic_incident_points.geom IS 'Point geometry in SRID 4326 (WGS84)';
COMMENT ON COLUMN geo.synthetic_incident_points.alcaldia_joined IS 'Alcaldía assigned via ST_Contains spatial join';

-- ============================================================================
-- Completion Message
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ PostGIS schema setup complete';
    RAISE NOTICE '   - Extension: postgis';
    RAISE NOTICE '   - Schemas: geo, economia';
    RAISE NOTICE '   - Tables: alcaldias_geom, synthetic_incident_points, digital_access_alcaldia';
    RAISE NOTICE '   - Indexes: GIST spatial indexes created';
    RAISE NOTICE '   - Views: validation_summary, spatial_join_validation';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  REMINDER: All data is SYNTHETIC for demo purposes only';
END $$;

-- Made with Bob
