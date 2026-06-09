# n8n Workflow - CENTINELA_CDMX_IA

## Descripción General

Este workflow orquesta el flujo completo de procesamiento de llamadas 911 simuladas a través de los tres microservicios:

1. **api-ingest**: Redacción de PII y almacenamiento raw
2. **api-triage**: Clasificación de riesgo y detección de señales P0
3. **api-analytics**: Almacenamiento de incidentes y métricas

## Arquitectura del Workflow

```
Webhook POST /911-call
    ↓
Validate Payload (transcript required)
    ↓ (valid)                    ↓ (invalid)
Call API Ingest              Error Invalid Payload
    ↓                              ↓
Call API Triage              Respond Error (400)
    ↓
Call API Analytics
    ↓
Consolidate Response
    ↓
Respond Success (200)
```

## Nodos del Workflow

### 1. Webhook 911 Call
- **Tipo**: Webhook
- **Método**: POST
- **Path**: `/webhook/911-call`
- **Modo**: Response Node
- **CORS**: Habilitado para localhost:3000 y localhost:5678

**Payload esperado:**
```json
{
  "transcript": "string (required)",
  "metadata": {
    "source": "string (optional)",
    "timestamp": "ISO 8601 (optional)"
  },
  "location_hint": "string (optional)",
  "solid_consent": "boolean (optional, default: true)"
}
```

### 2. Validate Payload
- **Tipo**: IF condition
- **Validación**: `transcript` no vacío
- **Salidas**: 
  - True → Continúa a API Ingest
  - False → Error Invalid Payload

### 3. Call API Ingest
- **Tipo**: HTTP Request
- **URL**: `http://api-ingest:8001/raw-conversations`
- **Método**: POST
- **Timeout**: 10 segundos
- **Reintentos**: 2 (con 1 segundo entre intentos)

**Body enviado:**
```json
{
  "transcript": "{{ $json.body.transcript }}",
  "metadata": "{{ $json.body.metadata || defaults }}"
}
```

**Respuesta esperada:**
```json
{
  "call_id": "uuid",
  "trace_id": "uuid",
  "redacted_text": "string",
  "stored_at": "ISO 8601"
}
```

### 4. Call API Triage
- **Tipo**: HTTP Request
- **URL**: `http://api-triage:8002/triage`
- **Método**: POST
- **Timeout**: 15 segundos
- **Reintentos**: 2

**Body enviado:**
```json
{
  "transcript": "{{ $json.redacted_text }}",
  "call_id": "{{ $json.call_id }}",
  "trace_id": "{{ $json.trace_id }}",
  "consent": "{{ solid_consent === true }}",
  "location_hint": "{{ location_hint || 'Unknown' }}"
}
```

**Respuesta esperada:**
```json
{
  "call_id": "uuid",
  "trace_id": "uuid",
  "risk_level": 1-10,
  "branch": "low|mid|critical",
  "case_category": "string",
  "human_required": boolean,
  "p0_signals": ["string"],
  "primary_authority": "string",
  "support_authorities": ["string"],
  "public_stage_phrase": "string",
  "rationale_public": "string"
}
```

### 5. Call API Analytics
- **Tipo**: HTTP Request
- **URL**: `http://api-analytics:8003/incidents`
- **Método**: POST
- **Timeout**: 10 segundos
- **Reintentos**: 2

**Body enviado:**
```json
{
  "call_id": "{{ $json.call_id }}",
  "trace_id": "{{ $json.trace_id }}",
  "risk_level": "{{ $json.risk_level }}",
  "branch": "{{ $json.branch }}",
  "case_category": "{{ $json.case_category }}",
  "human_required": "{{ $json.human_required }}",
  "p0_signals": "{{ $json.p0_signals }}",
  "location_hint": "{{ location_hint || 'Unknown' }}"
}
```

**Respuesta esperada:**
```json
{
  "incident_id": "uuid",
  "stored_at": "ISO 8601",
  "status": "stored"
}
```

