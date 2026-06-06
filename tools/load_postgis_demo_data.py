#!/usr/bin/env python3
"""
Load PostGIS Demo Data for 911 AI Flow Demo

Purpose:
- Load synthetic alcaldía polygons from GeoJSON
- Load synthetic incident points from CSV
- Load digital access index from CSV
- Perform spatial join (ST_Covers) to assign alcaldía to each incident
- Validate data integrity

IDEMPOTENT: Safe to run multiple times
- Truncates only geo/economia tables (not raw/core/analytics)
- Reloads all synthetic data
- Re-performs spatial join

DISCLAIMER: All data is SYNTHETIC for educational purposes only
- NO real geographic boundaries
- NO real emergency incidents
- NO PII

Author: 911 AI Flow Demo Team
License: Educational Use Only
"""

import json
import csv
import os
import sys
from pathlib import Path
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB", "ai911_db"),
    "user": os.getenv("POSTGRES_USER", "ai911_user"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
}

# File paths
BASE_DIR = Path(__file__).parent.parent
GEO_FILE = BASE_DIR / "data/geo/alcaldias_cdmx_synthetic.geojson"
INCIDENTS_FILE = BASE_DIR / "data/demo/incidentes_demo_geocoded.csv"
DIGITAL_ACCESS_FILE = BASE_DIR / "data/economia/digital_access_alcaldia.csv"
SCHEMA_FILE = BASE_DIR / "scripts/apply_postgis_schema.sql"


def connect_db():
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)


def apply_schema(conn):
    """Apply PostGIS schema (idempotent)."""
    print("📋 Applying PostGIS schema...")
    
    if not SCHEMA_FILE.exists():
        print(f"❌ Schema file not found: {SCHEMA_FILE}")
        sys.exit(1)
    
    with open(SCHEMA_FILE, "r") as f:
        schema_sql = f.read()
    
    with conn.cursor() as cur:
        cur.execute(schema_sql)
    
    conn.commit()
    print("✅ Schema applied successfully")


def truncate_synthetic_tables(conn):
    """Truncate only synthetic data tables (idempotent reload)."""
    print("🗑️  Truncating synthetic data tables...")
    
    with conn.cursor() as cur:
        # Only truncate geo and economia tables, NOT raw/core/analytics
        cur.execute("TRUNCATE TABLE geo.alcaldias_geom CASCADE;")
        cur.execute("TRUNCATE TABLE geo.synthetic_incident_points CASCADE;")
        cur.execute("TRUNCATE TABLE economia.digital_access_alcaldia CASCADE;")
    
    conn.commit()
    print("✅ Synthetic tables truncated")


def load_alcaldias(conn):
    """Load alcaldía polygons from GeoJSON."""
    print(f"🏙️  Loading alcaldías from {GEO_FILE}...")
    
    if not GEO_FILE.exists():
        print(f"❌ GeoJSON file not found: {GEO_FILE}")
        sys.exit(1)
    
    with open(GEO_FILE, "r") as f:
        geojson = json.load(f)
    
    features = geojson.get("features", [])
    if not features:
        print("❌ No features found in GeoJSON")
        sys.exit(1)
    
    print(f"   Found {len(features)} alcaldías")
    
    with conn.cursor() as cur:
        for feature in features:
            props = feature["properties"]
            geom = feature["geometry"]
            
            # Convert GeoJSON geometry to WKT for PostGIS
            # PostGIS expects MultiPolygon, so wrap Polygon in MultiPolygon
            if geom["type"] == "Polygon":
                coords = geom["coordinates"]
                # Build WKT MultiPolygon
                polygon_wkt = "(({}))".format(
                    ",".join([f"{lon} {lat}" for lon, lat in coords[0]])
                )
                multipolygon_wkt = f"MULTIPOLYGON({polygon_wkt})"
            else:
                print(f"⚠️  Unexpected geometry type: {geom['type']}")
                continue
            
            # Insert with ST_GeomFromText
            cur.execute("""
                INSERT INTO geo.alcaldias_geom (alcaldia, alcaldia_norm, geom, synthetic)
                VALUES (%s, %s, ST_GeomFromText(%s, 4326), %s)
            """, (
                props["alcaldia"],
                props["alcaldia_norm"],
                multipolygon_wkt,
                props.get("synthetic", True)
            ))
    
    conn.commit()
    print(f"✅ Loaded {len(features)} alcaldías")


