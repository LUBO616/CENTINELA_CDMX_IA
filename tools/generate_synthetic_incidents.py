#!/usr/bin/env python3
"""
Generate Synthetic Geocoded Incidents for 911 AI Flow Demo

DISCLAIMER:
This script generates SYNTHETIC demo data for educational purposes only.
These are NOT real emergency incidents. All data is fabricated for demonstration
of territorial equity metrics and geospatial analysis capabilities.

NO PII. NO real addresses. NO real emergency data.

Purpose:
- Generate minimum 160 synthetic incidents
- Distribute across 16 CDMX alcaldías
- Mix of low/mid/critical risk levels
- Include P0 signals for critical cases
- Lat/lon coordinates within synthetic polygon boundaries
- Output CSV for PostGIS loading

Author: 911 AI Flow Demo Team
License: Educational Use Only
"""

import json
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
import uuid

# Alcaldías with approximate center coordinates (matching generate_synthetic_geo.py)
ALCALDIAS = [
    {"name": "Álvaro Obregón", "norm": "alvaro_obregon", "lat": 19.3600, "lon": -99.2000},
    {"name": "Azcapotzalco", "norm": "azcapotzalco", "lat": 19.4900, "lon": -99.1800},
    {"name": "Benito Juárez", "norm": "benito_juarez", "lat": 19.3700, "lon": -99.1600},
    {"name": "Coyoacán", "norm": "coyoacan", "lat": 19.3500, "lon": -99.1400},
    {"name": "Cuajimalpa", "norm": "cuajimalpa", "lat": 19.3600, "lon": -99.3000},
    {"name": "Cuauhtémoc", "norm": "cuauhtemoc", "lat": 19.4300, "lon": -99.1400},
    {"name": "Gustavo A. Madero", "norm": "gustavo_a_madero", "lat": 19.4900, "lon": -99.1100},
    {"name": "Iztacalco", "norm": "iztacalco", "lat": 19.3900, "lon": -99.0900},
    {"name": "Iztapalapa", "norm": "iztapalapa", "lat": 19.3500, "lon": -99.0500},
    {"name": "Magdalena Contreras", "norm": "magdalena_contreras", "lat": 19.3000, "lon": -99.2400},
    {"name": "Miguel Hidalgo", "norm": "miguel_hidalgo", "lat": 19.4300, "lon": -99.2000},
    {"name": "Milpa Alta", "norm": "milpa_alta", "lat": 19.1900, "lon": -99.0200},
    {"name": "Tláhuac", "norm": "tlahuac", "lat": 19.2900, "lon": -99.0100},
    {"name": "Tlalpan", "norm": "tlalpan", "lat": 19.2900, "lon": -99.1700},
    {"name": "Venustiano Carranza", "norm": "venustiano_carranza", "lat": 19.4300, "lon": -99.1000},
    {"name": "Xochimilco", "norm": "xochimilco", "lat": 19.2600, "lon": -99.1000},
]

# Case categories
CATEGORIES = [
    "security",
    "medical",
    "protection_civil",
    "public_services",
    "social_support",
    "victim_attention",
]

# P0 signals for critical cases
P0_SIGNALS = [
    "arma_fuego",
    "violencia_familiar",
    "sangrado_grave",
    "dificultad_respiratoria",
    "inconsciente",
    "violencia_sexual",
    "privacion_libertad",
    "incendio_activo",
]


def generate_random_point_in_square(center_lat, center_lon, size_degrees=0.05):
    """
    Generate random lat/lon within square polygon boundaries.
    
    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        size_degrees: Size of square (default 0.05 degrees ~5.5km)
    
    Returns:
        tuple: (lat, lon)
    """
    half_size = size_degrees / 2
    # Random offset within square boundaries
    lat_offset = random.uniform(-half_size * 0.9, half_size * 0.9)  # 90% to stay well inside
    lon_offset = random.uniform(-half_size * 0.9, half_size * 0.9)
    
    return (
        round(center_lat + lat_offset, 6),
        round(center_lon + lon_offset, 6)
    )


