#!/usr/bin/env python3
"""
Generate Judge Metrics from PostGIS Data for 911 AI Flow Demo

Purpose:
- Calculate territorial equity metrics using PostGIS spatial data
- Generate metrics for hackathon judges
- Demonstrate geospatial analysis capabilities

Metrics Calculated:
- Gini coefficient (territorial equity)
- P0 detection recall rate (critical signal detection)
- Coverage bias correlation (digital access vs incident distribution)
- Operator hours freed (automation efficiency)
- Per-alcaldía statistics

DISCLAIMER: All data is SYNTHETIC for educational purposes only
- NO real geographic boundaries
- NO real emergency incidents
- Metrics are demonstrative, not production-grade

Author: 911 AI Flow Demo Team
License: Educational Use Only
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import numpy as np

def to_json_safe(obj):
    """Convert numpy/scientific Python types into JSON-safe native Python types."""
    try:
        import numpy as np
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
    except Exception:
        pass

    if isinstance(obj, dict):
        return {str(k): to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_json_safe(v) for v in obj]
    if isinstance(obj, tuple):
        return [to_json_safe(v) for v in obj]
    return obj



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
CONSTANTS_FILE = BASE_DIR / "data/economia/constants.json"
OUTPUT_FILE = BASE_DIR / "evidence/judge_metrics/judge_metrics_postgis.json"


def connect_db():
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)


def load_constants():
    """Load thresholds from constants.json."""
    if not CONSTANTS_FILE.exists():
        print(f"❌ Constants file not found: {CONSTANTS_FILE}")
        sys.exit(1)
    
    with open(CONSTANTS_FILE, "r") as f:
        data = json.load(f)
    
    return data.get("thresholds", {})


def calculate_gini(values):
    """
    Calculate Gini coefficient for territorial equity.
    
    Args:
        values: List of numeric values (e.g., risk load per alcaldía)
    
    Returns:
        float: Gini coefficient (0 = perfect equality, 1 = perfect inequality)
    """
    if not values or len(values) == 0:
        return 0.0
    
    # Sort values
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    # Calculate Gini
    cumsum = np.cumsum(sorted_values)
    gini = (2 * np.sum((np.arange(1, n + 1)) * sorted_values)) / (n * np.sum(sorted_values)) - (n + 1) / n
    
    return round(gini, 4)


def calculate_pearson_correlation(x, y):
    """
    Calculate Pearson correlation coefficient.
    
    Args:
        x: List of numeric values
        y: List of numeric values
    
    Returns:
        float: Correlation coefficient (-1 to 1)
    """
    if len(x) != len(y) or len(x) == 0:
        return 0.0
    
    x_arr = np.array(x)
    y_arr = np.array(y)
    
    correlation = np.corrcoef(x_arr, y_arr)[0, 1]
    
    return round(correlation, 4)


def get_alcaldia_stats(conn):
    """Get incident statistics by alcaldía."""
    print("📊 Calculating alcaldía statistics...")
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                a.alcaldia,
                a.alcaldia_norm,
                COUNT(p.id) AS incident_count,
                COALESCE(AVG(p.risk_level), 0) AS avg_risk,
                COUNT(CASE WHEN p.p0_signals IS NOT NULL AND p.p0_signals != '' THEN 1 END) AS p0_count,
                d.digital_access_index,
                d.percentile
            FROM geo.alcaldias_geom a
            LEFT JOIN geo.synthetic_incident_points p ON p.alcaldia_joined = a.alcaldia_norm
            LEFT JOIN economia.digital_access_alcaldia d ON d.alcaldia_norm = a.alcaldia_norm
            GROUP BY a.alcaldia, a.alcaldia_norm, d.digital_access_index, d.percentile
            ORDER BY a.alcaldia_norm
        """)
        
        results = cur.fetchall()
    
    # Convert to list of dicts
    stats = []
    for row in results:
        stats.append({
            "alcaldia": row["alcaldia"],
            "alcaldia_norm": row["alcaldia_norm"],
            "incident_count": int(row["incident_count"]),
            "avg_risk": round(float(row["avg_risk"]), 2),
            "p0_count": int(row["p0_count"]),
            "digital_access_index": float(row["digital_access_index"]) if row["digital_access_index"] else 0.0,
            "percentile": int(row["percentile"]) if row["percentile"] else 0
        })
    
    print(f"   ✅ Calculated stats for {len(stats)} alcaldías")
    return stats


