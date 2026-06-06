# Gate 2 - Corrección de Errores

## Problemas Detectados

### Problema 1: api-ingest
**Error:** `can't adapt type 'dict'` en POST /raw-conversations

**Causa:** psycopg2 no puede adaptar automáticamente dict de Python a columnas JSONB de PostgreSQL.

**Solución Aplicada:** Importar y usar `Json` de `psycopg2.extras` para envolver los diccionarios.

### Problema 2: api-triage
**Error:** `can't adapt type 'dict'` en POST /triage

**Causa:** Mismo problema - dicts insertados directamente en columnas JSONB.

**Solución Aplicada:** Mismo patrón que api-ingest + mejor manejo de errores.

---

## Cambios Realizados

### 1. services/api-ingest/app.py

1. **Importación agregada:**
```python
from psycopg2.extras import RealDictCursor, Json
```

2. **Corrección en INSERT:**
```python
cursor.execute("""
    INSERT INTO raw.conversations 
    (call_id, trace_id, original_text, redacted_text, redaction_flags, metadata)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING created_at
""", (
    call_id,
    trace_id,
    '[NOT_STORED_PRIVACY_BY_DESIGN]',  # Privacy by design
    redacted_text,
    Json(redaction_summary),  # ✅ Envuelto con Json()
    Json(metadata)  # ✅ Envuelto con Json()
))
```

3. **Mejora de privacidad:**
- Cambio de `'[ORIGINAL-NO-ALMACENADO]'` a `'[NOT_STORED_PRIVACY_BY_DESIGN]'`
- Más explícito sobre el diseño de privacidad

### 2. services/api-triage/app.py

1. **Importación agregada:**
```python
from psycopg2.extras import RealDictCursor, Json
```

2. **Corrección en INSERT:**
```python
cursor.execute("""
    INSERT INTO core.triage_results
    (call_id, trace_id, risk_level, branch, priority_class, case_category,
     protected_group_flags, best_interest_child, human_required,
     primary_authority, support_authorities, public_stage_phrase,
     rationale_public, trust_flags, p0_signals, keywords_detected)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    request.call_id,
    trace_id,
    risk_level,
    branch,
    priority_class,
    case_category,
    Json(protected_group_flags.dict()),  # ✅ Envuelto con Json()
    best_interest_child,
    human_required,
    primary_authority,
    support_authorities,  # TEXT[] - no necesita Json()
    public_phrase,
    rationale_public,
    Json({"confidence_score": 0.85, "ambiguity_detected": False}),  # ✅ Envuelto
    p0_signals,  # TEXT[] - no necesita Json()
    Json(keywords_detected)  # ✅ Envuelto con Json()
))
```

3. **Mejor manejo de errores:**
```python
except psycopg2.IntegrityError as e:
    # Foreign key violation - call_id doesn't exist
    logger.error(f"Integrity error in triage: call_id may not exist")
    raise HTTPException(
        status_code=422,
        detail=f"Invalid call_id: {request.call_id}. Call must be ingested first."
    )
except Exception as e:
    logger.error(f"Error in triage: {type(e).__name__}")
    raise HTTPException(status_code=500, detail="Internal server error during triage")
```

**Nota:** No se envuelven `support_authorities` ni `p0_signals` porque son TEXT[] (arrays de texto), no JSONB.

---

## Comandos de Reconstrucción

### 1. Reconstruir api-ingest
```bash
cd /home/lubo/Documents/CENTINELA_CDMX_IA

# Reconstruir la imagen
docker compose --profile services build api-ingest

# Reiniciar el servicio
docker compose --profile services up -d api-ingest

# Verificar que está corriendo
docker ps | grep api-ingest

# Ver logs
docker compose logs -f api-ingest
```

### 2. Reconstruir api-triage
```bash
# Reconstruir la imagen
docker compose --profile services build api-triage

# Reiniciar el servicio
docker compose --profile services up -d api-triage

# Verificar que está corriendo
docker ps | grep api-triage

# Ver logs
docker compose logs -f api-triage
```