def generate_incident(alcaldia_info, incident_num, base_date):
    """
    Generate a single synthetic incident.
    
    Args:
        alcaldia_info: Dict with alcaldia name, norm, lat, lon
        incident_num: Sequential incident number
        base_date: Base datetime for timestamp
    
    Returns:
        dict: Incident data
    """
    # Determine risk level and branch
    rand = random.random()
    if rand < 0.5:  # 50% low risk
        risk_level = 1
        branch = "low"
        human_required = False
        p0_signals = ""
    elif rand < 0.75:  # 25% mid risk
        risk_level = 5
        branch = "mid"
        human_required = True
        p0_signals = ""
    else:  # 25% critical
        risk_level = random.choice([8, 9])
        branch = "critical"
        human_required = True
        # Critical cases have P0 signals
        num_signals = random.randint(1, 3)
        p0_signals = ",".join(random.sample(P0_SIGNALS, num_signals))
    
    # Generate random point within alcaldia boundaries
    lat, lon = generate_random_point_in_square(
        alcaldia_info["lat"],
        alcaldia_info["lon"]
    )
    
    # Generate timestamp (spread over last 30 days)
    time_offset = timedelta(
        days=random.randint(0, 29),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    created_at = (base_date - time_offset).isoformat()
    
    # Generate IDs
    incident_id = f"INC-{incident_num:06d}"
    call_id = str(uuid.uuid4())
    
    # Select category
    case_category = random.choice(CATEGORIES)
    
    return {
        "incident_id": incident_id,
        "call_id": call_id,
        "branch": branch,
        "risk_level": risk_level,
        "case_category": case_category,
        "human_required": human_required,
        "p0_signals": p0_signals,
        "alcaldia": alcaldia_info["norm"],
        "lat": lat,
        "lon": lon,
        "created_at": created_at,
    }


def main():
    """Generate synthetic incidents and save to CSV."""
    print("=" * 70)
    print("911 AI Flow Demo - Synthetic Incident Generator")
    print("=" * 70)
    print()
    print("⚠️  DISCLAIMER: Generating SYNTHETIC demo data")
    print("   These are NOT real emergency incidents")
    print("   All data is fabricated for educational purposes")
    print()
    
    # Configuration
    MIN_INCIDENTS = 160
    INCIDENTS_PER_ALCALDIA = 10  # Base amount, will add more to reach minimum
    
    # Calculate total incidents (ensure minimum)
    total_incidents = max(MIN_INCIDENTS, len(ALCALDIAS) * INCIDENTS_PER_ALCALDIA)
    
    print(f"📊 Configuration:")
    print(f"   - Alcaldías: {len(ALCALDIAS)}")
    print(f"   - Target incidents: {total_incidents}")
    print(f"   - Distribution: ~{total_incidents // len(ALCALDIAS)} per alcaldía")
    print()
    
    # Base date for timestamps
    base_date = datetime.now()
    
    # Generate incidents
    incidents = []
    incident_counter = 1
    
    # Distribute incidents across alcaldías
    incidents_per_alcaldia = total_incidents // len(ALCALDIAS)
    extra_incidents = total_incidents % len(ALCALDIAS)
    
    for idx, alcaldia in enumerate(ALCALDIAS):
        # Some alcaldías get one extra incident to reach total
        num_incidents = incidents_per_alcaldia + (1 if idx < extra_incidents else 0)
        
        print(f"🏙️  Generating {num_incidents} incidents for {alcaldia['name']}...")
        
        for _ in range(num_incidents):
            incident = generate_incident(alcaldia, incident_counter, base_date)
            incidents.append(incident)
            incident_counter += 1
    
    print()
    print(f"✅ Generated {len(incidents)} synthetic incidents")
    
    # Calculate statistics
    low_count = sum(1 for i in incidents if i["branch"] == "low")
    mid_count = sum(1 for i in incidents if i["branch"] == "mid")
    critical_count = sum(1 for i in incidents if i["branch"] == "critical")
    p0_count = sum(1 for i in incidents if i["p0_signals"])
    
    print()
    print("📈 Statistics:")
    print(f"   - Low risk (1): {low_count} ({low_count/len(incidents)*100:.1f}%)")
    print(f"   - Mid risk (5): {mid_count} ({mid_count/len(incidents)*100:.1f}%)")
    print(f"   - Critical (8-9): {critical_count} ({critical_count/len(incidents)*100:.1f}%)")
    print(f"   - With P0 signals: {p0_count}")
    print(f"   - Human required: {sum(1 for i in incidents if i['human_required'])}")
    print()
    
    # Create output directory
    output_dir = Path("data/demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write CSV
    output_file = output_dir / "incidentes_demo_geocoded.csv"
    
    fieldnames = [
        "incident_id",
        "call_id",
        "branch",
        "risk_level",
        "case_category",
        "human_required",
        "p0_signals",
        "alcaldia",
        "lat",
        "lon",
        "created_at",
    ]
    
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(incidents)
    
    print(f"💾 Saved to: {output_file}")
    print(f"   - File size: {output_file.stat().st_size:,} bytes")
    print(f"   - Rows: {len(incidents) + 1} (including header)")
    print()
    print("✅ Synthetic incident generation complete!")
    print()
    print("⚠️  REMEMBER: This is SYNTHETIC demo data")
    print("   - NO real emergency incidents")
    print("   - NO PII")
    print("   - For educational purposes only")
    print()


if __name__ == "__main__":
    main()

# Made with Bob
