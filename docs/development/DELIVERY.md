# CENTINELA_CDMX_IA - Fase 2 Completada ✅

## Resumen de Entrega

Se ha completado la implementación de la infraestructura base y los 3 microservicios FastAPI con todas las funcionalidades requeridas.

---

## 1. Archivos Creados/Modificados

### Infraestructura Corregida
- ✅ `docker-compose.yml` - Actualizado con profiles para servicios, puertos en localhost
- ✅ `scripts/01_start.sh` - Actualizado con modos `infra` y `all`
- ✅ `scripts/04_test_environment.sh` - Actualizado con modos `infra` y `all`

### Microservicio: api-ingest (Puerto 8001)
- ✅ `services/api-ingest/requirements.txt`
- ✅ `services/api-ingest/Dockerfile`
- ✅ `services/api-ingest/app.py` (310 líneas)

**Funcionalidades:**
- ✅ GET /health - Health check
- ✅ POST /raw-conversations - Recibe y redacta conversaciones
- ✅ GET /raw-conversations - Lista conversaciones redactadas
- ✅ Redacción PII con regex + heurísticas (teléfonos, emails, nombres, direcciones)
- ✅ Generación de call_id y trace_id
- ✅ NUNCA guarda transcript original sin redactar
- ✅ SafeLogger que previene logging de PII

### Microservicio: api-triage (Puerto 8002)
- ✅ `services/api-triage/requirements.txt`
- ✅ `services/api-triage/Dockerfile`
- ✅ `services/api-triage/app.py` (485 líneas)

**Funcionalidades:**
- ✅ GET /health - Health check con contador de reglas
- ✅ POST /triage - Clasificación determinista
- ✅ Detección de señales P0 (60+ señales críticas)
- ✅ Clasificación de riesgo 1-10
- ✅ Detección NNA (Niñas, Niños, Adolescentes)
- ✅ Detección de adultos mayores
- ✅ Detección de violencia de género
- ✅ Clasificación por categorías (6 categorías)
- ✅ Determinación de autoridades primarias y de apoyo
- ✅ REGLA CRÍTICA: Nunca degradar llamadas con señales P0
- ✅ REGLA CRÍTICA: Señales P0 siempre resultan en risk_level >= 6

### Microservicio: api-analytics (Puerto 8003)
- ✅ `services/api-analytics/requirements.txt`
- ✅ `services/api-analytics/Dockerfile`
- ✅ `services/api-analytics/app.py` (476 líneas)

**Funcionalidades:**
- ✅ GET /health - Health check con contador de incidentes
- ✅ POST /incidents - Almacena incidentes
- ✅ GET /incidents - Lista incidentes con filtros
- ✅ GET /analytics/summary - Métricas agregadas
- ✅ GET /analytics/predictions - Predicciones mock
  - Pronóstico de volumen por hora
  - Distribución de categorías
  - Zonas de riesgo

---

## 2. Comandos para Reconstruir

### Paso 1: Preparar Entorno
```bash
# Navegar al directorio del proyecto
cd /home/lubo/Documents/CENTINELA_CDMX_IA

# Copiar archivo de configuración
cp .env.example .env

# Editar .env y cambiar contraseñas (IMPORTANTE)
nano .env
# Cambiar:
# - POSTGRES_PASSWORD
# - N8N_BASIC_AUTH_PASSWORD
# - N8N_ENCRYPTION_KEY
# - WEBHOOK_AUTH_TOKEN
```

### Paso 2: Validar Infraestructura
```bash
# Ejecutar precheck
./scripts/00_precheck.sh

# Debe mostrar:
# ✓ PASS: Docker is installed
# ✓ PASS: Docker Compose is installed
# ✓ PASS: Docker service is running
# ✓ PASS: All required ports are available
# ✓ PASS: .env file exists
# ✓ PASS: Project structure is complete
# ✓ PASS: Database initialization script exists
# ✓ PASS: docker-compose.yml is valid
# ✓ PASS: Sufficient disk space available
# ✓ PASS: Network connectivity is available
```

### Paso 3: Levantar Infraestructura (PostgreSQL + n8n)
```bash
# Iniciar solo infraestructura
./scripts/01_start.sh infra

# Esperar a que los servicios estén healthy (1-2 minutos)
# El script mostrará el progreso
```

### Paso 4: Validar Infraestructura
```bash
# Probar infraestructura
./scripts/04_test_environment.sh infra

# Debe mostrar:
# ✓ PASS Docker is running
# ✓ PASS PostgreSQL container is running
# ✓ PASS n8n container is running
# ✓ PASS PostgreSQL connection
# ✓ PASS All 3 schemas exist (raw, core, analytics)
# ✓ PASS All 4 tables exist
# ✓ PASS All 3 analytics views exist
# ✓ PASS n8n is accessible
```

