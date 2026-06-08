# Contrato de APIs — CENTINELA_CDMX_IA

> Versión 2.0 · Junio 2026  
> **Nota:** No enviar PII real. Todos los ejemplos usan datos sintéticos.

---

## Tabla de contenidos

1. [api-ingest — A1 Recolector (puerto 8001)](#api-ingest)
2. [api-triage — A4 Triador (puerto 8002)](#api-triage)
3. [api-analytics — A5/A6 (puerto 8003)](#api-analytics)
4. [n8n Webhook — A7 Bravo (puerto 5678)](#n8n-webhook)
5. [api-gateway — CORS proxy (puerto 8010)](#api-gateway)
6. [Códigos HTTP](#códigos-http)
7. [Flujo completo de ejemplo](#flujo-completo)

---

## api-ingest — A1 Recolector {#api-ingest}

**Base URL:** `http://localhost:8001`

### POST /raw-conversations

Recibe la transcripción cruda, redacta PII automáticamente y almacena solo la versión redactada.  
**La transcripción original nunca se persiste — Privacy by Design.**

**Request:**
```json
{
  "transcript": "Hola, hay un bache en la calle principal. Teléfono 5512345678.",
  "metadata": {
    "source": "operator_dashboard",
    "timestamp": "2026-06-08T14:00:00Z"
  }
}
```

**Response 201:**
```json
{
  "call_id": "123e4567-e89b-12d3-a456-426614174000",
  "trace_id": "223e4567-e89b-12d3-a456-426614174000",
  "redacted_text": "Hola, hay un bache en la calle principal. Teléfono [TELÉFONO-REDACTADO].",
  "redaction_summary": {
    "phones_redacted": 1,
    "emails_redacted": 0,
    "names_redacted": 0,
    "addresses_redacted": 0
  },
  "created_at": "2026-06-08T14:00:01.123Z"
}
```

> **Nota:** El campo es `created_at` (no `stored_at`).  
> Los marcadores de redacción usan formato español: `[TELÉFONO-REDACTADO]`, `[NOMBRE-REDACTADO]`, `[DIRECCIÓN-REDACTADA]`, `[EMAIL-REDACTADO]`.

**Campos del request:**
- `transcript` (string, requerido, mín. 1 char): texto de la llamada
- `metadata` (object, opcional): metadatos adicionales

**curl:**
```bash
curl -s -X POST http://localhost:8001/raw-conversations \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Hay un bache en la calle. Tel 5512345678.", "metadata": {"source": "test"}}'
```

---

### GET /raw-conversations

Lista conversaciones redactadas paginadas.

**Response 200:**
```json
{
  "total": 25,
  "items": [
    {
      "call_id": "123e4567-...",
      "trace_id": "223e4567-...",
      "redacted_text": "Hola, hay un bache en [DIRECCIÓN-REDACTADA]...",
      "created_at": "2026-06-08T14:00:01Z"
    }
  ]
}
```

**Query params:** `limit` (default 50, máx 100) · `offset` (default 0)

---

### GET /health

```json
{
  "status": "healthy",
  "service": "api-ingest",
  "version": "2.0.0",
  "database": "connected",
  "timestamp": "2026-06-08T14:00:00Z"
}
```

---

## api-triage — A4 Triador {#api-triage}

**Base URL:** `http://localhost:8002`

### POST /triage

Clasificación determinista 1-10 con detección de señales P0, grupos de protección reforzada y canalización a autoridades CDMX.

**RESTRICCIÓN TÉCNICA:** Llamadas con señales P0 activas nunca se degradan por debajo de nivel 6.

**Request:**
```json
{
  "transcript": "Hay un incendio en mi edificio, necesito ayuda urgente",
  "call_id": "123e4567-e89b-12d3-a456-426614174000",
  "trace_id": "223e4567-e89b-12d3-a456-426614174000",
  "consent": false,
  "location_hint": "Colonia Centro"
}
```

> **Nota:** `consent` es `false` por defecto — gate SOLID desactivado. Solo enviar `true` cuando el ciudadano lo autorice explícitamente.

**Response 200:**
```json
{
  "call_id": "123e4567-e89b-12d3-a456-426614174000",
  "trace_id": "223e4567-e89b-12d3-a456-426614174000",
  "risk_level": 8,
  "branch": "critical",
  "priority_class": "critical",
  "case_category": "protection_civil",
  "medical_category": null,
  "protected_group_flags": {
    "child_or_adolescent": false,
    "older_adult": false,
    "disability": false,
    "woman": false,
    "migrant_or_international_protection": false,
    "indigenous_person": false,
    "lgbttti": false,
    "homelessness": false,
    "human_rights_defender": false
  },
  "best_interest_child": false,
  "human_required": true,
  "primary_authority": "Protección Civil CDMX / Heroico Cuerpo de Bomberos",
  "support_authorities": ["Secretaría de Salud CDMX", "SSC", "C5"],
  "public_stage_phrase": "Estoy en la etapa de priorización. Atención prioritaria activada.",
  "rationale_public": "Señales detectadas: incendio; Nivel crítico",
  "trust_flags": {
    "confidence_score": 0.85,
    "ambiguity_detected": false
  },
  "p0_signals": ["incendio"],
  "keywords_detected": {
    "protection_civil": ["incendio"]
  }
}
```

**Grupos de protección reforzada detectados automáticamente:**
`child_or_adolescent` · `older_adult` · `disability` · `woman` · `migrant_or_international_protection` · `indigenous_person` · `lgbttti` · `homelessness` · `human_rights_defender`

> Uso exclusivo para priorización protectora. Nunca para perfilar ni discriminar.

**curl:**
```bash
curl -s -X POST http://localhost:8002/triage \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Hay un incendio", "call_id": "UUID_AQUI", "consent": false}'
```

---

### GET /health

```json
{
  "status": "healthy",
  "service": "api-triage",
  "version": "2.0.0",
  "rules_loaded": 145,
  "timestamp": "2026-06-08T14:00:00Z"
}
```

---

## api-analytics — A5 Cartógrafo / A6 Estratega {#api-analytics}

**Base URL:** `http://localhost:8003`

### POST /incidents

Registra incidente clasificado para analítica geoespacial.

**Request:**
```json
{
  "call_id": "123e4567-e89b-12d3-a456-426614174000",
  "trace_id": "223e4567-e89b-12d3-a456-426614174000",
  "risk_level": 8,
  "branch": "critical",
  "case_category": "protection_civil",
  "human_required": true,
  "p0_signals": ["incendio"],
  "location_hint": "Colonia Centro"
}
```

> `location_hint` se normaliza automáticamente a nivel de alcaldía — nunca se almacena dirección completa.

**Response 201:**
```json
{
  "incident_id": "323e4567-e89b-12d3-a456-426614174000",
  "stored_at": "2026-06-08T14:00:02Z",
  "status": "stored"
}
```

---

### GET /analytics/summary

Métricas agregadas del sistema.

**Response 200:**
```json
{
  "total_incidents": 50,
  "by_risk_level": {"6": 4, "7": 3, "8": 4, "9": 2, "10": 1},
  "by_branch": {"low": 30, "mid": 6, "critical": 14},
  "by_category": {"security": 20, "medical": 15, "protection_civil": 10},
  "human_required_count": 20,
  "p0_signals_count": 14,
  "nna_involved_count": 3,
  "last_updated": "2026-06-08T14:00:00Z"
}
```

---

### GET /analytics/predictions

Predicciones de volumen y zonas de riesgo (mock para MVP).

**Response 200:**
```json
{
  "volume_forecast": {
    "predicted_calls": 28,
    "confidence": 0.75,
    "trend": "increasing",
    "hourly_pattern": [{"hour": 8, "avg_calls": 25}]
  },
  "category_distribution": {
    "security": 0.30,
    "medical": 0.25,
    "protection_civil": 0.15,
    "public_services": 0.20,
    "social_support": 0.05,
    "victim_attention": 0.05
  },
  "risk_zones": [
    {"zone": "Iztapalapa", "risk_score": 6.8, "incident_count": 38, "primary_category": "security"}
  ],
  "generated_at": "2026-06-08T14:00:00Z",
  "ai_model_version": "mock-v1.0"
}
```

> Las predicciones son mock/demo. En producción se integran con A5 Cartógrafo (H3 + PostGIS + INEGI).

---

## n8n Webhook — A7 Bravo {#n8n-webhook}

**Base URL:** `http://localhost:5678`  
**Autenticación:** Basic Auth (`admin` / valor en `.env`)

### POST /webhook/911-call

Endpoint principal. Orquesta el flujo completo: ingest → triage → analytics → respuesta consolidada.

**Request:**
```json
{
  "transcript": "Hay un incendio en mi edificio, necesito ayuda urgente",
  "metadata": {
    "source": "operator_dashboard",
    "timestamp": "2026-06-08T14:00:00Z"
  },
  "location_hint": "Colonia Centro",
  "solid_consent": false
}
```

> `solid_consent` es `false` por defecto. Solo enviar `true` cuando el ciudadano lo autorice explícitamente (gate SOLID, LFPDPPP Art. 8).

**Response 200:**
```json
{
  "success": true,
  "call_id": "123e4567-...",
  "trace_id": "223e4567-...",
  "risk_level": 8,
  "branch": "critical",
  "case_category": "protection_civil",
  "human_required": true,
  "p0_signals": ["incendio"],
  "primary_authority": "Protección Civil CDMX / Heroico Cuerpo de Bomberos",
  "support_authorities": ["Secretaría de Salud CDMX", "SSC", "C5"],
  "best_interest_child": false,
  "protected_group_flags": {},
  "incident_id": "323e4567-...",
  "public_stage_phrase": "Estoy en la etapa de priorización. Atención prioritaria activada.",
  "rationale_public": "Señales detectadas: incendio; Nivel crítico",
  "processed_at": "2026-06-08T14:00:02Z"
}
```

**curl:**
```bash
curl -s -X POST http://localhost:5678/webhook/911-call \
  -u admin:changeme \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Hay un incendio", "location_hint": "Colonia Centro", "solid_consent": false}'
```

---

## api-gateway — CORS proxy {#api-gateway}

**Base URL:** `http://localhost:8010`

Proxy CORS para el dashboard Lovable. Expone el flujo 911 y los endpoints de analítica sin exponer credenciales directas de n8n.

| Endpoint gateway | Redirige a |
|---|---|
| `POST /911-call` | `http://n8n:5678/webhook/911-call` |
| `GET /analytics/summary` | `http://api-analytics:8003/analytics/summary` |
| `GET /analytics/predictions` | `http://api-analytics:8003/analytics/predictions` |
| `GET /health` | Estado del gateway |

**Variables de entorno para Lovable:**
```
VITE_N8N_WEBHOOK_URL=http://localhost:8010/911-call
VITE_ANALYTICS_SUMMARY_URL=http://localhost:8010/analytics/summary
VITE_ANALYTICS_PREDICTIONS_URL=http://localhost:8010/analytics/predictions
```

---

## Códigos HTTP {#códigos-http}

| Código | Significado | Cuándo ocurre |
|---|---|---|
| 200 OK | Éxito | GET, POST de clasificación |
| 201 Created | Recurso creado | POST /incidents |
| 400 Bad Request | Payload inválido | JSON malformado, campos faltantes |
| 401 Unauthorized | Autenticación fallida | Credenciales n8n incorrectas |
| 422 Unprocessable Entity | Validación fallida | `call_id` no existe en BD |
| 500 Internal Server Error | Error del servidor | Error de BD, servicio caído |

---

## Flujo completo de ejemplo {#flujo-completo}

```bash
# 1. Ingestar llamada
INGEST=$(curl -s -X POST http://localhost:8001/raw-conversations \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Auxilio, hay un niño sangrando. Tiene 8 años.", "metadata": {"source": "test"}}')

CALL_ID=$(echo $INGEST | jq -r '.call_id')
TRACE_ID=$(echo $INGEST | jq -r '.trace_id')
REDACTED=$(echo $INGEST | jq -r '.redacted_text')

# 2. Clasificar
TRIAGE=$(curl -s -X POST http://localhost:8002/triage \
  -H "Content-Type: application/json" \
  -d "{"transcript": "$REDACTED", "call_id": "$CALL_ID", "consent": false}")

RISK=$(echo $TRIAGE | jq '.risk_level')
BRANCH=$(echo $TRIAGE | jq -r '.branch')
P0=$(echo $TRIAGE | jq -c '.p0_signals')
NNA=$(echo $TRIAGE | jq '.best_interest_child')

echo "Nivel: $RISK | Rama: $BRANCH | P0: $P0 | NNA: $NNA"
# Esperado: Nivel: 8+ | Rama: critical | P0: ["sangrado grave","maltrato infantil"] | NNA: true

# 3. Registrar en analítica
curl -s -X POST http://localhost:8003/incidents \
  -H "Content-Type: application/json" \
  -d "{"call_id": "$CALL_ID", "trace_id": "$TRACE_ID",
       "risk_level": $RISK, "branch": "$BRANCH",
       "case_category": "medical", "human_required": true,
       "p0_signals": $P0}" | jq '.incident_id'

# 4. Ver resumen
curl -s http://localhost:8003/analytics/summary | jq '{total_incidents, p0_signals_count, human_required_count}'
```

---

## Errores comunes

### call_id no existe (422)
```bash
# Error: triage antes de ingest
curl -X POST http://localhost:8002/triage -d '{"call_id": "00000000-...", "transcript": "test", "consent": false}'
# Solución: siempre ingestar primero con api-ingest
```

### Autenticación n8n (401)
```bash
# Error: llamar webhook sin credenciales
curl -X POST http://localhost:5678/webhook/911-call -d '{"transcript": "test"}'
# Solución: usar -u admin:changeme o el api-gateway en puerto 8010
```

### Servicios no disponibles
```bash
docker compose ps                    # verificar estado
./scripts/01_start.sh all            # levantar todo
./scripts/04_test_environment.sh all # validar
```

---

*CENTINELA_CDMX_IA · Contrato de APIs v2.0 · Junio 2026*