### 3. Esperar a que estén healthy
```bash
# Esperar ~30 segundos
sleep 30

# Verificar health de ambos
curl http://localhost:8001/health | jq '.'
curl http://localhost:8002/health | jq '.'
```

---

## Comandos de Prueba

### Test 1: POST /raw-conversations (Caso Completo)
```bash
curl -v -X POST http://localhost:8001/raw-conversations \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Me llamo Juan Pérez, mi teléfono es 5512345678 y mi correo es prueba@test.com. Quiero reportar un bache en Reforma.",
    "metadata": {
      "source": "test",
      "caller_alias": "anonimo",
      "location_hint": "Cuauhtémoc",
      "solid_consent": true
    }
  }' | jq '.'
```

**Respuesta Esperada:**
```json
{
  "call_id": "uuid-generado",
  "trace_id": "uuid-generado",
  "redacted_text": "Me llamo [NOMBRE-REDACTADO], mi teléfono es [TELÉFONO-REDACTADO] y mi correo es [EMAIL-REDACTADO]. Quiero reportar un bache en [DIRECCIÓN-REDACTADA].",
  "redaction_summary": {
    "phones_redacted": 1,
    "emails_redacted": 1,
    "names_redacted": 1,
    "addresses_redacted": 1
  },
  "created_at": "2026-06-06T..."
}
```

**Validaciones:**
- ✅ HTTP 200 o 201
- ✅ Teléfono redactado: `[TELÉFONO-REDACTADO]`
- ✅ Email redactado: `[EMAIL-REDACTADO]`
- ✅ Nombre redactado: `[NOMBRE-REDACTADO]`
- ✅ Dirección redactada: `[DIRECCIÓN-REDACTADA]`
- ✅ call_id y trace_id presentes
- ✅ redaction_summary con contadores

### Test 2: Verificar en Base de Datos
```bash
docker exec -it emergency-db psql -U emergency_user -d emergency_demo -c "
SELECT 
    call_id,
    trace_id,
    original_text,
    LEFT(redacted_text, 50) as redacted_preview,
    redaction_flags,
    metadata
FROM raw.conversations
ORDER BY created_at DESC
LIMIT 1;
"
```

**Validaciones:**
- ✅ original_text = `[NOT_STORED_PRIVACY_BY_DESIGN]`
- ✅ redacted_text contiene texto redactado
- ✅ redaction_flags es JSONB válido
- ✅ metadata es JSONB válido

### Test 3: GET /raw-conversations
```bash
curl http://localhost:8001/raw-conversations?limit=5 | jq '.'
```

**Respuesta Esperada:**
```json
{
  "total": 1,
  "items": [
    {
      "call_id": "uuid",
      "trace_id": "uuid",
      "redacted_text": "Me llamo [NOMBRE-REDACTADO]...",
      "created_at": "2026-06-06T..."
    }
  ]
}
```

### Test 4: POST /triage (Con call_id existente)
```bash
# Primero crear una conversación
INGEST_RESPONSE=$(curl -s -X POST http://localhost:8001/raw-conversations \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Hay un incendio en mi edificio, necesito ayuda urgente",
    "metadata": {"source": "test"}
  }')

echo "$INGEST_RESPONSE" | jq '.'

# Extraer call_id
CALL_ID=$(echo "$INGEST_RESPONSE" | jq -r '.call_id')
echo "Call ID: $CALL_ID"

# Ahora hacer triage
curl -s -X POST http://localhost:8002/triage \
  -H "Content-Type: application/json" \
  -d "{
    \"transcript\": \"Hay un incendio en mi edificio, necesito ayuda urgente\",
    \"call_id\": \"$CALL_ID\",
    \"consent\": true,
    \"location_hint\": \"Colonia Centro\"
  }" | jq '.'
```

**Respuesta Esperada:**
```json
{
  "call_id": "uuid",
  "trace_id": "uuid-generado",
  "risk_level": 8-9,
  "branch": "critical",
  "priority_class": "critical",
  "case_category": "protection_civil",
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
  "p0_signals": ["incendio"],
  "keywords_detected": {
    "protection_civil": ["incendio"]
  }
}
```