### Paso 5: Levantar Todos los Servicios
```bash
# Construir e iniciar microservicios
./scripts/01_start.sh all

# Esto construirá las imágenes Docker y levantará los 3 microservicios
# Esperar 2-3 minutos para que todo esté listo
```

### Paso 6: Validar Todos los Servicios
```bash
# Probar todos los servicios
./scripts/04_test_environment.sh all

# Debe mostrar todos los tests pasando
```

---

## 3. Comandos de Prueba (curl)

### Test 1: Health Checks
```bash
# api-ingest
curl http://localhost:8001/health | jq '.'

# Respuesta esperada:
# {
#   "status": "healthy",
#   "service": "api-ingest",
#   "version": "1.0.0",
#   "database": "connected",
#   "timestamp": "2026-06-06T..."
# }

# api-triage
curl http://localhost:8002/health | jq '.'

# Respuesta esperada:
# {
#   "status": "healthy",
#   "service": "api-triage",
#   "version": "1.0.0",
#   "rules_loaded": 150,
#   "timestamp": "2026-06-06T..."
# }

# api-analytics
curl http://localhost:8003/health | jq '.'

# Respuesta esperada:
# {
#   "status": "healthy",
#   "service": "api-analytics",
#   "version": "1.0.0",
#   "database": "connected",
#   "total_incidents": 0,
#   "timestamp": "2026-06-06T..."
# }
```

### Test 2: Caso Bajo Riesgo (Public Services)
```bash
curl -X POST http://localhost:8001/raw-conversations \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Hola, quiero reportar un bache en la calle Reforma. Mi teléfono es 5512345678.",
    "metadata": {
      "source": "test",
      "timestamp": "2026-06-06T10:00:00Z"
    }
  }' | jq '.'

# Guardar call_id de la respuesta
CALL_ID="<call_id_de_respuesta>"

# Clasificar con triage
curl -X POST http://localhost:8002/triage \
  -H "Content-Type: application/json" \
  -d "{
    \"transcript\": \"Hola, quiero reportar un bache en la calle Reforma.\",
    \"call_id\": \"$CALL_ID\",
    \"consent\": true,
    \"location_hint\": \"Reforma\"
  }" | jq '.'

# Respuesta esperada:
# {
#   "risk_level": 2-3,
#   "branch": "low",
#   "case_category": "public_services",
#   "human_required": false,
#   "p0_signals": []
# }
```

### Test 3: Caso Medio Riesgo (Nivel 5 - Validación)
```bash
curl -X POST http://localhost:8001/raw-conversations \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Hay un accidente de tránsito en Insurgentes con Reforma. Hay varios carros chocados pero no veo heridos graves.",
    "metadata": {
      "source": "test",
      "timestamp": "2026-06-06T11:00:00Z"
    }
  }' | jq '.'

CALL_ID="<call_id_de_respuesta>"

curl -X POST http://localhost:8002/triage \
  -H "Content-Type: application/json" \
  -d "{
    \"transcript\": \"Hay un accidente de tránsito en Insurgentes con Reforma. Hay varios carros chocados.\",
    \"call_id\": \"$CALL_ID\",
    \"consent\": true,
    \"location_hint\": \"Insurgentes con Reforma\"
  }" | jq '.'

# Respuesta esperada:
# {
#   "risk_level": 5,
#   "branch": "mid",
#   "human_required": true,
#   "case_category": "protection_civil"
# }
```

### Test 4: Caso Crítico P0 (Niño con Sangrado Grave)
```bash
curl -X POST http://localhost:8001/raw-conversations \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "¡Auxilio! Hay un niño sangrando mucho de la cabeza. Se cayó de las escaleras. Está consciente pero sangra mucho. Estamos en la Colonia Centro.",
    "metadata": {
      "source": "test",
      "timestamp": "2026-06-06T14:00:00Z"
    }
  }' | jq '.'

CALL_ID="<call_id_de_respuesta>"

curl -X POST http://localhost:8002/triage \
  -H "Content-Type: application/json" \
  -d "{
    \"transcript\": \"¡Auxilio! Hay un niño sangrando mucho de la cabeza. Se cayó de las escaleras. Está consciente pero sangra mucho.\",
    \"call_id\": \"$CALL_ID\",
    \"consent\": true,
    \"location_hint\": \"Colonia Centro\"
  }" | jq '.'

# Respuesta esperada:
# {
#   "risk_level": 8-9,
#   "branch": "critical",
#   "case_category": "medical",
#   "human_required": true,
#   "best_interest_child": true,
#   "p0_signals": ["sangrado grave", "menor de edad"],
#   "primary_authority": "ERUM",
#   "protected_group_flags": {
#     "nna_involved": true
#   }
# }
```