### 6. Consolidate Response
- **Tipo**: Code (JavaScript)
- **Función**: Combina respuestas de los 3 servicios en un JSON consolidado

**Salida:**
```json
{
  "success": true,
  "call_id": "uuid",
  "trace_id": "uuid",
  "risk_level": 1-10,
  "branch": "low|mid|critical",
  "case_category": "string",
  "human_required": boolean,
  "p0_signals": ["string"],
  "primary_authority": "string",
  "support_authorities": ["string"],
  "incident_id": "uuid",
  "status": "processed",
  "public_stage_phrase": "string",
  "rationale_public": "string",
  "processed_at": "ISO 8601"
}
```

### 7. Respond Success
- **Tipo**: Respond to Webhook
- **Código**: 200
- **Formato**: JSON

### 8. Error Invalid Payload
- **Tipo**: Code (JavaScript)
- **Función**: Genera mensaje de error para payload inválido

### 9. Respond Error
- **Tipo**: Respond to Webhook
- **Código**: 400
- **Formato**: JSON

## Importación del Workflow

### Paso 1: Acceder a n8n
```bash
# Asegurarse de que n8n está corriendo
docker ps | grep centinela-n8n

# Acceder a la interfaz web
open http://localhost:5678
```

### Paso 2: Importar Workflow
1. En n8n, hacer clic en el menú superior derecho
2. Seleccionar "Import from File"
3. Navegar a: `n8n/workflows/centinela-cdmx-ia-main.json`
4. Hacer clic en "Import"

### Paso 3: Activar Workflow
1. Abrir el workflow importado
2. Hacer clic en el botón "Active" en la esquina superior derecha
3. Verificar que el estado cambie a "Active"

### Paso 4: Obtener URL del Webhook
1. Hacer clic en el nodo "Webhook 911 Call"
2. Copiar la URL del webhook (debería ser: `http://localhost:5678/webhook/911-call`)

## Pruebas del Workflow

### Test 1: Caso de Bajo Riesgo
```bash
curl -X POST http://localhost:5678/webhook/911-call \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Hola, quiero reportar un bache en la calle Reforma. Mi teléfono es 5512345678.",
    "metadata": {
      "source": "test_manual",
      "timestamp": "2026-06-06T12:00:00Z"
    },
    "location_hint": "Colonia Centro"
  }'
```

**Resultado esperado:**
- `risk_level`: 1-4
- `branch`: "low"
- `human_required`: false
- `p0_signals`: []

### Test 2: Caso de Validación (Nivel 5)
```bash
curl -X POST http://localhost:5678/webhook/911-call \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Hay un accidente de tránsito con varios carros chocados. No veo heridos graves.",
    "location_hint": "Insurgentes con Reforma"
  }'
```

**Resultado esperado:**
- `risk_level`: 5
- `branch`: "mid"
- `human_required`: true

### Test 3: Caso Crítico P0
```bash
curl -X POST http://localhost:5678/webhook/911-call \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "¡Auxilio! Hay un niño sangrando mucho de la cabeza. Tiene 8 años y se cayó de las escaleras.",
    "location_hint": "Calle Madero 45, Colonia Centro"
  }'
```

**Resultado esperado:**
- `risk_level`: 8-10
- `branch`: "critical"
- `human_required`: true
- `p0_signals`: ["sangrado grave", "maltrato infantil"]
- `best_interest_child`: true

### Test 4: Payload Inválido
```bash
curl -X POST http://localhost:5678/webhook/911-call \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "source": "test"
    }
  }'
```

**Resultado esperado:**
- HTTP 400
- `success`: false
- `error`: "Invalid payload"

## Verificación de Datos

