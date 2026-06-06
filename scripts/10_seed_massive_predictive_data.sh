#!/bin/bash
set -euo pipefail

echo "=========================================="
echo "Seeding Massive Predictive Data"
echo "=========================================="

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

DATA_FILE="data/demo/massive_predictive_data.json"
TARGET_MIN=5000

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ ! -f ".env" ]; then
  echo -e "${RED}✗ .env file not found${NC}"
  exit 1
fi

DB_USER=$(grep '^POSTGRES_USER=' .env | cut -d= -f2-)
DB_NAME=$(grep '^POSTGRES_DB=' .env | cut -d= -f2-)
DB_PASS=$(grep '^POSTGRES_PASSWORD=' .env | cut -d= -f2-)
DB_HOST="localhost"
DB_PORT="5432"

echo -e "${YELLOW}Step 1: Generating massive synthetic data...${NC}"
mkdir -p data/demo

# Pedimos más de 5000 porque el generador actual produce menos por su lógica probabilística.
python3 tools/generate_massive_demo_data.py 7000 30 "$DATA_FILE"

if [ ! -f "$DATA_FILE" ]; then
  echo -e "${RED}✗ Failed to generate data file${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Data file generated${NC}"

echo -e "${YELLOW}Step 2: Ensuring minimum ${TARGET_MIN} records...${NC}"

python3 - <<PY
import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta

path = Path("$DATA_FILE")
data = json.loads(path.read_text())

if not isinstance(data, list):
    raise SystemExit("Expected JSON list")

original_len = len(data)
print(f"Original generated records: {original_len}")

if original_len == 0:
    raise SystemExit("Generated data is empty")

target = int("$TARGET_MIN")
i = 0
while len(data) < target:
    base = dict(data[i % original_len])
    base["incident_id"] = f"PRED-FILLER-{uuid.uuid4().hex[:12].upper()}"

    try:
        dt = datetime.fromisoformat(str(base["created_at"]).replace("Z", ""))
    except Exception:
        dt = datetime.utcnow()

    base["created_at"] = (dt + timedelta(seconds=i + 1)).isoformat()
    data.append(base)
    i += 1

path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
print(f"Final records: {len(data)}")
PY

echo -e "${YELLOW}Step 3: Loading data into PostgreSQL/PostGIS...${NC}"

python3 - <<PY
import json
import psycopg2
from psycopg2.extras import execute_batch
from pathlib import Path

db = {
    "host": "$DB_HOST",
    "port": int("$DB_PORT"),
    "dbname": "$DB_NAME",
    "user": "$DB_USER",
    "password": "$DB_PASS",
}

data_file = Path("$DATA_FILE")
incidents = json.loads(data_file.read_text())

print(f"Loading {len(incidents)} predictive incidents...")

conn = psycopg2.connect(**db)
cur = conn.cursor()