### Test 5: Analytics - Almacenar Incidente
```bash
curl -X POST http://localhost:8003/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "123e4567-e89b-12d3-a456-426614174000",
    "trace_id": "223e4567-e89b-12d3-a456-426614174000",
    "risk_level": 8,
    "branch": "critical",
    "case_category": "medical",
    "human_required": true,
    "p0_signals": ["sangrado grave"],
    "location_hint": "Colonia Centro"
  }' | jq '.'

# Respuesta esperada:
# {
#   "incident_id": "uuid",
#   "stored_at": "2026-06-06T...",
#   "status": "stored"
# }
```

### Test 6: Analytics - Obtener Resumen
```bash
curl http://localhost:8003/analytics/summary | jq '.'

# Respuesta esperada:
# {
#   "total_incidents": 1,
#   "by_risk_level": {"8": 1},
#   "by_branch": {"critical": 1},
#   "by_category": {"medical": 1},
#   "human_required_count": 1,
#   "p0_signals_count": 1,
#   "last_updated": "2026-06-06T..."
# }
```

### Test 7: Analytics - Obtener Predicciones
```bash
curl http://localhost:8003/analytics/predictions | jq '.'

# Respuesta esperada:
# {
#   "volume_forecast": {
#     "predicted_calls": 25,
#     "confidence": 0.75,
#     "trend": "increasing",
#     "hourly_pattern": [...]
#   },
#   "category_distribution": {
#     "security": 0.30,
#     "medical": 0.25,
#     ...
#   },
#   "risk_zones": [
#     {
#       "zone": "Centro",
#       "risk_score": 7.5,
#       "incident_count": 45,
#       "primary_category": "security"
#     }
#   ]
# }
```

### Test 8: Listar Conversaciones Redactadas
```bash
curl "http://localhost:8001/raw-conversations?limit=10" | jq '.'

# Respuesta esperada:
# {
#   "total": 3,
#   "items": [
#     {
#       "call_id": "uuid",
#       "trace_id": "uuid",
#       "redacted_text": "Hola, quiero reportar un bache... [TELÉFONO-REDACTADO]",
#       "created_at": "2026-06-06T..."
#     }
#   ]
# }
```

### Test 9: Listar Incidentes con Filtros
```bash
# Todos los incidentes
curl "http://localhost:8003/incidents?limit=10" | jq '.'

# Filtrar por nivel de riesgo
curl "http://localhost:8003/incidents?risk_level=8" | jq '.'

# Filtrar por categoría
curl "http://localhost:8003/incidents?category=medical" | jq '.'
```

---

## 4. Resultado Esperado

### Infraestructura (Modo infra)
✅ PostgreSQL corriendo en 127.0.0.1:5432
✅ n8n corriendo en 127.0.0.1:5678
✅ 3 schemas creados (raw, core, analytics)
✅ 4 tablas creadas
✅ 3 views analíticas creadas

### Microservicios (Modo all)
✅ api-ingest corriendo en 127.0.0.1:8001
✅ api-triage corriendo en 127.0.0.1:8002
✅ api-analytics corriendo en 127.0.0.1:8003
✅ Todos los /health responden HTTP 200
✅ Redacción de PII funcional
✅ Clasificación determinista funcional
✅ Detección P0 funcional
✅ Almacenamiento de incidentes funcional
✅ Métricas y predicciones funcionales

### Validaciones de Seguridad
✅ Transcript original NUNCA se guarda sin redactar
✅ PII NUNCA se imprime en logs
✅ Puertos expuestos solo en localhost (127.0.0.1)
✅ Red Docker interna para comunicación entre servicios
✅ Señales P0 NUNCA se degradan

---

## 5. Limitaciones del MVP

### Funcionalidades Simplificadas
1. **Redacción PII**: Usa regex + heurísticas básicas, no NLP avanzado
2. **Clasificación**: Determinista por keywords, no ML real
3. **Predicciones**: Mock basado en patrones históricos simples
4. **Autenticación**: Solo Basic Auth en n8n, no OAuth2/JWT
5. **Geolocalización**: Solo hints de texto, no coordenadas GPS
6. **Audio**: No procesa audio, solo texto
7. **Tiempo Real**: Polling, no WebSockets
8. **Escalabilidad**: Single host, no horizontal scaling
9. **Monitoreo**: Logs básicos, no Prometheus/Grafana
10. **Testing**: Sin suite completa de pytest