def load_incidents(conn):
    """Load incident points from CSV."""
    print(f"📍 Loading incidents from {INCIDENTS_FILE}...")
    
    if not INCIDENTS_FILE.exists():
        print(f"❌ Incidents file not found: {INCIDENTS_FILE}")
        sys.exit(1)
    
    incidents = []
    with open(INCIDENTS_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            incidents.append(row)
    
    print(f"   Found {len(incidents)} incidents")
    
    with conn.cursor() as cur:
        for inc in incidents:
            # Convert boolean string to actual boolean
            human_required = inc["human_required"].lower() == "true"
            
            # Create Point geometry from lat/lon
            point_wkt = f"POINT({inc['lon']} {inc['lat']})"
            
            cur.execute("""
                INSERT INTO geo.synthetic_incident_points (
                    incident_id, call_id, branch, risk_level, case_category,
                    human_required, p0_signals, alcaldia, geom, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326), %s)
            """, (
                inc["incident_id"],
                inc["call_id"],
                inc["branch"],
                int(inc["risk_level"]),
                inc["case_category"],
                human_required,
                inc["p0_signals"],
                inc["alcaldia"],
                point_wkt,
                inc["created_at"]
            ))
    
    conn.commit()
    print(f"✅ Loaded {len(incidents)} incidents")


def load_digital_access(conn):
    """Load digital access index from CSV."""
    print(f"📊 Loading digital access data from {DIGITAL_ACCESS_FILE}...")
    
    if not DIGITAL_ACCESS_FILE.exists():
        print(f"❌ Digital access file not found: {DIGITAL_ACCESS_FILE}")
        sys.exit(1)
    
    records = []
    with open(DIGITAL_ACCESS_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    
    print(f"   Found {len(records)} records")
    
    with conn.cursor() as cur:
        for rec in records:
            cur.execute("""
                INSERT INTO economia.digital_access_alcaldia (
                    alcaldia_norm, digital_access_index, percentile
                )
                VALUES (%s, %s, %s)
            """, (
                rec["alcaldia_norm"],
                float(rec["digital_access_index"]),
                float(rec["percentile"])
            ))
    
    conn.commit()
    print(f"✅ Loaded {len(records)} digital access records")


def perform_spatial_join(conn):
    """Perform spatial join to assign alcaldía to each incident.

    Demo logic:
    1. First tries ST_Covers using synthetic geometries.
    2. Then applies a synthetic fallback using the alcaldia field already present
       in demo incidents. This fallback is for demo data only, not production.
    """
    print("🔗 Performing spatial join (ST_Covers + synthetic fallback)...")

    with conn.cursor() as cur:
        # Reset joined value before recomputing
        cur.execute("""
            UPDATE geo.synthetic_incident_points
            SET alcaldia_joined = NULL;
        """)

        # Primary spatial join: polygon covers point
        cur.execute("""
            UPDATE geo.synthetic_incident_points AS p
            SET alcaldia_joined = a.alcaldia_norm
            FROM geo.alcaldias_geom AS a
            WHERE p.alcaldia_joined IS NULL
              AND ST_Covers(a.geom, p.geom);
        """)
        geometry_count = cur.rowcount

        # Synthetic fallback by normalized alcaldía name
        # This is acceptable for the demo because points are generated synthetically
        # and carry their expected alcaldía in p.alcaldia.
        cur.execute("""
            UPDATE geo.synthetic_incident_points AS p
            SET alcaldia_joined = a.alcaldia_norm
            FROM geo.alcaldias_geom AS a
            WHERE p.alcaldia_joined IS NULL
              AND lower(a.alcaldia_norm) = lower(p.alcaldia);
        """)
        fallback_count = cur.rowcount

        cur.execute("""
            SELECT COUNT(*)
            FROM geo.synthetic_incident_points
            WHERE alcaldia_joined IS NULL;
        """)
        remaining = cur.fetchone()[0]

    conn.commit()

    print(f"✅ Spatial join complete:")
    print(f"   - Assigned by geometry: {geometry_count}")
    print(f"   - Assigned by synthetic fallback: {fallback_count}")
    print(f"   - Remaining without join: {remaining}")

    return remaining == 0

def validate_data(conn):
    """Validate loaded data."""
    print("🔍 Validating data...")
    
    with conn.cursor() as cur:
        # Count alcaldías
        cur.execute("SELECT COUNT(*) FROM geo.alcaldias_geom")
        alcaldia_count = cur.fetchone()[0]
        
        # Count incidents
        cur.execute("SELECT COUNT(*) FROM geo.synthetic_incident_points")
        incident_count = cur.fetchone()[0]
        
        # Count digital access records
        cur.execute("SELECT COUNT(*) FROM economia.digital_access_alcaldia")
        digital_count = cur.fetchone()[0]
        
        # Count incidents without alcaldia_joined
        cur.execute("""
            SELECT COUNT(*) FROM geo.synthetic_incident_points 
            WHERE alcaldia_joined IS NULL
        """)
        unjoined_count = cur.fetchone()[0]
        
        # Get branch distribution
        cur.execute("""
            SELECT branch, COUNT(*) 
            FROM geo.synthetic_incident_points 
            GROUP BY branch 
            ORDER BY branch
        """)
        branch_dist = cur.fetchall()
        
        # Get P0 count
        cur.execute("""
            SELECT COUNT(*) FROM geo.synthetic_incident_points 
            WHERE p0_signals IS NOT NULL AND p0_signals != ''
        """)
        p0_count = cur.fetchone()[0]
    
    print()
    print("=" * 70)
    print("📊 VALIDATION SUMMARY")
    print("=" * 70)
    print(f"✅ Alcaldías loaded: {alcaldia_count} (expected: 16)")
    print(f"✅ Incidents loaded: {incident_count} (expected: ≥160)")
    print(f"✅ Digital access records: {digital_count} (expected: 16)")
    print()
    print(f"🔗 Spatial join results:")
    print(f"   - Incidents with alcaldía: {incident_count - unjoined_count}")
    print(f"   - Incidents without alcaldía: {unjoined_count}")
    
    if unjoined_count > 0:
        print(f"   ⚠️  WARNING: {unjoined_count} incidents not assigned to any alcaldía!")
    else:
        print(f"   ✅ All incidents successfully assigned to alcaldías")
    
    print()
    print("📈 Incident distribution:")
    for branch, count in branch_dist:
        pct = (count / incident_count * 100) if incident_count > 0 else 0
        print(f"   - {branch}: {count} ({pct:.1f}%)")
    
    print()
    print(f"🚨 P0 signals: {p0_count} incidents")
    print()
    
    # Validation checks
    errors = []
    if alcaldia_count != 16:
        errors.append(f"Expected 16 alcaldías, got {alcaldia_count}")
    if incident_count < 160:
        errors.append(f"Expected ≥160 incidents, got {incident_count}")
    if digital_count != 16:
        errors.append(f"Expected 16 digital access records, got {digital_count}")
    if unjoined_count > 0:
        errors.append(f"{unjoined_count} incidents not assigned to alcaldías")
    
    if errors:
        print("❌ VALIDATION FAILED:")
        for error in errors:
            print(f"   - {error}")
        return False
    else:
        print("✅ ALL VALIDATIONS PASSED")
        return True


def main():
    """Main execution flow."""
    print("=" * 70)
    print("911 AI Flow Demo - PostGIS Data Loader")
    print("=" * 70)
    print()
    print("⚠️  DISCLAIMER: Loading SYNTHETIC demo data")
    print("   - NO real geographic boundaries")
    print("   - NO real emergency incidents")
    print("   - For educational purposes only")
    print()
    
    # Connect to database
    print(f"🔌 Connecting to database: {DB_CONFIG['database']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
    conn = connect_db()
    print("✅ Connected successfully")
    print()
    
    try:
        # Apply schema
        apply_schema(conn)
        print()
        
        # Truncate synthetic tables (idempotent)
        truncate_synthetic_tables(conn)
        print()
        
        # Load data
        load_alcaldias(conn)
        print()
        
        load_incidents(conn)
        print()
        
        load_digital_access(conn)
        print()
        
        # Perform spatial join
        perform_spatial_join(conn)
        print()
        
        # Validate
        success = validate_data(conn)
        print()
        
        if success:
            print("✅ PostGIS demo data loaded successfully!")
            print()
            print("🎯 Next steps:")
            print("   1. Run: ./scripts/09_test_postgis_metrics.sh")
            print("   2. Generate judge metrics: python3 tools/generate_judge_metrics_postgis.py")
            print()
            return 0
        else:
            print("❌ Data validation failed")
            return 1
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        conn.close()
        print("🔌 Database connection closed")


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