### Verificar en PostgreSQL
```bash
# Contar conversaciones raw
docker exec centinela-db psql -U emergency_user -d centinela_demo \
  -c "SELECT COUNT(*) FROM raw.conversations;"

# Contar resultados de triage
docker exec centinela-db psql -U emergency_user -d centinela_demo \
  -c "SELECT COUNT(*) FROM core.triage_results;"

# Contar incidentes
docker exec centinela-db psql -U emergency_user -d centinela_demo \
  -c "SELECT COUNT(*) FROM analytics.incidents;"

# Ver últimos 5 incidentes
docker exec centinela-db psql -U emergency_user -d centinela_demo \
  -c "SELECT incident_id, risk_level, branch, case_category, human_required 
      FROM analytics.incidents 
      ORDER BY processed_at DESC 
      LIMIT 5;"
```

### Verificar Analytics
```bash
# Summary
curl http://localhost:8003/analytics/summary | jq

# Predictions
curl http://localhost:8003/analytics/predictions | jq
```

## Manejo de Errores

### Errores Comunes

1. **"Webhook not found"**
   - Verificar que el workflow esté activo
   - Verificar la URL del webhook

2. **"Service timeout"**
   - Verificar que los 3 servicios estén corriendo: `docker ps`
   - Revisar logs: `./scripts/03_logs.sh api-ingest`

3. **"Database connection failed"**
   - Verificar PostgreSQL: `docker ps | grep centinela-db`
   - Revisar logs de DB: `./scripts/03_logs.sh postgres`

4. **"Invalid JSON response"**
   - Verificar health de servicios:
     ```bash
     curl http://localhost:8001/health
     curl http://localhost:8002/health
     curl http://localhost:8003/health
     ```

### Logs del Workflow

Para ver logs de ejecución en n8n:
1. Ir a "Executions" en el menú lateral
2. Hacer clic en una ejecución específica
3. Ver el flujo de datos entre nodos
4. Revisar errores en nodos fallidos

## Seguridad y Privacidad

### Datos NO Almacenados en n8n
- ❌ Transcript original (solo redacted_text)
- ❌ PII sin redactar
- ❌ Datos sensibles en logs

### Datos Almacenados
- ✅ call_id y trace_id (UUIDs)
- ✅ Texto redactado
- ✅ Clasificaciones y métricas
- ✅ Metadatos no sensibles

### Recomendaciones
1. No habilitar "Save Execution Data" en producción
2. Usar autenticación en webhook (Basic Auth)
3. Limitar CORS a dominios específicos
4. Rotar credenciales regularmente

## Integración con Lovable

El webhook puede ser consumido directamente desde Lovable:

```javascript
// Ejemplo de llamada desde Lovable
const response = await fetch('http://localhost:5678/webhook/911-call', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    transcript: userInput,
    location_hint: userLocation,
    solid_consent: false  // OFF por defecto — activar solo con autorización explícita
  })
});

const result = await response.json();
console.log('Risk Level:', result.risk_level);
console.log('Branch:', result.branch);
console.log('Human Required:', result.human_required);
```

## Monitoreo

### Métricas Clave
- Total de llamadas procesadas
- Tasa de éxito/error
- Tiempo promedio de procesamiento
- Distribución de niveles de riesgo
- Casos con human_required=true

### Dashboard en n8n
1. Ir a "Executions"
2. Filtrar por workflow "CENTINELA_CDMX_IA - Main"
3. Ver estadísticas de ejecución

## Troubleshooting

### El workflow no se activa
```bash
# Verificar que n8n está corriendo
docker ps | grep n8n

# Reiniciar n8n si es necesario
docker restart centinela-n8n

# Ver logs de n8n
docker logs centinela-n8n --tail 50
```

### Respuestas lentas
- Aumentar timeouts en nodos HTTP Request
- Verificar recursos del sistema: `docker stats`
- Revisar logs de servicios individuales

### Datos no se guardan
- Verificar conexión a PostgreSQL
- Revisar permisos de usuario de DB
- Verificar schemas y tablas existen

## Próximos Pasos

1. Agregar autenticación al webhook
2. Implementar rate limiting
3. Agregar notificaciones para casos críticos
4. Crear dashboard de monitoreo en tiempo real
5. Implementar webhooks de salida para sistemas externos

---

**Versión:** 1.0.0  
**Última actualización:** 2026-06-06  
**Autor:** Bob