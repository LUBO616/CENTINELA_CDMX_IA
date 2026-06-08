# 911 AI Flow Demo - Detailed Implementation Plan

## Executive Summary

This document outlines the complete architecture and implementation plan for the "911 AI Flow Demo" MVP - an educational demonstration of an AI-assisted 911 emergency call flow system for Mexico City.

**Key Constraints:**
- Single Fedora 43 host with limited resources
- No VMs, Docker Compose only
- No real data, PII, or audio
- Simulated AI using deterministic rules
- Mexican legal compliance (LFPDPPP, NNA protection)
- Educational/demo purposes only

## System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph External
        Lovable[Lovable Dashboard]
        User[Demo User/Tester]
    end
    
    subgraph Docker Network
        N8N[n8n Orchestrator<br/>:5678]
        
        subgraph Services
            Ingest[api-ingest<br/>:8001]
            Triage[api-triage<br/>:8002]
            Analytics[api-analytics<br/>:8003]
        end
        
        subgraph Data Layer
            DB[(PostgreSQL<br/>:5432)]
        end
    end
    
    User -->|POST /webhook/911-call| N8N
    N8N -->|1. Save Raw| Ingest
    N8N -->|2. Analyze| Triage
    N8N -->|3. Store Result| Analytics
    N8N -->|Response| User
    
    Ingest --> DB
    Triage --> DB
    Analytics --> DB
    
    Lovable -->|GET /analytics/*| Analytics
    Lovable -->|GET /incidents| Analytics
```

### Data Flow Sequence

```mermaid
sequenceDiagram
    participant U as User/Lovable
    participant N as n8n Webhook
    participant I as api-ingest
    participant T as api-triage
    participant A as api-analytics
    participant D as PostgreSQL
    
    U->>N: POST /webhook/911-call<br/>{transcript, metadata}
    
    N->>I: POST /raw-conversations
    I->>I: Redact PII (regex + heuristics)
    I->>I: Generate trace_id
    I->>D: INSERT INTO raw.conversations
    I->>N: {call_id, trace_id, redacted_text}
    
    N->>T: POST /triage
    T->>T: Keyword analysis
    T->>T: P0 signal detection
    T->>T: Risk scoring (1-10)
    T->>T: Category classification
    T->>T: NNA detection
    T->>D: INSERT INTO core.triage_results
    T->>N: {risk_level, branch, category, flags}
    
    N->>A: POST /incidents
    A->>D: INSERT INTO analytics.incidents
    A->>D: UPDATE analytics.metrics
    A->>N: {incident_id, stored_at}
    
    N->>U: Consolidated Response
    
    U->>A: GET /analytics/summary
    A->>D: SELECT aggregated metrics
    A->>U: {totals, by_risk, by_category}
    
    U->>A: GET /analytics/predictions
    A->>D: SELECT historical data
    A->>A: Calculate mock predictions
    A->>U: {volume_forecast, category_dist, risk_zones}
```

## Database Schema Design

### Schema Organization

**PostgreSQL Database: `emergency_demo`**

Three schemas for data separation:
1. **raw** - Original redacted conversations
2. **core** - Processed triage results
3. **analytics** - Aggregated metrics and incidents

### Table Definitions

#### raw.conversations
```sql
CREATE TABLE raw.conversations (
    id SERIAL PRIMARY KEY,
    call_id UUID UNIQUE NOT NULL,
    trace_id UUID UNIQUE NOT NULL,
    original_text TEXT NOT NULL,
    redacted_text TEXT NOT NULL,
    redaction_flags JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_call_id (call_id),
    INDEX idx_trace_id (trace_id),
    INDEX idx_created_at (created_at)
);
```

#### core.triage_results
```sql
CREATE TABLE core.triage_results (
    id SERIAL PRIMARY KEY,
    call_id UUID REFERENCES raw.conversations(call_id),
    trace_id UUID NOT NULL,
    risk_level INTEGER CHECK (risk_level BETWEEN 1 AND 10),
    branch VARCHAR(20) CHECK (branch IN ('low', 'mid', 'critical')),
    priority_class VARCHAR(20) CHECK (priority_class IN ('minimum', 'low', 'medium', 'high', 'critical')),
    case_category VARCHAR(50),
    medical_category VARCHAR(50),
    protected_group_flags JSONB,
    best_interest_child BOOLEAN DEFAULT FALSE,
    human_required BOOLEAN DEFAULT FALSE,
    primary_authority VARCHAR(100),
    support_authorities TEXT[],
    public_stage_phrase TEXT,
    rationale_public TEXT,
    trust_flags JSONB,
    p0_signals TEXT[],
    keywords_detected JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_call_id (call_id),
    INDEX idx_risk_level (risk_level),
    INDEX idx_branch (branch),
    INDEX idx_category (case_category),
    INDEX idx_human_required (human_required)
);
```

#### analytics.incidents
```sql
CREATE TABLE analytics.incidents (
    id SERIAL PRIMARY KEY,
    incident_id UUID UNIQUE NOT NULL,
    call_id UUID REFERENCES raw.conversations(call_id),
    trace_id UUID NOT NULL,
    risk_level INTEGER,
    branch VARCHAR(20),
    case_category VARCHAR(50),
    human_required BOOLEAN,
    has_p0_signals BOOLEAN,
    location_hint TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_incident_id (incident_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_risk_level (risk_level),
    INDEX idx_category (case_category)
);
```

#### analytics.metrics_cache
```sql
CREATE TABLE analytics.metrics_cache (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50),
    metric_key VARCHAR(100),
    metric_value JSONB,
    calculated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_metric_type (metric_type),
    INDEX idx_calculated_at (calculated_at)
);
```

## Service Specifications

### 1. api-ingest (Port 8001)

**Purpose:** Receive raw conversations, redact PII, generate identifiers

**Technology Stack:**
- FastAPI
- Python 3.11+
- psycopg2 or SQLAlchemy
- Regex + heuristic redaction

**Endpoints:**

#### POST /raw-conversations
```json
Request:
{
  "transcript": "string",
  "metadata": {
    "source": "demo",
    "timestamp": "ISO8601"
  }
}

Response:
{
  "call_id": "uuid",
  "trace_id": "uuid",
  "redacted_text": "string",
  "redaction_summary": {
    "phones_redacted": 2,
    "emails_redacted": 1,
    "names_redacted": 3,
    "addresses_redacted": 1
  },
  "created_at": "ISO8601"
}
```

#### GET /raw-conversations?limit=50&offset=0
```json
Response:
{
  "total": 150,
  "items": [
    {
      "call_id": "uuid",
      "trace_id": "uuid",
      "redacted_text": "string",
      "created_at": "ISO8601"
    }
  ]
}
```

#### GET /health
```json
Response:
{
  "status": "healthy",
  "service": "api-ingest",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "ISO8601"
}
```

**Redaction Logic:**

1. **Phone Numbers (Regex):**
   - Pattern: `\d{10}` or `\d{3}[-.\s]?\d{3}[-.\s]?\d{4}`
   - Replace with: `[TELÉFONO-REDACTADO]`

2. **Email Addresses (Regex):**
   - Pattern: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`
   - Replace with: `[EMAIL-REDACTADO]`

3. **Names (Heuristic):**
   - Detect capitalized words after "me llamo", "soy", "mi nombre es"
   - Replace with: `[NOMBRE-REDACTADO]`

4. **Addresses (Heuristic):**
   - Detect patterns: "calle", "avenida", "colonia", "número"
   - Replace with: `[DIRECCIÓN-REDACTADA]`

### 2. api-triage (Port 8002)

**Purpose:** Analyze conversations, calculate risk, classify incidents

**Technology Stack:**
- FastAPI
- Python 3.11+
- Deterministic rule engine
- Keyword matrix system

**Endpoints:**

#### POST /triage
```json
Request:
{
  "transcript": "string",
  "call_id": "uuid",
  "consent": true,
  "location_hint": "string (optional)"
}

Response:
{
  "call_id": "uuid",
  "trace_id": "uuid",
  "risk_level": 8,
  "branch": "critical",
  "priority_class": "high",
  "case_category": "medical",
  "medical_category": "trauma",
  "protected_group_flags": {
    "nna_involved": true,
    "elderly": false,
    "disability": false,
    "gender_violence": false
  },
  "best_interest_child": true,
  "human_required": true,
  "primary_authority": "ERUM",
  "support_authorities": ["Cruz Roja", "Protección Civil"],
  "public_stage_phrase": "Unidad médica en camino",
  "rationale_public": "Lesión grave detectada, menor involucrado",
  "trust_flags": {
    "confidence_score": 0.85,
    "ambiguity_detected": false
  },
  "p0_signals": ["sangrado grave", "menor de edad"],
  "keywords_detected": {
    "medical": ["sangre", "herida", "dolor"],
    "nna": ["niño", "menor"]
  }
}
```

#### GET /health
```json
Response:
{
  "status": "healthy",
  "service": "api-triage",
  "version": "1.0.0",
  "rules_loaded": 150,
  "timestamp": "ISO8601"
}
```

**Risk Scoring Algorithm:**

```python
# Base score starts at 1
base_score = 1

# P0 Signal Detection (Critical)
p0_signals = [
    "arma", "pistola", "cuchillo", "navaja",
    "fuego", "incendio", "humo",
    "explosión", "bomba",
    "gas", "fuga de gas",
    "químico", "tóxico",
    "suicida", "suicidio", "matarme",
    "inconsciente", "desmayado",
    "no respira", "dificultad respirar", "ahogo",
    "sangrado", "sangre", "hemorragia",
    "secuestro", "privación libertad", "retenido",
    "desaparición", "desaparecido",
    "violación", "abuso sexual",
    "golpes", "violencia familiar",
    "mujer golpeada", "violencia mujer",
    "niño golpeado", "maltrato infantil",
    "adulto mayor maltrato",
    "discapacidad riesgo",
    "llamada silenciosa", "no puede hablar",
    "gritos", "llanto", "auxilio"
]

# If ANY P0 signal detected: risk_level >= 6
if any_p0_signal_detected:
    base_score = max(6, base_score)
    human_required = True

# Category-specific scoring
medical_keywords = ["dolor", "herida", "enfermo", "ambulancia"]
security_keywords = ["robo", "asalto", "delincuente"]
protection_keywords = ["inundación", "derrumbe", "árbol caído"]

# Accumulate score based on keyword density
score += count_medical_keywords * 0.5
score += count_security_keywords * 0.3
score += count_protection_keywords * 0.2

# NNA Detection (Always elevate)
nna_keywords = ["niño", "niña", "menor", "bebé", "adolescente"]
if any_nna_keyword:
    score += 2
    best_interest_child = True
    human_required = True

# Cap at 10
risk_level = min(10, int(score))

# Branch assignment
if risk_level <= 4:
    branch = "low"
elif risk_level == 5:
    branch = "mid"
else:
    branch = "critical"

# Priority class
priority_map = {
    1-2: "minimum",
    3-4: "low",
    5: "medium",
    6-7: "high",
    8-10: "critical"
}
```

**Category Classification:**

```python
categories = {
    "security": ["robo", "asalto", "violencia", "arma"],
    "medical": ["dolor", "herida", "sangre", "ambulancia", "enfermo"],
    "protection_civil": ["incendio", "inundación", "derrumbe", "gas"],
    "public_services": ["alumbrado", "bache", "agua", "basura"],
    "social_support": ["adicción", "depresión", "orientación"],
    "victim_attention": ["violación", "secuestro", "trata", "abuso"]
}

# Select category with highest keyword match
case_category = max_matching_category or "unknown"
```

### 3. api-analytics (Port 8003)

**Purpose:** Store incidents, calculate metrics, generate predictions

**Technology Stack:**
- FastAPI
- Python 3.11+
- PostgreSQL aggregations
- Mock prediction engine

**Endpoints:**

#### POST /incidents
```json
Request:
{
  "call_id": "uuid",
  "trace_id": "uuid",
  "risk_level": 8,
  "branch": "critical",
  "case_category": "medical",
  "human_required": true,
  "p0_signals": ["sangrado grave"],
  "location_hint": "Colonia Centro"
}

Response:
{
  "incident_id": "uuid",
  "stored_at": "ISO8601",
  "status": "stored"
}
```

#### GET /incidents?limit=50&offset=0&risk_level=8&category=medical
```json
Response:
{
  "total": 45,
  "items": [
    {
      "incident_id": "uuid",
      "call_id": "uuid",
      "risk_level": 8,
      "branch": "critical",
      "case_category": "medical",
      "human_required": true,
      "timestamp": "ISO8601"
    }
  ]
}
```

#### GET /analytics/summary
```json
Response:
{
  "total_incidents": 1523,
  "by_risk_level": {
    "1": 120,
    "2": 230,
    "3": 310,
    "4": 280,
    "5": 195,
    "6": 150,
    "7": 110,
    "8": 75,
    "9": 35,
    "10": 18
  },
  "by_branch": {
    "low": 940,
    "mid": 195,
    "critical": 388
  },
  "by_category": {
    "security": 450,
    "medical": 380,
    "protection_civil": 210,
    "public_services": 320,
    "social_support": 95,
    "victim_attention": 68
  },
  "human_required_count": 388,
  "p0_signals_count": 215,
  "nna_involved_count": 142,
  "last_updated": "ISO8601"
}
```

#### GET /analytics/predictions
```json
Response:
{
  "volume_forecast": {
    "next_hour": {
      "predicted_calls": 45,
      "confidence": 0.75,
      "trend": "increasing"
    },
    "hourly_pattern": [
      {"hour": 0, "avg_calls": 12},
      {"hour": 1, "avg_calls": 8},
      {"hour": 2, "avg_calls": 6},
      ...
      {"hour": 23, "avg_calls": 15}
    ]
  },
  "category_distribution": {
    "next_hour": {
      "security": 0.30,
      "medical": 0.25,
      "protection_civil": 0.15,
      "public_services": 0.20,
      "social_support": 0.05,
      "victim_attention": 0.05
    }
  },
  "risk_zones": [
    {
      "zone": "Centro",
      "risk_score": 8.5,
      "incident_count": 45,
      "primary_category": "security"
    },
    {
      "zone": "Iztapalapa",
      "risk_score": 7.2,
      "incident_count": 38,
      "primary_category": "medical"
    }
  ],
  "generated_at": "ISO8601",
  "model_version": "mock-v1.0"
}
```

#### GET /health
```json
Response:
{
  "status": "healthy",
  "service": "api-analytics",
  "version": "1.0.0",
  "database": "connected",
  "total_incidents": 1523,
  "timestamp": "ISO8601"
}
```

**Mock Prediction Logic:**

```python
# Volume Forecast (based on historical hourly averages)
def predict_volume():
    current_hour = datetime.now().hour
    historical_avg = get_avg_calls_for_hour(current_hour)
    
    # Add random variation ±20%
    predicted = historical_avg * random.uniform(0.8, 1.2)
    
    # Determine trend
    prev_hour_avg = get_avg_calls_for_hour(current_hour - 1)
    trend = "increasing" if predicted > prev_hour_avg else "decreasing"
    
    return {
        "predicted_calls": int(predicted),
        "confidence": 0.75,
        "trend": trend
    }

# Category Distribution (based on recent patterns)
def predict_categories():
    recent_incidents = get_last_n_incidents(100)
    category_counts = count_by_category(recent_incidents)
    total = sum(category_counts.values())
    
    return {
        cat: count / total 
        for cat, count in category_counts.items()
    }

# Risk Zones (based on location_hint aggregation)
def predict_risk_zones():
    zones = aggregate_by_location_hint()
    
    return [
        {
            "zone": zone_name,
            "risk_score": calculate_avg_risk(zone_incidents),
            "incident_count": len(zone_incidents),
            "primary_category": most_common_category(zone_incidents)
        }
        for zone_name, zone_incidents in zones.items()
    ][:5]  # Top 5 zones
```

## n8n Workflow Design

### Workflow: "911 AI Flow Demo - Main"

**Trigger:** Webhook POST `/webhook/911-call`

**Authentication:** Basic Auth (username/password in .env)

**Nodes:**

1. **Webhook Trigger**
   - Method: POST
   - Path: `/webhook/911-call`
   - Authentication: Basic Auth
   - Response Mode: When Last Node Finishes

2. **Validate Input**
   - Type: Function
   - Code: Validate required fields (transcript, metadata)

3. **HTTP Request - Ingest**
   - Method: POST
   - URL: `http://api-ingest:8001/raw-conversations`
   - Body: `{{ $json }}`
   - Retry on Fail: 3 times, 2s delay

4. **HTTP Request - Triage**
   - Method: POST
   - URL: `http://api-triage:8002/triage`
   - Body: Combine webhook + ingest response
   - Retry on Fail: 3 times, 2s delay

5. **HTTP Request - Analytics**
   - Method: POST
   - URL: `http://api-analytics:8003/incidents`
   - Body: Combine all previous responses
   - Retry on Fail: 3 times, 2s delay

6. **Format Response**
   - Type: Function
   - Code: Consolidate all responses into final JSON

7. **Respond to Webhook**
   - Status Code: 200
   - Body: Formatted response

**Error Handling:**
- Each HTTP node has retry logic (3 attempts, 2s delay)
- If any service fails after retries, return 500 with error details
- Log all errors to n8n execution log

## Docker Compose Configuration

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: emergency-db
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - emergency-network

  api-ingest:
    build: ./services/api-ingest
    container_name: api-ingest
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      SERVICE_PORT: 8001
    ports:
      - "8001:8001"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - emergency-network

  api-triage:
    build: ./services/api-triage
    container_name: api-triage
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      SERVICE_PORT: 8002
    ports:
      - "8002:8002"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - emergency-network

  api-analytics:
    build: ./services/api-analytics
    container_name: api-analytics
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      SERVICE_PORT: 8003
    ports:
      - "8003:8003"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - emergency-network

  n8n:
    image: n8nio/n8n:latest
    container_name: n8n-orchestrator
    environment:
      N8N_BASIC_AUTH_ACTIVE: "true"
      N8N_BASIC_AUTH_USER: ${N8N_USER}
      N8N_BASIC_AUTH_PASSWORD: ${N8N_PASSWORD}
      N8N_HOST: localhost
      N8N_PORT: 5678
      N8N_PROTOCOL: http
      WEBHOOK_URL: http://localhost:5678
    volumes:
      - n8n_data:/home/node/.n8n
      - ./n8n/workflows:/workflows
    ports:
      - "5678:5678"
    depends_on:
      - api-ingest
      - api-triage
      - api-analytics
    networks:
      - emergency-network

volumes:
  postgres_data:
  n8n_data:

networks:
  emergency-network:
    driver: bridge
```

## Environment Configuration

**.env.example:**
```bash
# PostgreSQL Configuration
POSTGRES_DB=emergency_demo
POSTGRES_USER=emergency_user
POSTGRES_PASSWORD=change_this_password_in_production

# n8n Configuration
N8N_USER=admin
N8N_PASSWORD=change_this_password_in_production

# API Configuration
API_INGEST_PORT=8001
API_TRIAGE_PORT=8002
API_ANALYTICS_PORT=8003

# Webhook Authentication (for external calls)
WEBHOOK_AUTH_TOKEN=change_this_token_in_production

# Demo Configuration
DEMO_MODE=true
LOG_LEVEL=INFO
```

## Testing Strategy

### Test Scenarios

#### Scenario 1: Low Risk (Orientation)
```json
{
  "transcript": "Hola, quiero reportar un bache en la calle Reforma. No es urgente pero está grande.",
  "metadata": {
    "source": "demo",
    "timestamp": "2026-06-06T10:30:00Z"
  }
}

Expected:
- risk_level: 2-3
- branch: "low"
- case_category: "public_services"
- human_required: false
- No P0 signals
```

#### Scenario 2: Medium Risk (Validation Level 5)
```json
{
  "transcript": "Hay un accidente de tránsito en Insurgentes con Reforma. Hay varios carros chocados pero no veo heridos graves. Necesitan grúa.",
  "metadata": {
    "source": "demo",
    "timestamp": "2026-06-06T11:45:00Z"
  }
}

Expected:
- risk_level: 5
- branch: "mid"
- case_category: "protection_civil"
- human_required: true (for validation)
- No P0 signals
```

#### Scenario 3: Critical P0 (Child in Danger)
```json
{
  "transcript": "¡Auxilio! Hay un niño sangrando mucho en la cabeza. Se cayó de las escaleras. Está consciente pero sangra mucho. Estamos en la Colonia Centro.",
  "metadata": {
    "source": "demo",
    "timestamp": "2026-06-06T14:20:00Z"
  }
}

Expected:
- risk_level: 8-9
- branch: "critical"
- case_category: "medical"
- medical_category: "trauma"
- human_required: true
- best_interest_child: true
- P0 signals: ["sangrado grave", "menor de edad"]
- primary_authority: "ERUM"
```

### Unit Tests (pytest)

Each service should have:
- Test health endpoint
- Test main functionality with valid input
- Test error handling with invalid input
- Test database connection
- Test redaction/scoring/analytics logic

### Integration Tests

- Test complete workflow through n8n
- Test all three scenarios end-to-end
- Verify data persistence in all schemas
- Verify metrics calculation

## Security Considerations

### Data Protection
- No real PII stored
- All sensitive fields redacted
- Demo data only
- No audio processing

### Access Control
- n8n webhook requires Basic Auth
- Database credentials in .env (not committed)
- Internal Docker network isolation
- No external database access

### Compliance (Mexican Law)
- LFPDPPP compliance (no real personal data)
- NNA protection (best interest principle)
- Consent tracking (demo consent only)
- Data minimization (only necessary fields)

## Operational Scripts

### 00_precheck.sh
- Check Docker installed
- Check Docker Compose installed
- Check ports 5432, 5678, 8001-8003 available
- Check .env file exists

### 01_start.sh
- Run precheck
- docker compose up -d
- Wait for health checks
- Display service URLs

### 02_stop.sh
- docker compose down
- Optional: remove volumes

### 03_logs.sh
- docker compose logs -f [service]

### 04_test_environment.sh
- Test all /health endpoints
- Test database connection
- Test n8n accessibility

### 05_seed_demo_data.sh
- Insert 3 test scenarios via webhook
- Verify data in database
- Display results

## Documentation Structure

### architecture.md
- System overview
- Component descriptions
- Data flow diagrams
- Technology decisions

### legal_privacy.md
- LFPDPPP compliance
- NNA protection guidelines
- Consent management
- Data retention policies

### cybersecurity.md
- Threat model
- Security controls
- Vulnerability assessment
- Incident response

### api_contract.md
- OpenAPI 3.0 specifications
- Request/response examples
- Error codes
- Rate limiting

### lovable_integration.md
- Webhook usage guide
- Dashboard data format
- Real-time updates
- Example queries

### demo_script.md
- Step-by-step demo flow
- Test scenarios
- Expected results
- Troubleshooting

## Lovable Integration

### Dashboard Data Sources

1. **Real-time Incidents**
   - Endpoint: `GET http://localhost:8003/incidents?limit=10`
   - Refresh: Every 5 seconds
   - Display: Recent incidents table

2. **Summary Metrics**
   - Endpoint: `GET http://localhost:8003/analytics/summary`
   - Refresh: Every 30 seconds
   - Display: KPI cards, charts

3. **Predictions**
   - Endpoint: `GET http://localhost:8003/analytics/predictions`
   - Refresh: Every 60 seconds
   - Display: Forecast charts, risk map

4. **Submit Test Call**
   - Endpoint: `POST http://localhost:5678/webhook/911-call`
   - Auth: Basic (username/password from .env)
   - Display: Response in modal

### Example Lovable API Calls

```javascript
// Fetch summary metrics
const response = await fetch('http://localhost:8003/analytics/summary');
const metrics = await response.json();

// Submit test call
const callResponse = await fetch('http://localhost:5678/webhook/911-call', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Basic ' + btoa('admin:password')
  },
  body: JSON.stringify({
    transcript: "Test call transcript",
    metadata: { source: "lovable-dashboard" }
  })
});
```

## MVP Limitations

1. **Simulated AI**: No real ML models, only keyword matching
2. **No Audio**: Text-only processing
3. **Mock Predictions**: Statistical patterns, not real forecasting
4. **Single Host**: No horizontal scaling
5. **Basic Auth**: Production would need OAuth2/JWT
6. **No Real-time**: Polling-based updates, not WebSockets
7. **Limited Redaction**: Regex-based, not NLP
8. **No Geolocation**: Text-based location hints only
9. **No Call Recording**: No audio storage or playback
10. **Demo Data Only**: Not production-ready

## Next Steps After MVP

1. **Connect Lovable Dashboard**
   - Implement API calls
   - Create visualizations
   - Add real-time updates

2. **Enhanced AI**
   - Integrate real NLP models
   - Improve classification accuracy
   - Add sentiment analysis

3. **Production Hardening**
   - Add authentication/authorization
   - Implement rate limiting
   - Add monitoring/alerting
   - Set up CI/CD pipeline

4. **Scalability**
   - Add load balancing
   - Implement caching
   - Optimize database queries
   - Add message queue (RabbitMQ/Kafka)

5. **Compliance**
   - Legal review
   - Security audit
   - Penetration testing
   - Privacy impact assessment

## Success Criteria

✅ All services start successfully
✅ All /health endpoints respond
✅ n8n accessible at localhost:5678
✅ Workflow processes 3 test scenarios
✅ Data persists in all schemas
✅ Analytics endpoints return metrics
✅ Predictions endpoint returns forecasts
✅ Documentation complete
✅ Scripts executable
✅ Ready for Lovable integration

---

**Document Version:** 1.0
**Last Updated:** 2026-06-06
**Status:** Ready for Implementation