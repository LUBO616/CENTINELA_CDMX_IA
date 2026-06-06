#!/usr/bin/env python3
"""
Generate massive synthetic predictive data for CENTINELA_CDMX_IA
Generates 5000+ incidents distributed across time, alcaldías, and categories
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid

# Alcaldías CDMX
ALCALDIAS = [
    "alvaro_obregon", "azcapotzalco", "benito_juarez", "coyoacan",
    "cuajimalpa", "cuauhtemoc", "gustavo_a_madero", "iztapalapa",
    "iztapalapa", "magdalena_contreras", "miguel_hidalgo", "milpa_alta",
    "tlahuac", "tlalpan", "venustiano_carranza", "xochimilco"
]

# Categories and their weights
CATEGORIES = {
    "security": 0.25,
    "medical": 0.20,
    "protection_civil": 0.15,
    "public_services": 0.20,
    "social_support": 0.10,
    "victim_attention": 0.08,
    "unknown": 0.02
}

# Branch distribution
BRANCHES = {
    "low": 0.50,
    "mid": 0.35,
    "critical": 0.15
}

# P0 signals by category
P0_SIGNALS = {
    "security": ["arma de fuego", "secuestro", "amenaza de muerte", "disparos"],
    "medical": ["sangrado grave", "inconsciente", "no respira", "infarto"],
    "protection_civil": ["incendio", "explosión", "derrumbe", "fuga de gas"],
    "victim_attention": ["violencia familiar grave", "abuso infantil", "agresión sexual"],
    "social_support": ["bebé abandonado", "niño extraviado", "adulto mayor en riesgo"]
}

# Hourly patterns (more incidents during day, less at night)
HOURLY_WEIGHTS = {
    0: 0.3, 1: 0.2, 2: 0.2, 3: 0.2, 4: 0.3, 5: 0.5,
    6: 0.8, 7: 1.2, 8: 1.5, 9: 1.4, 10: 1.3, 11: 1.2,
    12: 1.3, 13: 1.2, 14: 1.1, 15: 1.2, 16: 1.3, 17: 1.4,
    18: 1.5, 19: 1.4, 20: 1.2, 21: 1.0, 22: 0.8, 23: 0.5
}

# Synthetic coordinates by alcaldía (approximate centers)
ALCALDIA_COORDS = {
    "alvaro_obregon": (-99.2044, 19.3467),
    "azcapotzalco": (-99.1860, 19.4900),
    "benito_juarez": (-99.1587, 19.3700),
    "coyoacan": (-99.1620, 19.3467),
    "cuajimalpa": (-99.2917, 19.3550),
    "cuauhtemoc": (-99.1333, 19.4333),
    "gustavo_a_madero": (-99.1133, 19.4850),
    "iztapalapa": (-99.0733, 19.3550),
    "iztapalapa": (-99.0733, 19.3550),
    "magdalena_contreras": (-99.2650, 19.2850),
    "miguel_hidalgo": (-99.2017, 19.4267),
    "milpa_alta": (-99.0233, 19.1917),
    "tlahuac": (-99.0133, 19.2867),
    "tlalpan": (-99.1667, 19.2900),
    "venustiano_carranza": (-99.1000, 19.4333),
    "xochimilco": (-99.1050, 19.2550)
}


def weighted_choice(choices: Dict[str, float]) -> str:
    """Select item based on weights"""
    items = list(choices.keys())
    weights = list(choices.values())
    return random.choices(items, weights=weights, k=1)[0]


def generate_risk_level(branch: str) -> int:
    """Generate risk level based on branch"""
    if branch == "low":
        return random.randint(1, 3)
    elif branch == "mid":
        return random.randint(4, 6)
    else:  # critical
        return random.randint(7, 10)


def generate_p0_signals(category: str, branch: str) -> List[str]:
    """Generate P0 signals for critical cases"""
    if branch != "critical":
        return []
    
    if category in P0_SIGNALS:
        # 70% chance of P0 signal in critical cases
        if random.random() < 0.7:
            num_signals = random.randint(1, 2)
            return random.sample(P0_SIGNALS[category], min(num_signals, len(P0_SIGNALS[category])))
    
    return []


def generate_human_required(branch: str, risk_level: int) -> bool:
    """Determine if human review is required"""
    if branch == "critical":
        return True
    elif branch == "mid":
        return True
    else:  # low
        # Some low cases still need human review
        return risk_level >= 3 or random.random() < 0.1


def add_coordinate_noise(base_coord: tuple, noise_km: float = 2.0) -> tuple:
    """Add random noise to coordinates (approximate km to degrees)"""
    # Rough conversion: 1 degree ≈ 111 km
    noise_deg = noise_km / 111.0
    lon = base_coord[0] + random.uniform(-noise_deg, noise_deg)
    lat = base_coord[1] + random.uniform(-noise_deg, noise_deg)
    return (lon, lat)


def generate_incident(base_time: datetime, hour_offset: int) -> Dict[str, Any]:
    """Generate a single synthetic incident"""
    # Select category and branch
    category = weighted_choice(CATEGORIES)
    branch = weighted_choice(BRANCHES)
    
    # Generate attributes
    risk_level = generate_risk_level(branch)
    p0_signals = generate_p0_signals(category, branch)
    human_required = generate_human_required(branch, risk_level)
    
    # Select alcaldía
    alcaldia = random.choice(ALCALDIAS)
    
    # Generate timestamp with hourly pattern
    hour = hour_offset % 24
    created_at = base_time + timedelta(hours=hour_offset, minutes=random.randint(0, 59))
    
    # Generate coordinates
    base_coords = ALCALDIA_COORDS[alcaldia]
    coords = add_coordinate_noise(base_coords)
    
    # Generate unique incident ID
    incident_id = f"PRED-{uuid.uuid4().hex[:12].upper()}"
    
    return {
        "incident_id": incident_id,
        "branch": branch,
        "risk_level": risk_level,
        "case_category": category,
        "human_required": human_required,
        "p0_signals": p0_signals,
        "alcaldia_norm": alcaldia,
        "synthetic": True,
        "created_at": created_at.isoformat(),
        "longitude": coords[0],
        "latitude": coords[1]
    }


def generate_massive_data(num_incidents: int = 5000, days_back: int = 30) -> List[Dict[str, Any]]:
    """Generate massive synthetic dataset"""
    print(f"Generating {num_incidents} synthetic incidents over {days_back} days...")
    
    incidents = []
    base_time = datetime.now() - timedelta(days=days_back)
    
    # Calculate total hours
    total_hours = days_back * 24
    
    # Generate incidents distributed across hours
    for i in range(num_incidents):
        # Select hour with weighted distribution
        hour_offset = random.randint(0, total_hours - 1)
        hour_of_day = hour_offset % 24
        
        # Apply hourly weight (more incidents during peak hours)
        if random.random() < HOURLY_WEIGHTS[hour_of_day]:
            incident = generate_incident(base_time, hour_offset)
            incidents.append(incident)
        else:
            # Retry to maintain count
            i -= 1
    
    print(f"Generated {len(incidents)} incidents")
    
    # Print statistics
    print("\n=== Statistics ===")
    print(f"Total incidents: {len(incidents)}")
    
    # By branch
    branch_counts = {}
    for inc in incidents:
        branch_counts[inc["branch"]] = branch_counts.get(inc["branch"], 0) + 1
    print(f"\nBy branch:")
    for branch, count in sorted(branch_counts.items()):
        print(f"  {branch}: {count} ({count/len(incidents)*100:.1f}%)")
    
    # By category
    category_counts = {}
    for inc in incidents:
        category_counts[inc["case_category"]] = category_counts.get(inc["case_category"], 0) + 1
    print(f"\nBy category:")
    for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count} ({count/len(incidents)*100:.1f}%)")
    
    # Critical stats
    critical_count = sum(1 for inc in incidents if inc["branch"] == "critical")
    human_required_count = sum(1 for inc in incidents if inc["human_required"])
    p0_count = sum(1 for inc in incidents if inc["p0_signals"])
    
    print(f"\nCritical incidents: {critical_count}")
    print(f"Human required: {human_required_count}")
    print(f"P0 signals: {p0_count}")
    
    return incidents


def main():
    """Main execution"""
    import sys
    
    # Parse arguments
    num_incidents = 5000
    days_back = 30
    output_file = "data/demo/massive_predictive_data.json"
    
    if len(sys.argv) > 1:
        num_incidents = int(sys.argv[1])
    if len(sys.argv) > 2:
        days_back = int(sys.argv[2])
    if len(sys.argv) > 3:
        output_file = sys.argv[3]
    
    # Generate data
    incidents = generate_massive_data(num_incidents, days_back)
    
    # Save to file
    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(incidents, f, indent=2)
    
    print(f"\n✓ Data saved to {output_file}")
    print(f"✓ Ready to load into analytics.predictive_incidents table")


if __name__ == "__main__":
    main()

# Made with Bob
