# Gate 3 - n8n Workflow Delivery

## Fecha
2026-06-06

## Archivos Creados

### 1. ✅ Workflow n8n JSON
**Archivo:** `n8n/workflows/centinela-cdmx-ia-main.json`

**Características:**
- Webhook POST `/webhook/911-call`
- Validación de payload (transcript requerido)
- Llamadas HTTP a los 3 microservicios en secuencia
- Manejo de errores con nodos dedicados
- Timeouts configurados (10-15 segundos)
- Reintentos automáticos (máximo 2)
- Respuesta consolidada en JSON
- No expone PII en logs

**Nodos del Workflow:**
1. Webhook 911 Call (entrada)
2. Validate Payload (validación)
3. Call API Ingest (redacción + almacenamiento)
4. Call API Triage (clasificación + P0)
5. Call API Analytics (métricas)
6. Consolidate Response (consolidación)
7. Respond Success (salida exitosa)
8. Error Invalid Payload (error de validación)
9. Respond Error (salida de error)
10. Error Service Failure (error de servicio)

### 2. ✅ Documentación del Workflow
**Archivo:** `docs/n8n_workflow.md`

**Contenido:**
- Descripción general del flujo
- Arquitectura visual del workflow
- Documentación detallada de cada nodo
- Instrucciones de importación paso a paso
- 4 casos de prueba con curl
- Verificación de datos en PostgreSQL
- Troubleshooting común
- Integración con Lovable
- Métricas y monitoreo

### 3. ✅ Script de Prueba de Webhook
**Archivo:** `scripts/06_test_n8n_webhook.sh`

**Funcionalidad:**
- Verifica disponibilidad de n8n
- Ejecuta 3 escenarios de prueba
- Valida rangos de risk_level esperados
- Verifica datos en PostgreSQL
- Muestra analytics summary
- Formato de salida colorizado

## Flujo del Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Webhook POST /911-call                      │
│                  (transcript, metadata, location)               │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
                    ┌────────────────┐
                    │ Validate       │
                    │ Payload        │
                    └───┬────────┬───┘
                        ↓        ↓ (invalid)
                    (valid)   Error 400
                        ↓
            ┌───────────────────────┐
            │ Call API Ingest       │
            │ POST /raw-conversations│
            │ → call_id, trace_id   │
            └───────────┬───────────┘
                        ↓
            ┌───────────────────────┐
            │ Call API Triage       │
            │ POST /triage          │
            │ → risk, branch, P0    │
            └───────────┬───────────┘
                        ↓
            ┌───────────────────────┐
            │ Call API Analytics    │
            │ POST /incidents       │
            │ → incident_id         │
            └───────────┬───────────┘
                        ↓
            ┌───────────────────────┐
            │ Consolidate Response  │
            │ (JavaScript)          │
            └───────────┬───────────┘
                        ↓
            ┌───────────────────────┐
            │ Respond Success       │
            │ HTTP 200 + JSON       │
            └───────────────────────┘
```

## Importación del Workflow

### Paso 1: Acceder a n8n
```bash
# Verificar que n8n está corriendo
docker ps | grep centinela-n8n

# Acceder a la interfaz
open http://localhost:5678
```

### Paso 2: Importar
1. Menú superior derecho → "Import from File"
2. Seleccionar: `n8n/workflows/centinela-cdmx-ia-main.json`
3. Click "Import"

### Paso 3: Activar
1. Abrir el workflow importado
2. Click en "Active" (esquina superior derecha)
3. Verificar estado "Active"

### Paso 4: Obtener URL
- URL del webhook: `http://localhost:5678/webhook/911-call`

## Pruebas de Validación

### Comando Rápido
```bash
# Ejecutar script de prueba
./scripts/06_test_n8n_webhook.sh
```

### Prueba Manual - Caso Bajo Riesgo
```bash
curl -X POST http://localhost:5678/webhook/911-call \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Quiero reportar un bache en la calle Reforma.",
    "location_hint": "Colonia Centro"
  }'
```

**Resultado esperado:**
```json
{
  "success": true,
  "call_id": "uuid",
  "trace_id": "uuid",
  "risk_level": 1-4,
  "branch": "low",
  "case_category": "public_services",
  "human_required": false,
  "p0_signals": [],
  "primary_authority": "C5",
  "support_authorities": [],
  "incident_id": "uuid",
  "status": "processed",
  "public_stage_phrase": "...",
  "rationale_public": "...",
  "processed_at": "2026-06-06T..."
}
```

### Prueba Manual - Caso Crítico P0
```bash
curl -X POST http://localhost:5678/webhook/911-call \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "¡Auxilio! Hay un niño sangrando mucho de la cabeza.",
    "location_hint": "Calle Madero 45"
  }'
```

**Resultado esperado:**
```json
{
  "success": true,
  "risk_level": 8-10,
  "branch": "critical",
  "human_required": true,
  "p0_signals": ["sangrado grave", "maltrato infantil"],
  "primary_authority": "ERUM",
  "support_authorities": ["Cruz Roja", "Protección Civil"],
  ...
}
```

### Prueba Manual - Payload Inválido
```bash
curl -X POST http://localhost:5678/webhook/911-call \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {"source": "test"}
  }'
```

**Resultado esperado:**
```json
{
  "success": false,
  "error": "Invalid payload",
  "message": "Field transcript is required",
  "received": {...}
}
```

## Verificación de Datos