schema_sql = """
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.predictive_incidents (
    id SERIAL PRIMARY KEY,
    incident_id TEXT NOT NULL UNIQUE,
    branch VARCHAR(20) NOT NULL CHECK (branch IN ('low', 'mid', 'critical')),
    risk_level INTEGER NOT NULL CHECK (risk_level >= 1 AND risk_level <= 10),
    case_category VARCHAR(50) NOT NULL,
    human_required BOOLEAN DEFAULT false,
    p0_signals TEXT[],
    alcaldia_norm VARCHAR(50),
    synthetic BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    geom geometry(Point, 4326)
);

CREATE INDEX IF NOT EXISTS idx_predictive_incident_id ON analytics.predictive_incidents(incident_id);
CREATE INDEX IF NOT EXISTS idx_predictive_created_at ON analytics.predictive_incidents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictive_branch ON analytics.predictive_incidents(branch);
CREATE INDEX IF NOT EXISTS idx_predictive_risk_level ON analytics.predictive_incidents(risk_level);
CREATE INDEX IF NOT EXISTS idx_predictive_category ON analytics.predictive_incidents(case_category);
CREATE INDEX IF NOT EXISTS idx_predictive_alcaldia ON analytics.predictive_incidents(alcaldia_norm);
CREATE INDEX IF NOT EXISTS idx_predictive_human_required ON analytics.predictive_incidents(human_required);
CREATE INDEX IF NOT EXISTS idx_predictive_synthetic ON analytics.predictive_incidents(synthetic);
CREATE INDEX IF NOT EXISTS idx_predictive_geom ON analytics.predictive_incidents USING GIST(geom);

CREATE OR REPLACE FUNCTION analytics.notify_predictive_change()
RETURNS trigger AS \$\$
DECLARE
    payload JSON;
BEGIN
    IF TG_OP = 'DELETE' THEN
        payload = json_build_object(
            'operation', TG_OP,
            'table', TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME,
            'incident_id', OLD.incident_id,
            'created_at', now()
        );
    ELSE
        payload = json_build_object(
            'operation', TG_OP,
            'table', TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME,
            'incident_id', NEW.incident_id,
            'branch', NEW.branch,
            'risk_level', NEW.risk_level,
            'case_category', NEW.case_category,
            'alcaldia_norm', NEW.alcaldia_norm,
            'created_at', NEW.created_at
        );
    END IF;

    PERFORM pg_notify('predictive_updates', payload::text);
    RETURN COALESCE(NEW, OLD);
END;
\$\$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS notify_predictive_insert ON analytics.predictive_incidents;
DROP TRIGGER IF EXISTS notify_predictive_update ON analytics.predictive_incidents;
DROP TRIGGER IF EXISTS notify_predictive_delete ON analytics.predictive_incidents;

CREATE TRIGGER notify_predictive_insert
AFTER INSERT ON analytics.predictive_incidents
FOR EACH ROW EXECUTE FUNCTION analytics.notify_predictive_change();

CREATE TRIGGER notify_predictive_update
AFTER UPDATE ON analytics.predictive_incidents
FOR EACH ROW EXECUTE FUNCTION analytics.notify_predictive_change();

CREATE TRIGGER notify_predictive_delete
AFTER DELETE ON analytics.predictive_incidents
FOR EACH ROW EXECUTE FUNCTION analytics.notify_predictive_change();
"""

cur.execute(schema_sql)

# Solo limpia datos sintéticos predictivos. No toca raw/core/analytics.incidents/geo/economia.
cur.execute("DELETE FROM analytics.predictive_incidents WHERE synthetic = true;")

insert_sql = """
INSERT INTO analytics.predictive_incidents
(incident_id, branch, risk_level, case_category, human_required, p0_signals,
 alcaldia_norm, synthetic, created_at, geom)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
        ST_SetSRID(ST_MakePoint(%s, %s), 4326))
ON CONFLICT (incident_id) DO NOTHING;
"""

rows = []
for inc in incidents:
    rows.append((
        inc["incident_id"],
        inc["branch"],
        int(inc["risk_level"]),
        inc["case_category"],
        bool(inc["human_required"]),
        inc.get("p0_signals") or [],
        inc.get("alcaldia_norm"),
        bool(inc.get("synthetic", True)),
        inc["created_at"],
        float(inc["longitude"]),
        float(inc["latitude"]),
    ))

execute_batch(cur, insert_sql, rows, page_size=500)
conn.commit()

cur.execute("""
SELECT
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE synthetic = true) AS synthetic_total,
  COUNT(*) FILTER (WHERE branch = 'critical') AS critical_total,
  COUNT(*) FILTER (WHERE human_required = true) AS human_required_total,
  COUNT(*) FILTER (WHERE p0_signals IS NOT NULL AND array_length(p0_signals, 1) > 0) AS p0_total
FROM analytics.predictive_incidents;
""")
stats = cur.fetchone()

print("\\n=== Database Statistics ===")
print(f"Total incidents: {stats[0]}")
print(f"Synthetic incidents: {stats[1]}")
print(f"Critical incidents: {stats[2]}")
print(f"Human required: {stats[3]}")
print(f"P0 signals: {stats[4]}")

if stats[0] < int("$TARGET_MIN"):
    raise SystemExit(f"Expected at least {int('$TARGET_MIN')} records, got {stats[0]}")

cur.close()
conn.close()
print("\\n✓ Massive predictive data loaded successfully")
PY

echo ""
echo -e "${GREEN}=========================================="
echo -e "✓ Massive Predictive Data Seeded"
echo -e "==========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Test: curl http://localhost:8010/predictive/overview | jq"
echo "  2. Open: http://127.0.0.1:5173/predictivo"
echo ""