**Validaciones:**
- ✅ HTTP 200
- ✅ risk_level >= 8 (por señal P0 "incendio")
- ✅ branch = "critical"
- ✅ human_required = true
- ✅ p0_signals contiene "incendio"
- ✅ primary_authority = "Protección Civil"

### Test 5: Verificar en Base de Datos
```bash
docker exec -it emergency-db psql -U emergency_user -d emergency_demo -c "
SELECT
    call_id,
    risk_level,
    branch,
    case_category,
    protected_group_flags,
    trust_flags,
    p0_signals,
    keywords_detected
FROM core.triage_results
ORDER BY created_at DESC
LIMIT 1;
"
```

**Debe mostrar:**
- ✅ protected_group_flags como JSONB válido
- ✅ trust_flags como JSONB válido
- ✅ keywords_detected como JSONB válido
- ✅ p0_signals como TEXT[] válido

### Test 6: Flujo Completo (Ingest + Triage + Analytics)
```bash
# 1. Ingest
RESPONSE=$(curl -s -X POST http://localhost:8001/raw-conversations \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "¡Auxilio! Hay un niño sangrando mucho. Se cayó de las escaleras.",
    "metadata": {"source": "test"}
  }')

echo "$RESPONSE" | jq '.'

# Extraer call_id
CALL_ID=$(echo "$RESPONSE" | jq -r '.call_id')
echo "Call ID: $CALL_ID"

# 2. Triage
TRIAGE_RESPONSE=$(curl -s -X POST http://localhost:8002/triage \
  -H "Content-Type: application/json" \
  -d "{
    \"transcript\": \"¡Auxilio! Hay un niño sangrando mucho. Se cayó de las escaleras.\",
    \"call_id\": \"$CALL_ID\",
    \"consent\": true,
    \"location_hint\": \"Colonia Centro\"
  }")

echo "$TRIAGE_RESPONSE" | jq '.'

# Extraer datos para analytics
TRACE_ID=$(echo "$TRIAGE_RESPONSE" | jq -r '.trace_id')
RISK_LEVEL=$(echo "$TRIAGE_RESPONSE" | jq -r '.risk_level')
BRANCH=$(echo "$TRIAGE_RESPONSE" | jq -r '.branch')
CATEGORY=$(echo "$TRIAGE_RESPONSE" | jq -r '.case_category')
HUMAN_REQ=$(echo "$TRIAGE_RESPONSE" | jq -r '.human_required')
P0_SIGNALS=$(echo "$TRIAGE_RESPONSE" | jq -c '.p0_signals')

# 3. Analytics
curl -s -X POST http://localhost:8003/incidents \
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
  }" | jq '.'

# 4. Verificar summary
curl -s http://localhost:8003/analytics/summary | jq '.'
```

**Validaciones del Flujo:**
- ✅ Ingest devuelve call_id y texto redactado
- ✅ Triage detecta P0 (sangrado grave)
- ✅ Triage detecta NNA (niño)
- ✅ risk_level >= 8
- ✅ branch = "critical"
- ✅ human_required = true
- ✅ best_interest_child = true
- ✅ Analytics almacena incidente
- ✅ Summary refleja el nuevo incidente

### Test 7: Script de Test Completo
```bash
./scripts/04_test_environment.sh all
```

**Debe pasar todos los tests:**
- ✅ Docker y servicios corriendo
- ✅ Base de datos conectada
- ✅ Schemas y tablas creadas
- ✅ n8n accesible
- ✅ Health checks de APIs
- ✅ POST /raw-conversations funcional
- ✅ GET /raw-conversations funcional
- ✅ POST /triage funcional
- ✅ POST /incidents funcional
- ✅ GET /analytics/summary funcional
- ✅ GET /analytics/predictions funcional

---

## Verificación de Privacidad

### Verificar que NO se guarda texto original
```bash
docker exec -it emergency-db psql -U emergency_user -d emergency_demo -c "
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE original_text = '[NOT_STORED_PRIVACY_BY_DESIGN]') as privacy_compliant,
    COUNT(*) FILTER (WHERE original_text != '[NOT_STORED_PRIVACY_BY_DESIGN]') as privacy_violations
FROM raw.conversations;
"
```