### Datos y Compliance
1. **Solo datos demo**: No usar en producción
2. **Sin datos reales**: Nunca procesar llamadas reales
3. **Sin PII real**: Solo para demostración educativa
4. **Compliance básico**: Requiere auditoría legal completa
5. **Sin encriptación**: Base de datos sin TDE
6. **Sin backup**: No hay estrategia de respaldo
7. **Sin DR**: No hay plan de recuperación ante desastres

### Arquitectura
1. **Single point of failure**: Un solo host
2. **Sin load balancing**: No distribuye carga
3. **Sin caching**: No usa Redis/Memcached
4. **Sin message queue**: No usa RabbitMQ/Kafka
5. **Sin CDN**: No optimiza entrega de contenido

---

## 6. Comandos Útiles

### Ver Logs
```bash
# Todos los servicios
./scripts/03_logs.sh

# Servicio específico
./scripts/03_logs.sh api-ingest
./scripts/03_logs.sh api-triage
./scripts/03_logs.sh api-analytics
./scripts/03_logs.sh postgres
./scripts/03_logs.sh n8n

# Seguir logs en tiempo real
./scripts/03_logs.sh -f api-ingest
```

### Detener Sistema
```bash
# Detener servicios (mantiene datos)
./scripts/02_stop.sh

# Detener y eliminar volúmenes (BORRA DATOS)
./scripts/02_stop.sh --volumes

# Detener y eliminar todo (BORRA TODO)
./scripts/02_stop.sh --all
```

### Acceder a PostgreSQL
```bash
# Desde el host
docker exec -it centinela-db psql -U emergency_user -d centinela_demo

# Consultas útiles
\dt raw.*          # Listar tablas en schema raw
\dt core.*         # Listar tablas en schema core
\dt analytics.*    # Listar tablas en schema analytics
\dv analytics.*    # Listar views en schema analytics

SELECT COUNT(*) FROM raw.conversations;
SELECT COUNT(*) FROM core.triage_results;
SELECT COUNT(*) FROM analytics.incidents;

SELECT * FROM analytics.summary_stats;
```

### Reconstruir Servicios
```bash
# Reconstruir un servicio específico
docker compose --profile services build api-ingest
docker compose --profile services up -d api-ingest

# Reconstruir todos
docker compose --profile services build
docker compose --profile services up -d
```

---

## 7. Próximos Pasos

### Para Completar MVP
1. ✅ Infraestructura base - COMPLETADO
2. ✅ Microservicios FastAPI - COMPLETADO
3. ⏳ Workflow n8n - PENDIENTE
4. ⏳ Documentación completa - PENDIENTE
5. ⏳ Integración con Lovable - PENDIENTE

### Para Conectar Lovable
1. Usar endpoints de analytics:
   - `GET http://localhost:8003/analytics/summary`
   - `GET http://localhost:8003/analytics/predictions`
   - `GET http://localhost:8003/incidents`

2. Configurar polling cada 5-30 segundos

3. Usar webhook de n8n (cuando esté implementado):
   - `POST http://localhost:5678/webhook/911-call`
   - Autenticación: Basic Auth (usuario/password de .env)

---

## 8. Soporte y Troubleshooting

### Problema: Puertos en uso
```bash
# Ver qué está usando el puerto
sudo lsof -i :5432
sudo lsof -i :5678
sudo lsof -i :8001

# Detener proceso o cambiar puerto en .env
```

### Problema: Servicios no healthy
```bash
# Ver logs del servicio
./scripts/03_logs.sh <servicio>

# Reiniciar servicio específico
docker compose restart <servicio>

# Reconstruir servicio
docker compose --profile services build <servicio>
docker compose --profile services up -d <servicio>
```

### Problema: Base de datos no conecta
```bash
# Verificar que PostgreSQL está corriendo
docker ps | grep centinela-db

# Ver logs de PostgreSQL
./scripts/03_logs.sh postgres

# Probar conexión manual
docker exec -it centinela-db psql -U emergency_user -d centinela_demo -c "SELECT 1;"
```

### Problema: Permisos en scripts
```bash
# Dar permisos de ejecución
chmod +x scripts/*.sh
```

---

## Conclusión

✅ **Fase 2 Completada Exitosamente**

- Infraestructura corregida con profiles y puertos en localhost
- 3 microservicios FastAPI implementados y funcionales
- Redacción PII con regex + heurísticas
- Clasificación determinista con detección P0
- Métricas y predicciones mock
- Scripts operacionales actualizados
- Sistema listo para pruebas y siguiente fase

**Estado:** Listo para Gate 2 - Validación de Microservicios