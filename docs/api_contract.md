# Contrato de APIs - 911 AI Flow Demo

## Descripción General

Este documento especifica el contrato HTTP de todos los endpoints del sistema, incluyendo request/response JSON, códigos HTTP, y ejemplos curl.

**⚠️ Importante:** No enviar PII real. Todos los ejemplos usan datos sintéticos.

---

## Tabla de Contenidos

1. [api-ingest (Puerto 8001)](#api-ingest-puerto-8001)
2. [api-triage (Puerto 8002)](#api-triage-puerto-8002)
3. [api-analytics (Puerto 8003)](#api-analytics-puerto-8003)
4. [n8n Webhook](#n8n-webhook)
5. [Códigos HTTP](#códigos-http)
6. [Errores Comunes](#errores-comunes)

---

## api-ingest (Puerto 8001)

### Base URL
```
http://localhost:8001
```

### Endpoints

#### 1. POST /raw-conversations

**Descripción:** Ingestar nueva conversación con redacción automática de PII.

**Request:**
```http
POST /raw-conversations HTTP/1.1
Host: localhost:8001
Content-Type: application/json

{
  "transcript": "Hola, mi nombre es Juan Pérez, teléfono 5512345678. Hay un bache en Calle Madero 45.",
  "metadata": {
    "source": "demo",
    "timestamp": "2026-06-06T12:00:00Z"
  }
}
```

**Response (200 OK):**
```json
{
  "call_id": "123e4567-e89b-12d3-a456-426614174000",
  "trace_id": "223e4567-e89b-12d3-a456-426614174000",
  "redacted_text": "Hola, mi nombre es [NAME_REDACTED], teléfono [PHONE_REDACTED]. Hay un bache en [ADDRESS_REDACTED].",
  "stored_at": "2026-06-06T12:00:01.123Z",
  "redaction_summary": {
    "phones_redacted": 1,
    "emails_redacted": 0,
    "names_redacted": 1,
    "addresses_redacted": 1
  }
}
```

**Ejemplo curl:**
```bash
curl -X POST http://localhost:8001/raw-conversations \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Hola, necesito reportar un bache. Mi teléfono es 5512345678.",
    "metadata": {
      "source": "test",
      "timestamp": "2026-06-06T12:00:00Z"
    }
  }'
```

**Campos:**
- `transcript` (string, required): Texto de la llamada (1-10000 caracteres)
- `metadata` (object, optional): Metadatos adicionales

**Códigos HTTP:**
- `200 OK`: Conversación ingresada exitosamente
- `400 Bad Request`: Payload inválido
- `422 Unprocessable Entity`: Validación fallida
- `500 Internal Server Error`: Error del servidor

---

#### 2. GET /raw-conversations

**Descripción:** Listar conversaciones redactadas (paginado).

**Request:**
```http
GET /raw-conversations?limit=10&offset=0 HTTP/1.1
Host: localhost:8001
```

**Response (200 OK):**
```json
{
  "total": 25,
  "items": [
    {
      "call_id": "123e4567-e89b-12d3-a456-426614174000",
      "trace_id": "223e4567-e89b-12d3-a456-426614174000",
      "redacted_text": "Hola, mi nombre es [NAME_REDACTED]...",
      "timestamp": "2026-06-06T12:00:01Z"
    }
  ]
}
```

**Ejemplo curl:**
```bash
curl http://localhost:8001/raw-conversations?limit=5
```

**Query Parameters:**
- `limit` (int, optional, default=10): Número de resultados
- `offset` (int, optional, default=0): Offset para paginación

---

#### 3. GET /health

**Descripción:** Health check del servicio.

**Request:**
```http
GET /health HTTP/1.1
Host: localhost:8001
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "api-ingest",
  "version": "1.0.0",
  "database": "connected",
  "total_conversations": 25,
  "timestamp": "2026-06-06T12:00:00Z"
}
```

**Ejemplo curl:**
```bash
curl http://localhost:8001/health
```

---

## api-triage (Puerto 8002)

### Base URL
```
http://localhost:8002
```

### Endpoints

#### 1. POST /triage

**Descripción:** Clasificar llamada con IA determinista.

**Request:**
```http
POST /triage HTTP/1.1
Host: localhost:8002
Content-Type: application/json

{
  "transcript": "Hay un incendio en mi edificio, necesito ayuda urgente",
  "call_id": "123e4567-e89b-12d3-a456-426614174000",
  "trace_id": "223e4567-e89b-12d3-a456-426614174000",
  "consent": true,
  "location_hint": "Colonia Centro"
}
```

**Response (200 OK):**
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
    "nna_involved": false,
    "elderly": false,
    "disability": false,
    "gender_violence": false
  },
  "best_interest_child": false,
  "human_required": true,
  "primary_authority": "Protección Civil",
  "support_authorities": ["Bomberos", "ERUM"],
  "public_stage_phrase": "Emergencia de incendio detectada. Unidades en camino.",
  "rationale_public": "Incendio requiere atención inmediata de Protección Civil y Bomberos.",
  "trust_flags": {
    "confidence_score": 0.95,
    "ambiguity_detected": false
  },
  "p0_signals": ["incendio"],
  "keywords_detected": {
    "protection_civil": ["incendio"],
    "urgency": ["urgente", "ayuda"]
  }
}
```

**Ejemplo curl:**
```bash
curl -X POST http://localhost:8002/triage \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Hay un incendio en mi edificio",
    "call_id": "123e4567-e89b-12d3-a456-426614174000",
    "trace_id": "223e4567-e89b-12d3-a456-426614174000",
    "consent": true,
    "location_hint": "Colonia Centro"
  }'
```

**Campos:**
- `transcript` (string, required): Texto redactado de la llamada
- `call_id` (string, required): UUID de la llamada
- `trace_id` (string, optional): UUID de trazabilidad
- `consent` (boolean, optional, default=true): Consentimiento
- `location_hint` (string, optional): Ubicación aproximada

**Códigos HTTP:**
- `200 OK`: Clasificación exitosa
- `400 Bad Request`: Payload inválido
- `422 Unprocessable Entity`: call_id no existe
- `500 Internal Server Error`: Error del servidor

---

#### 2. GET /health

**Descripción:** Health check del servicio.

**Request:**
```http
GET /health HTTP/1.1
Host: localhost:8002
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "api-triage",
  "version": "1.0.0",
  "rules_loaded": 120,
  "timestamp": "2026-06-06T12:00:00Z"
}
```

**Ejemplo curl:**
```bash
curl http://localhost:8002/health
```

---

## api-analytics (Puerto 8003)

### Base URL
```
http://localhost:8003
```

### Endpoints

#### 1. POST /incidents

**Descripción:** Registrar incidente clasificado.

**Request:**
```http
POST /incidents HTTP/1.1
Host: localhost:8003
Content-Type: application/json

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

**Response (201 Created):**
```json
{
  "incident_id": "323e4567-e89b-12d3-a456-426614174000",
  "stored_at": "2026-06-06T12:00:02Z",
  "status": "stored"
}
```

**Ejemplo curl:**
```bash
curl -X POST http://localhost:8003/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "123e4567-e89b-12d3-a456-426614174000",
    "trace_id": "223e4567-e89b-12d3-a456-426614174000",
    "risk_level": 8,
    "branch": "critical",
    "case_category": "protection_civil",
    "human_required": true,
    "p0_signals": ["incendio"],
    "location_hint": "Colonia Centro"
  }'
```

**Campos:**
- `call_id` (string, required): UUID de la llamada
- `trace_id` (string, required): UUID de trazabilidad
- `risk_level` (int, required): Nivel de riesgo 1-10
- `branch` (string, required): low/mid/critical
- `case_category` (string, required): Categoría del caso
- `human_required` (boolean, required): Requiere humano
- `p0_signals` (array, required): Señales P0 detectadas
- `location_hint` (string, optional): Ubicación (se normaliza)

---

#### 2. GET /incidents

**Descripción:** Listar incidentes (paginado).

**Request:**
```http
GET /incidents?limit=10&offset=0 HTTP/1.1
Host: localhost:8003
```

**Response (200 OK):**
```json
{
  "total": 50,
  "items": [
    {
      "incident_id": "323e4567-e89b-12d3-a456-426614174000",
      "call_id": "123e4567-e89b-12d3-a456-426614174000",
      "risk_level": 8,
      "branch": "critical",
      "case_category": "protection_civil",
      "human_required": true,
      "timestamp": "2026-06-06T12:00:02Z"
    }
  ]
}
```

**Ejemplo curl:**
```bash
curl http://localhost:8003/incidents?limit=5
```

---

#### 3. GET /analytics/summary

**Descripción:** Obtener métricas agregadas.

**Request:**
```http
GET /analytics/summary HTTP/1.1
Host: localhost:8003
```

**Response (200 OK):**
```json
{
  "total_incidents": 50,
  "by_risk_level": {
    "1": 5,
    "2": 8,
    "3": 10,
    "4": 7,
    "5": 6,
    "6": 4,
    "7": 3,
    "8": 4,
    "9": 2,
    "10": 1
  },
  "by_branch": {
    "low": 30,
    "mid": 6,
    "critical": 14
  },
  "by_category": {
    "public_services": 20,
    "security": 10,
    "medical": 8,
    "protection_civil": 7,
    "social_support": 3,
    "victim_attention": 2
  },
  "human_required_count": 20,
  "p0_signals_count": 14,
  "nna_involved_count": 3,
  "last_updated": "2026-06-06T12:00:00Z"
}
```

**Ejemplo curl:**
```bash
curl http://localhost:8003/analytics/summary | jq
```

---

#### 4. GET /analytics/predictions

**Descripción:** Obtener predicciones mock.

**Request:**
```http
GET /analytics/predictions HTTP/1.1
Host: localhost:8003
```

**Response (200 OK):**
```json
{
  "volume_forecast": {
    "predicted_calls": 28,
    "confidence": 0.75,
    "trend": "increasing",
    "hourly_pattern": [
      {"hour": 0, "avg_calls": 8},
      {"hour": 1, "avg_calls": 6},
      {"hour": 8, "avg_calls": 25},
      {"hour": 12, "avg_calls": 30}
    ]
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
    {
      "zone": "Centro",
      "risk_score": 7.5,
      "incident_count": 15,
      "primary_category": "security"
    },
    {
      "zone": "Iztapalapa",
      "risk_score": 6.8,
      "incident_count": 12,
      "primary_category": "medical"
    }
  ],
  "generated_at": "2026-06-06T12:00:00Z",
  "ai_model_version": "mock-v1.0"
}
```

**Ejemplo curl:**
```bash
curl http://localhost:8003/analytics/predictions | jq
```

**Nota:** Las predicciones son mock/demo, no basadas en ML real.

---

#### 5. GET /health

**Descripción:** Health check del servicio.

**Request:**
```http
GET /health HTTP/1.1
Host: localhost:8003
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "api-analytics",
  "version": "1.0.0",
  "database": "connected",
  "total_incidents": 50,
  "timestamp": "2026-06-06T12:00:00Z"
}
```

**Ejemplo curl:**
```bash
curl http://localhost:8003/health
```

---

## n8n Webhook

### Base URL
```
http://localhost:5678
```

### Endpoint

#### POST /webhook/911-call

**Descripción:** Webhook principal que orquesta el flujo completo.

**Autenticación:** Basic Auth (admin/changeme)

**Request:**
```http
POST /webhook/911-call HTTP/1.1
Host: localhost:5678
Content-Type: application/json
Authorization: Basic YWRtaW46Y2hhbmdlbWU=

{
  "transcript": "Hay un incendio en mi edificio, necesito ayuda urgente",
  "metadata": {
    "source": "lovable_dashboard",
    "timestamp": "2026-06-06T12:00:00Z"
  },
  "location_hint": "Colonia Centro",
  "solid_consent": true
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "call_id": "123e4567-e89b-12d3-a456-426614174000",
  "trace_id": "223e4567-e89b-12d3-a456-426614174000",
  "risk_level": 8,
  "branch": "critical",
  "case_category": "protection_civil",
  "human_required": true,
  "p0_signals": ["incendio"],
  "primary_authority": "Protección Civil",
  "support_authorities": ["Bomberos", "ERUM"],
  "incident_id": "323e4567-e89b-12d3-a456-426614174000",
  "status": "processed",
  "public_stage_phrase": "Emergencia de incendio detectada. Unidades en camino.",
  "rationale_public": "Incendio requiere atención inmediata de Protección Civil y Bomberos.",
  "processed_at": "2026-06-06T12:00:02Z"
}
```

**Response (400 Bad Request) - Payload Inválido:**
```json
{
  "success": false,
  "error": "Invalid payload",
  "message": "Field transcript is required",
  "received": {
    "metadata": {"source": "test"}
  }
}
```

**Ejemplo curl:**
```bash
curl -X POST http://localhost:5678/webhook/911-call \
  -u admin:changeme \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Hay un incendio en mi edificio",
    "location_hint": "Colonia Centro",
    "solid_consent": true
  }'
```

**Campos:**
- `transcript` (string, required): Texto de la llamada
- `metadata` (object, optional): Metadatos adicionales
- `location_hint` (string, optional): Ubicación aproximada
- `solid_consent` (boolean, optional, default=true): Consentimiento

**Códigos HTTP:**
- `200 OK`: Procesamiento exitoso
- `400 Bad Request`: Payload inválido
- `401 Unauthorized`: Autenticación fallida
- `500 Internal Server Error`: Error en algún servicio

---

## Códigos HTTP

### Códigos de Éxito

| Código | Significado | Uso |
|--------|-------------|-----|
| 200 OK | Solicitud exitosa | GET, POST (mayoría) |
| 201 Created | Recurso creado | POST /incidents |

### Códigos de Error del Cliente

| Código | Significado | Causa Común |
|--------|-------------|-------------|
| 400 Bad Request | Payload inválido | JSON malformado, campos faltantes |
| 401 Unauthorized | Autenticación fallida | Credenciales incorrectas (n8n) |
| 404 Not Found | Recurso no encontrado | Endpoint incorrecto |
| 422 Unprocessable Entity | Validación fallida | call_id no existe, datos inválidos |

### Códigos de Error del Servidor

| Código | Significado | Causa Común |
|--------|-------------|-------------|
| 500 Internal Server Error | Error del servidor | Error de DB, bug en código |
| 503 Service Unavailable | Servicio no disponible | Servicio caído, timeout |

---

## Errores Comunes

### 1. call_id No Existe

**Problema:**
```bash
curl -X POST http://localhost:8002/triage \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Test",
    "call_id": "00000000-0000-0000-0000-000000000000",
    "consent": true
  }'
```

**Error (422):**
```json
{
  "detail": "call_id not found in database"
}
```

**Solución:** Primero crear conversación en api-ingest, luego usar el call_id devuelto.

---

### 2. Transcript Vacío

**Problema:**
```bash
curl -X POST http://localhost:8001/raw-conversations \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "",
    "metadata": {}
  }'
```

**Error (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "transcript"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

**Solución:** Enviar transcript con al menos 1 carácter.

---

### 3. JSON Malformado

**Problema:**
```bash
curl -X POST http://localhost:8001/raw-conversations \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Test"'  # Falta cerrar }
```

**Error (400):**
```json
{
  "detail": "Invalid JSON"
}
```

**Solución:** Verificar sintaxis JSON.

---

### 4. Servicio No Disponible

**Problema:**
```bash
curl http://localhost:8001/health
# curl: (7) Failed to connect to localhost port 8001: Connection refused
```

**Solución:**
```bash
# Verificar que servicios están corriendo
docker compose ps

# Levantar servicios si es necesario
./scripts/01_start.sh all
```

---

### 5. Autenticación Fallida en n8n

**Problema:**
```bash
curl -X POST http://localhost:5678/webhook/911-call \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Test"}'
```

**Error (401):**
```json
{
  "error": "Unauthorized"
}
```

**Solución:** Agregar credenciales Basic Auth:
```bash
curl -X POST http://localhost:5678/webhook/911-call \
  -u admin:changeme \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Test"}'
```

---

## Flujo Completo de Ejemplo

### Escenario: Llamada Crítica P0

```bash
# 1. Ingestar conversación
INGEST_RESPONSE=$(curl -s -X POST http://localhost:8001/raw-conversations \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "¡Auxilio! Hay un niño sangrando mucho de la cabeza.",
    "metadata": {"source": "test"}
  }')

# 2. Extraer call_id y trace_id
CALL_ID=$(echo $INGEST_RESPONSE | jq -r '.call_id')
TRACE_ID=$(echo $INGEST_RESPONSE | jq -r '.trace_id')
REDACTED=$(echo $INGEST_RESPONSE | jq -r '.redacted_text')

echo "Call ID: $CALL_ID"
echo "Trace ID: $TRACE_ID"

# 3. Clasificar con triage
TRIAGE_RESPONSE=$(curl -s -X POST http://localhost:8002/triage \
  -H "Content-Type: application/json" \
  -d "{
    \"transcript\": \"$REDACTED\",
    \"call_id\": \"$CALL_ID\",
    \"trace_id\": \"$TRACE_ID\",
    \"consent\": true,
    \"location_hint\": \"Colonia Centro\"
  }")

# 4. Extraer resultados
RISK_LEVEL=$(echo $TRIAGE_RESPONSE | jq -r '.risk_level')
BRANCH=$(echo $TRIAGE_RESPONSE | jq -r '.branch')
CATEGORY=$(echo $TRIAGE_RESPONSE | jq -r '.case_category')
HUMAN_REQ=$(echo $TRIAGE_RESPONSE | jq -r '.human_required')
P0_SIGNALS=$(echo $TRIAGE_RESPONSE | jq -c '.p0_signals')

echo "Risk Level: $RISK_LEVEL"
echo "Branch: $BRANCH"
echo "Human Required: $HUMAN_REQ"
echo "P0 Signals: $P0_SIGNALS"

# 5. Registrar en analytics
ANALYTICS_RESPONSE=$(curl -s -X POST http://localhost:8003/incidents \
  -H "Content-Type: application/json" \
  -d "{
    \"call_id\": \"$CALL_ID\",
    \"trace_id\": \"$TRACE_ID\",
    \"risk_level\": $RISK_LEVEL,
    \"branch\": \"$BRANCH\",
    \"case_category\": \"$CATEGORY\",
    \"human_required\": $HUMAN_REQ,
    \"p0_signals\": $P0_SIGNALS,
    \"location_hint\": \"Colonia Centro\"
  }")

INCIDENT_ID=$(echo $ANALYTICS_RESPONSE | jq -r '.incident_id')
echo "Incident ID: $INCIDENT_ID"

# 6. Ver métricas
curl -s http://localhost:8003/analytics/summary | jq '{
  total_incidents,
  by_branch,
  human_required_count,
  p0_signals_count
}'
```

**Resultado Esperado:**
```
Call ID: 123e4567-e89b-12d3-a456-426614174000
Trace ID: 223e4567-e89b-12d3-a456-426614174000
Risk Level: 8
Branch: critical
Human Required: true
P0 Signals: ["sangrado grave","maltrato infantil"]
Incident ID: 323e4567-e89b-12d3-a456-426614174000
{
  "total_incidents": 51,
  "by_branch": {
    "low": 30,
    "mid": 6,
    "critical": 15
  },
  "human_required_count": 21,
  "p0_signals_count": 15
}
```

---

## Notas Importantes

### Privacidad

- ❌ **NO enviar PII real** en ningún endpoint
- ✅ Usar datos sintéticos para pruebas
- ✅ El sistema redacta automáticamente, pero mejor no enviar PII

### Datos Sintéticos

**Ejemplos de datos seguros para pruebas:**
```json
{
  "transcript": "Hay un bache en la calle principal",
  "location_hint": "Colonia Centro"
}
```

**NO usar:**
```json
{
  "transcript": "Mi nombre es Juan Pérez Gómez, INE 1234567890, vivo en Calle Real 123 Int 4B",
  "location_hint": "Calle Real 123, Colonia Centro, CP 06000"
}
```

### Limitaciones

- Las predicciones son **mock/demo**, no basadas en ML real
- El sistema es **local**, no expuesto a internet
- No usar para **emergencias reales**

---

**Versión:** 1.0.0  
**Fecha:** 2026-06-06  
**Autor:** Bob  
**Propósito:** Demo educativa - Hackathon