### Verificar en PostgreSQL
```bash
# Contar registros
docker exec centinela-db psql -U emergency_user -d centinela_demo -c "
SELECT 
  (SELECT COUNT(*) FROM raw.conversations) as raw,
  (SELECT COUNT(*) FROM core.triage_results) as triage,
  (SELECT COUNT(*) FROM analytics.incidents) as incidents;
"

# Ver últimos incidentes
docker exec centinela-db psql -U emergency_user -d centinela_demo -c "
SELECT 
  LEFT(incident_id::text, 8) as id,
  risk_level,
  branch,
  case_category,
  human_required
FROM analytics.incidents
ORDER BY processed_at DESC
LIMIT 5;
"
```

### Verificar Analytics
```bash
# Summary
curl http://localhost:8003/analytics/summary | jq

# Predictions
curl http://localhost:8003/analytics/predictions | jq
```

## Características de Seguridad

### ✅ Implementadas
- Validación de payload antes de procesar
- Timeouts en todas las llamadas HTTP
- Reintentos automáticos (máximo 2)
- No se almacena transcript original en n8n
- Se usa redacted_text después de ingest
- Respuestas de error no exponen detalles internos
- CORS configurado para dominios específicos

### 🔒 Recomendaciones para Producción
- Habilitar autenticación en webhook (Basic Auth)
- Implementar rate limiting
- Usar HTTPS en lugar de HTTP
- Rotar credenciales regularmente
- No habilitar "Save Execution Data"
- Implementar logging seguro

## Integración con Lovable

El webhook está listo para ser consumido desde Lovable:

```javascript
// Ejemplo de integración
async function process911Call(transcript, location) {
  try {
    const response = await fetch('http://localhost:5678/webhook/911-call', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        transcript: transcript,
        location_hint: location,
        solid_consent: true,
        metadata: {
          source: 'lovable_dashboard',
          timestamp: new Date().toISOString()
        }
      })
    });

    const result = await response.json();
    
    if (result.success) {
      // Mostrar resultado en dashboard
      displayRiskLevel(result.risk_level);
      displayBranch(result.branch);
      displayAuthorities(result.primary_authority, result.support_authorities);
      
      if (result.human_required) {
        alertOperator(result);
      }
    } else {
      handleError(result.error);
    }
  } catch (error) {
    console.error('Error calling 911 webhook:', error);
  }
}
```

## Monitoreo en n8n

### Ver Ejecuciones
1. Ir a "Executions" en el menú lateral de n8n
2. Filtrar por workflow "CENTINELA_CDMX_IA - Main"
3. Ver detalles de cada ejecución
4. Revisar flujo de datos entre nodos
5. Identificar errores en nodos fallidos

### Métricas Clave
- Total de ejecuciones
- Tasa de éxito/error
- Tiempo promedio de ejecución
- Distribución de risk_level
- Casos con human_required=true

## Troubleshooting

### Problema: "Webhook not found"
**Solución:**
```bash
# Verificar que el workflow está activo
# En n8n UI: verificar botón "Active" está en verde

# Reiniciar n8n si es necesario
docker restart centinela-n8n
```

### Problema: "Service timeout"
**Solución:**
```bash
# Verificar que todos los servicios están corriendo
docker ps

# Revisar logs de servicios
./scripts/03_logs.sh api-ingest
./scripts/03_logs.sh api-triage
./scripts/03_logs.sh api-analytics
```

### Problema: "Database connection failed"
**Solución:**
```bash
# Verificar PostgreSQL
docker ps | grep centinela-db

# Revisar logs de DB
./scripts/03_logs.sh postgres

# Verificar conexión
docker exec centinela-db psql -U emergency_user -d centinela_demo -c "SELECT 1;"
```

## Estado de Gate 3

✅ **COMPLETADO**

### Entregables
- ✅ Workflow n8n JSON funcional
- ✅ Documentación completa del workflow
- ✅ Script de prueba automatizado
- ✅ Manejo de errores implementado
- ✅ Timeouts y reintentos configurados
- ✅ Validación de payload
- ✅ Respuesta consolidada
- ✅ No expone PII
- ✅ Integración con Lovable documentada

### Validación
- ✅ Workflow se importa correctamente
- ✅ Workflow se activa sin errores
- ✅ Webhook procesa llamadas correctamente
- ✅ Datos se guardan en PostgreSQL
- ✅ Analytics incrementa total_incidents
- ✅ Respuesta JSON consolidada correcta

## Próximos Pasos (Gate 4)

1. Crear documentación técnica completa:
   - architecture.md
   - legal_privacy.md
   - cybersecurity.md
   - api_contract.md
   - lovable_integration.md
   - demo_script.md

2. Crear README.md completo con:
   - Descripción del proyecto
   - Arquitectura general
   - Instrucciones de instalación
   - Guía de uso
   - Comandos de validación

3. Crear tests automatizados:
   - pytest para cada servicio
   - Tests de integración
   - Tests de carga básicos

## Comandos de Referencia Rápida

```bash
# Levantar todo
./scripts/01_start.sh all && sleep 15

# Test APIs directamente
./scripts/04_test_environment.sh all

# Seed con APIs directas
./scripts/05_seed_demo_data.sh direct

# Test webhook n8n (requiere workflow activo)
./scripts/06_test_n8n_webhook.sh

# Ver logs
./scripts/03_logs.sh api-ingest
./scripts/03_logs.sh api-triage
./scripts/03_logs.sh api-analytics
./scripts/03_logs.sh n8n

# Detener todo
./scripts/02_stop.sh
```

---

**Versión:** Gate 3 Final  
**Fecha:** 2026-06-06  
**Autor:** Bob  
**Estado:** ✅ Aprobado para producción demo