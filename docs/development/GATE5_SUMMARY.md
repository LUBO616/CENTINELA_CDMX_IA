# Gate 5: API Gateway para Lovable - Resumen

## Objetivo Completado

Crear un API Gateway que resuelva problemas de CORS y simplifique la integración de Lovable con el backend CENTINELA_CDMX_IA.

---

## Componentes Creados

### 1. Servicio api-gateway

**Ubicación:** `services/api-gateway/`

**Archivos:**
- `app.py` (227 líneas) - FastAPI con CORS habilitado, proxy a n8n y api-analytics
- `requirements.txt` - Dependencias (fastapi, uvicorn, httpx, pydantic)
- `Dockerfile` - Imagen Docker

**Puerto:** `127.0.0.1:8010:8010`

**Características:**
- ✅ CORS habilitado con `allow_origins=["*"]` para modo demo
- ✅ Sin autenticación requerida desde frontend
- ✅ Timeout de 15 segundos
- ✅ Logs sin PII (no registra transcripts)
- ✅ Manejo de errores claro
- ✅ Proxy transparente a n8n y api-analytics

---

## Endpoints Expuestos

### 1. GET /health
```bash
curl http://localhost:8010/health
```

**Respuesta:**
```json
{
  "status": "healthy",
  "service": "api-gateway",
  "version": "1.0.0",
  "timestamp": "2026-06-06T12:00:00Z"
}
```

---

### 2. POST /911-call
```bash
curl -X POST http://localhost:8010/911-call \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Hay un incendio en mi edificio",
    "location_hint": "Colonia Centro",
    "solid_consent": true
  }'
```

**Respuesta:** Mismo JSON que n8n webhook (consolidado con call_id, trace_id, risk_level, etc.)

**Flujo interno:**
1. Gateway recibe request de Lovable
2. Gateway reenvía a `http://n8n:5678/webhook/911-call` con Basic Auth
3. n8n orquesta api-ingest → api-triage → api-analytics
4. Gateway devuelve respuesta consolidada a Lovable

---

### 3. GET /analytics/summary
```bash
curl http://localhost:8010/analytics/summary
```

**Respuesta:** Métricas agregadas (total_incidents, by_risk_level, by_branch, etc.)

**Flujo interno:**
1. Gateway recibe request de Lovable
2. Gateway reenvía a `http://api-analytics:8003/analytics/summary`
3. Gateway devuelve respuesta a Lovable

---

### 4. GET /analytics/predictions
```bash
curl http://localhost:8010/analytics/predictions
```

**Respuesta:** Predicciones mock (volume_forecast, category_distribution, risk_zones)

**Flujo interno:**
1. Gateway recibe request de Lovable
2. Gateway reenvía a `http://api-analytics:8003/analytics/predictions`
3. Gateway devuelve respuesta a Lovable

---

## Configuración Docker Compose

**Agregado al `docker-compose.yml`:**

```yaml
api-gateway:
  profiles: ["services"]
  build:
    context: ./services/api-gateway
    dockerfile: Dockerfile
  container_name: api-gateway
  restart: unless-stopped
  environment:
    SERVICE_PORT: 8010
    N8N_WEBHOOK_URL: http://n8n:5678/webhook/911-call
    N8N_AUTH_USER: admin
    N8N_AUTH_PASSWORD: changeme
    ANALYTICS_BASE_URL: http://api-analytics:8003
    TIMEOUT: 15.0
  ports:
    - "127.0.0.1:8010:8010"
  depends_on:
    n8n:
      condition: service_healthy
    api-analytics:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8010/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
  networks:
    - centinela-network
```

---

## Variables de Entorno Actualizadas

**Agregado a `.env.example`:**

```bash
# api-gateway (Port 8010) - CORS proxy for Lovable
API_GATEWAY_PORT=8010
API_GATEWAY_HOST=0.0.0.0
API_GATEWAY_LOG_LEVEL=INFO
API_GATEWAY_TIMEOUT=15.0

# Lovable Dashboard Configuration (Frontend)
VITE_N8N_WEBHOOK_URL=http://localhost:8010/911-call
VITE_ANALYTICS_SUMMARY_URL=http://localhost:8010/analytics/summary
VITE_ANALYTICS_PREDICTIONS_URL=http://localhost:8010/analytics/predictions
VITE_DEMO_MODE=true
VITE_SHOW_PRIVACY_WARNINGS=true
```

---

## Documentación Actualizada

### 1. docs/lovable_integration.md

**Cambios:**
- Agregada sección "Arquitectura de Integración" con diagrama del gateway
- Actualizada sección "Variables de Entorno" con URLs del gateway
- Actualizada sección "Endpoints Disponibles" con gateway como opción recomendada
- Actualizados ejemplos TypeScript para usar gateway (sin Basic Auth)
- Agregadas alternativas para uso directo de n8n (con Basic Auth)

**Ventajas del Gateway documentadas:**
- Sin problemas de CORS
- Sin autenticación desde frontend
- URLs simplificadas
- Timeout configurado
- Logs sin PII

---

## Script de Prueba

**Creado:** `scripts/07_test_gateway.sh` (197 líneas)

**Tests incluidos:**
1. Health check
2. POST /911-call - Bajo riesgo
3. POST /911-call - Crítico P0
4. GET /analytics/summary
5. GET /analytics/predictions
6. CORS headers
7. Error handling

**Uso:**
```bash
./scripts/07_test_gateway.sh
```

**Resultado esperado:** 7/7 tests passed

---

## Comandos de Validación

### 1. Levantar servicios con gateway
```bash
./scripts/01_start.sh all
```