def calculate_gini_risk_norm(alcaldia_stats):
    """Calculate Gini coefficient for risk distribution."""
    print("📈 Calculating Gini coefficient (territorial equity)...")
    
    # Calculate risk load per alcaldía (incident_count * avg_risk)
    risk_loads = [s["incident_count"] * s["avg_risk"] for s in alcaldia_stats]
    
    gini = calculate_gini(risk_loads)
    
    print(f"   ✅ Gini coefficient: {gini}")
    return gini


def calculate_recall_p0(conn):
    """Calculate P0 detection recall rate."""
    print("🚨 Calculating P0 detection recall rate...")
    
    with conn.cursor() as cur:
        # Count critical incidents
        cur.execute("""
            SELECT COUNT(*) AS total_critical
            FROM geo.synthetic_incident_points
            WHERE branch = 'critical'
        """)
        total_critical = cur.fetchone()["total_critical"]
        
        # Count critical incidents with P0 signals
        cur.execute("""
            SELECT COUNT(*) AS critical_with_p0
            FROM geo.synthetic_incident_points
            WHERE branch = 'critical' 
            AND p0_signals IS NOT NULL 
            AND p0_signals != ''
        """)
        critical_with_p0 = cur.fetchone()["critical_with_p0"]
    
    if total_critical == 0:
        recall = 0.0
    else:
        recall = critical_with_p0 / total_critical
    
    print(f"   ✅ P0 recall: {recall:.4f} ({critical_with_p0}/{total_critical})")
    print(f"   ℹ️  NOTE: This is a synthetic metric for demo purposes")
    print(f"   ℹ️  In production, recall would be measured against ground truth")
    
    return round(recall, 4)


def calculate_coverage_bias_correlation(alcaldia_stats):
    """Calculate correlation between digital access and incident count."""
    print("🔗 Calculating coverage bias correlation...")
    
    digital_access = [s["digital_access_index"] for s in alcaldia_stats]
    incident_counts = [s["incident_count"] for s in alcaldia_stats]
    
    correlation = calculate_pearson_correlation(digital_access, incident_counts)
    
    print(f"   ✅ Correlation: {correlation}")
    print(f"   ℹ️  Positive correlation suggests coverage bias")
    print(f"   ℹ️  (More digital access → More reported incidents)")
    
    return correlation


def calculate_operator_hours_freed(conn, thresholds):
    """Calculate operator hours freed per day."""
    print("⏱️  Calculating operator hours freed...")
    
    with conn.cursor() as cur:
        # Count low-risk incidents without human required
        cur.execute("""
            SELECT COUNT(*) AS low_automated
            FROM geo.synthetic_incident_points
            WHERE branch = 'low' AND human_required = false
        """)
        low_automated = cur.fetchone()["low_automated"]
    
    # Calculate hours freed
    min_per_call = thresholds.get("min_por_llamada_falsa_high", 8)
    hours_freed = (low_automated * min_per_call) / 60
    
    print(f"   ✅ Hours freed: {hours_freed:.2f} hours/day")
    print(f"   ℹ️  Based on {low_automated} automated low-risk calls")
    print(f"   ℹ️  Assuming {min_per_call} minutes per call")
    
    return round(hours_freed, 2)