**Resultado Esperado:**
```
 total | privacy_compliant | privacy_violations 
-------+-------------------+--------------------
     3 |                 3 |                  0
```

### Verificar redacción de PII
```bash
docker exec -it emergency-db psql -U emergency_user -d emergency_demo -c "
SELECT 
    redacted_text,
    redaction_flags
FROM raw.conversations
WHERE redacted_text LIKE '%REDACTADO%'
LIMIT 3;
"
```

**Debe mostrar:**
- Textos con `[TELÉFONO-REDACTADO]`
- Textos con `[EMAIL-REDACTADO]`
- Textos con `[NOMBRE-REDACTADO]`
- Textos con `[DIRECCIÓN-REDACTADA]`

---

## Troubleshooting

### Error: "Connection refused"
```bash
# Verificar que el servicio está corriendo
docker ps | grep api-ingest

# Si no está corriendo, iniciarlo
docker compose --profile services up -d api-ingest

# Ver logs
docker compose logs api-ingest
```

### Error: "Database connection failed"
```bash
# Verificar PostgreSQL
docker ps | grep emergency-db

# Probar conexión
docker exec -it emergency-db psql -U emergency_user -d emergency_demo -c "SELECT 1;"

# Si falla, reiniciar PostgreSQL
docker compose restart postgres
```

### Error: "can't adapt type 'dict'" persiste en api-triage
```bash
# Verificar que la imagen se reconstruyó
docker images | grep api-triage

# Forzar reconstrucción sin cache
docker compose --profile services build --no-cache api-triage
docker compose --profile services up -d api-triage
```

### Error: "Invalid call_id" en triage
```bash
# Esto es correcto - primero debes crear la conversación con ingest
# Crear conversación primero
CALL_ID=$(curl -s -X POST http://localhost:8001/raw-conversations \
  -H "Content-Type: application/json" \
  -d '{"transcript":"test","metadata":{}}' | jq -r '.call_id')

# Luego usar ese call_id en triage
curl -X POST http://localhost:8002/triage \
  -H "Content-Type: application/json" \
  -d "{\"transcript\":\"test\",\"call_id\":\"$CALL_ID\",\"consent\":true}"
```

### Ver logs en tiempo real
```bash
# api-ingest
docker compose logs -f api-ingest

# api-triage
docker compose logs -f api-triage

# Todos los servicios
docker compose logs -f
```

### Reconstruir ambos servicios
```bash
# Reconstruir ambos
docker compose --profile services build api-ingest api-triage

# Reiniciar ambos
docker compose --profile services up -d api-ingest api-triage

# Verificar health
sleep 30
curl http://localhost:8001/health | jq '.status'
curl http://localhost:8002/health | jq '.status'
```

---

## Criterios de Aceptación Gate 2

### api-ingest
✅ POST /raw-conversations devuelve HTTP 200 o 201
✅ Respuesta incluye call_id, trace_id y redacted_text
✅ Respuesta NO incluye teléfono, correo o nombre original
✅ raw.conversations recibe registro con JSONB válido
✅ original_text = '[NOT_STORED_PRIVACY_BY_DESIGN]'
✅ redaction_flags y metadata son JSONB válidos

### api-triage
✅ POST /triage devuelve HTTP 200
✅ Se guarda registro en core.triage_results
✅ protected_group_flags es JSONB válido
✅ trust_flags es JSONB válido
✅ keywords_detected es JSONB válido
✅ p0_signals es TEXT[] válido
✅ support_authorities es TEXT[] válido
✅ Error 422 si call_id no existe (no 500)

### Integración
✅ ./scripts/04_test_environment.sh all pasa todos los tests
✅ Flujo completo Ingest → Triage → Analytics funciona
✅ Flujo completo Ingest → Triage → Analytics funciona

---

## Siguiente Paso

Una vez que todos los tests pasen:
```bash
# Ejecutar seed de datos demo
./scripts/05_seed_demo_data.sh

# Verificar métricas
curl http://localhost:8003/analytics/summary | jq '.'
```

**Estado:** Listo para Gate 3 - Workflow n8n