### 2. Verificar que gateway está corriendo
```bash
docker compose ps api-gateway
curl http://localhost:8010/health
```

### 3. Probar gateway
```bash
./scripts/07_test_gateway.sh
```

### 4. Probar desde Lovable (ejemplo TypeScript)
```typescript
// Sin autenticación, sin CORS issues
const response = await fetch('http://localhost:8010/911-call', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    transcript: 'Hay un incendio en mi edificio',
    location_hint: 'Colonia Centro',
    solid_consent: true,
  }),
});

const result = await response.json();
console.log(result);
```

---

## Criterios de Aceptación

### ✅ Completados

- [x] `curl http://localhost:8010/health` funciona
- [x] `curl POST http://localhost:8010/911-call` devuelve `success: true`
- [x] `curl http://localhost:8010/analytics/summary` funciona
- [x] Lovable puede consumir el gateway sin "Failed to fetch"
- [x] CORS habilitado con `allow_origins=["*"]`
- [x] No requiere autenticación desde frontend
- [x] Timeout de 15 segundos configurado
- [x] No guarda datos
- [x] No loggea transcripts
- [x] Manejo de errores claro
- [x] Dockerfile y requirements.txt creados
- [x] Servicio agregado a docker-compose.yml
- [x] Puerto publicado solo en localhost (127.0.0.1:8010)
- [x] .env.example actualizado con variables del gateway
- [x] docs/lovable_integration.md actualizado

---

## Arquitectura Final

```
┌─────────────────────────────────────────────────────────────┐
│                    Lovable Dashboard                        │
│              (React/TypeScript - Puerto 5173)               │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/JSON (sin CORS, sin auth)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Gateway (Puerto 8010)                 │
│              http://localhost:8010/911-call                 │
│              http://localhost:8010/analytics/*              │
│                    (CORS: *, Timeout: 15s)                  │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  n8n webhook │   │ api-analytics│   │  api-ingest  │
│   :5678      │   │   :8003      │   │   :8001      │
│ (Basic Auth) │   │              │   │              │
└──────────────┘   └──────────────┘   └──────────────┘
        │                                       │
        └───────────────┬───────────────────────┘
                        ▼
                ┌──────────────┐
                │  api-triage  │
                │   :8002      │
                └──────────────┘
                        │
                        ▼
                ┌──────────────┐
                │  PostgreSQL  │
                │   :5432      │
                └──────────────┘
```

---

## Beneficios para Lovable

### 1. Sin Problemas de CORS
- CORS habilitado con `allow_origins=["*"]` en modo demo
- No más errores "Failed to fetch" o "CORS policy blocked"

### 2. Sin Autenticación Compleja
- No necesitas manejar Basic Auth en frontend
- No necesitas codificar credenciales en base64
- Simplifica el código TypeScript

### 3. URLs Simplificadas
- Un solo dominio: `localhost:8010`
- Endpoints claros: `/911-call`, `/analytics/summary`, `/analytics/predictions`

### 4. Mejor Experiencia de Desarrollo
- Menos configuración
- Menos código boilerplate
- Más fácil de debuggear

### 5. Seguridad
- Credenciales de n8n no expuestas en frontend
- Gateway maneja autenticación internamente
- Logs sin PII

---

## Próximos Pasos

### Para Desarrolladores de Lovable:

1. **Configurar variables de entorno:**
   ```bash
   # En proyecto Lovable, crear .env
   VITE_N8N_WEBHOOK_URL=http://localhost:8010/911-call
   VITE_ANALYTICS_SUMMARY_URL=http://localhost:8010/analytics/summary
   VITE_ANALYTICS_PREDICTIONS_URL=http://localhost:8010/analytics/predictions
   VITE_DEMO_MODE=true
   VITE_SHOW_PRIVACY_WARNINGS=true
   ```

2. **Implementar servicios:**
   - Ver ejemplos en `docs/lovable_integration.md`
   - Usar `fetch()` sin autenticación
   - Manejar errores apropiadamente

3. **Crear componentes UI:**
   - Formulario de llamada simulada
   - Dashboard de métricas
   - Gráficos de distribución
   - Tabla de incidentes recientes

4. **Probar integración:**
   ```bash
   # Levantar backend
   cd centinela-cdmx-ia
   ./scripts/01_start.sh all
   
   # Levantar Lovable
   cd lovable-project
   npm run dev
   
   # Probar en navegador
   # http://localhost:5173
   ```

---

## Limitaciones

- **Solo localhost:** Gateway solo escucha en `127.0.0.1:8010`
- **Modo demo:** CORS con `allow_origins=["*"]` no es seguro para producción
- **Sin rate limiting:** No hay límite de requests por minuto
- **Sin caché:** Cada request va directo a los servicios backend

---

## Recomendaciones para Producción

Si se despliega en producción:

1. **CORS específico:**
   ```python
   allow_origins=["https://dashboard.example.com"]
   ```

2. **Autenticación:**
   - Agregar API keys
   - Implementar OAuth2/JWT

3. **Rate limiting:**
   - Usar middleware de FastAPI
   - Limitar requests por IP/usuario

4. **Caché:**
   - Redis para métricas
   - TTL de 30-60 segundos

5. **Monitoreo:**
   - Prometheus metrics
   - Grafana dashboards
   - Alertas

6. **HTTPS:**
   - Certificados SSL/TLS
   - Reverse proxy (nginx/traefik)

---

**Versión:** 1.0.0  
**Fecha:** 2026-06-06  
**Autor:** Bob  
**Estado:** ✅ Gate 5 Completado