def generate_metrics():
    """Main function to generate all metrics."""
    print("=" * 70)
    print("911 AI Flow Demo - Judge Metrics Generator (PostGIS)")
    print("=" * 70)
    print()
    print("⚠️  DISCLAIMER: Using SYNTHETIC demo data")
    print("   - NO real geographic boundaries")
    print("   - NO real emergency incidents")
    print("   - Metrics are demonstrative only")
    print()
    
    # Load thresholds
    print("📋 Loading thresholds...")
    thresholds = load_constants()
    print(f"   ✅ Loaded {len(thresholds)} thresholds")
    print()
    
    # Connect to database
    print(f"🔌 Connecting to database: {DB_CONFIG['database']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
    conn = connect_db()
    print("✅ Connected successfully")
    print()
    
    try:
        # Get alcaldía statistics
        alcaldia_stats = get_alcaldia_stats(conn)
        print()
        
        # Calculate metrics
        gini = calculate_gini_risk_norm(alcaldia_stats)
        print()
        
        recall_p0 = calculate_recall_p0(conn)
        print()
        
        correlation = calculate_coverage_bias_correlation(alcaldia_stats)
        print()
        
        hours_freed = calculate_operator_hours_freed(conn, thresholds)
        print()
        
        # Build output JSON
        output = {
            "status": "generated",
            "synthetic_data": True,
            "disclaimer": "Datos geoespaciales sintéticos para demo. No representan límites oficiales ni incidentes reales.",
            "generated_at": datetime.now().isoformat(),
            "thresholds": thresholds,
            "metrics": {
                "gini_risk_norm": {
                    "value": gini,
                    "threshold": thresholds.get("gini_umbral_exito", 0.35),
                    "pass": gini <= thresholds.get("gini_umbral_exito", 0.35),
                    "description": "Gini coefficient for territorial equity (lower is better)"
                },
                "recall_p0_detection_rate": {
                    "value": recall_p0,
                    "threshold": thresholds.get("recall_p0_umbral", 0.95),
                    "pass": recall_p0 >= thresholds.get("recall_p0_umbral", 0.95),
                    "description": "P0 signal detection rate in critical incidents (synthetic metric)"
                },
                "operator_hours_freed_per_day": {
                    "value": hours_freed,
                    "threshold": thresholds.get("operator_hours_freed_threshold", 2.0),
                    "pass": hours_freed >= thresholds.get("operator_hours_freed_threshold", 2.0),
                    "description": "Operator hours freed per day through automation"
                },
                "coverage_bias_correlation_after": {
                    "value": correlation,
                    "threshold": thresholds.get("corr_digital_umbral", 0.20),
                    "pass": abs(correlation) <= thresholds.get("corr_digital_umbral", 0.20),
                    "description": "Correlation between digital access and incident count (lower is better)"
                }
            },
            "by_alcaldia": alcaldia_stats
        }
        
        # Create output directory
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON
        with open(OUTPUT_FILE, "w") as f:
            json.dump(to_json_safe(output), f, indent=2, ensure_ascii=False)
        
        print("=" * 70)
        print("📊 METRICS SUMMARY")
        print("=" * 70)
        print()
        print(f"✅ Gini coefficient: {gini} (threshold: {thresholds.get('gini_umbral_exito', 0.35)}) - {'PASS' if output['metrics']['gini_risk_norm']['pass'] else 'FAIL'}")
        print(f"✅ P0 recall rate: {recall_p0} (threshold: {thresholds.get('recall_p0_umbral', 0.95)}) - {'PASS' if output['metrics']['recall_p0_detection_rate']['pass'] else 'FAIL'}")
        print(f"✅ Hours freed/day: {hours_freed} (threshold: {thresholds.get('operator_hours_freed_threshold', 2.0)}) - {'PASS' if output['metrics']['operator_hours_freed_per_day']['pass'] else 'FAIL'}")
        print(f"✅ Coverage bias: {correlation} (threshold: {thresholds.get('corr_digital_umbral', 0.20)}) - {'PASS' if output['metrics']['coverage_bias_correlation_after']['pass'] else 'FAIL'}")
        print()
        print(f"💾 Saved to: {OUTPUT_FILE}")
        print(f"   - File size: {OUTPUT_FILE.stat().st_size:,} bytes")
        print()
        print("✅ Judge metrics generation complete!")
        print()
        print("🎯 Next steps:")
        print("   1. Validate: ./scripts/09_test_postgis_metrics.sh")
        print("   2. View metrics: curl http://localhost:8010/judge/metrics/postgis | jq")
        print("   3. View GeoJSON: curl http://localhost:8010/judge/geo/alcaldias | jq")
        print()
        
        return 0
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        conn.close()
        print("🔌 Database connection closed")


if __name__ == "__main__":
    sys.exit(generate_metrics())

# Made with Bob
