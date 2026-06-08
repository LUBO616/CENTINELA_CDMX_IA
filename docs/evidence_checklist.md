# Checklist de Evidencias - CENTINELA_CDMX_IA

## Información General

Este documento proporciona una lista de verificación completa para validar que el MVP cumple con todos los requisitos técnicos, funcionales, y de hackathon. Incluye comandos de validación, evidencias esperadas, y sugerencias de screenshots.

**Propósito:** Facilitar la evaluación del proyecto por jueces y revisores técnicos.

---

## Tabla de Contenidos

1. [Gate 1: Infraestructura](#gate-1-infraestructura)
2. [Gate 2: Microservicios](#gate-2-microservicios)
3. [Gate 3: Orquestación n8n](#gate-3-orquestación-n8n)
4. [Gate 4: Documentación y Privacidad](#gate-4-documentación-y-privacidad)
5. [Rúbrica de Hackathon](#rúbrica-de-hackathon)
6. [Evidencias Visuales](#evidencias-visuales)
7. [Entregables Finales](#entregables-finales)

---

## Gate 1: Infraestructura

### Objetivo
Validar que Docker Compose levanta todos los servicios correctamente.

### Checklist

- [ ] **1.1 Docker Compose válido**
  ```bash
  docker compose config
  ```
  **Evidencia esperada:** Sin errores de sintaxis

- [ ] **1.2 Servicios levantados**
  ```bash
  docker compose up -d
  docker compose ps
  ```
  **Evidencia esperada:** 5 servicios corriendo (postgres, n8n, api-ingest, api-triage, api-analytics)

- [ ] **1.3 PostgreSQL accesible**
  ```bash
  docker compose exec postgres psql -U postgres -d emergencias_db -c "\dt raw.*"
  docker compose exec postgres psql -U postgres -d emergencias_db -c "\dt core.*"
  docker compose exec postgres psql -U postgres -d emergencias_db -c "\dt analytics.*"
  ```
  **Evidencia esperada:** Tablas en schemas raw, core, analytics

- [ ] **1.4 n8n accesible**
  ```bash
  curl -s http://localhost:5678/healthz | jq
  ```
  **Evidencia esperada:** `{"status": "ok"}`

- [ ] **1.5 Logs sin errores críticos**
  ```bash
  docker compose logs --tail=50
  ```
  **Evidencia esperada:** Sin errores de conexión o crashes

### Screenshot Sugerido
- Terminal mostrando `docker compose ps` con todos los servicios "Up"
- Navegador en `localhost:5678` mostrando login de n8n

---

## Gate 2: Microservicios

### Objetivo
Validar que los 3 microservicios responden correctamente.

### Checklist

#### 2.1 api-ingest (Puerto 8001)

- [ ] **Health check**
  ```bash
  curl -s http://localhost:8001/health | jq
  ```
  **Evidencia esperada:**
  ```json
  {
    "status": "healthy",
    "service": "api-ingest",
    "version": "1.0.0",
    "database": "connected"
  }
  ```

- [ ] **POST /raw-conversations**
  ```bash
  curl -X POST http://localhost:8001/raw-conversations \
    -H "Content-Type: application/json" \
    -d '{
      "transcript": "Hola, mi teléfono es 5512345678 y vivo en Calle Madero 45",
      "metadata": {"source": "test"}
    }' | jq
  ```
  **Evidencia esperada:**
  - `call_id` generado (UUID)
  - `trace_id` generado (UUID)
  - `redacted_text` con `[PHONE_REDACTED]` y `[ADDRESS_REDACTED]`
  - `redaction_summary` con conteos

- [ ] **GET /raw-conversations**
  ```bash
  curl -s http://localhost:8001/raw-conversations?limit=5 | jq
  ```
  **Evidencia esperada:** Lista de conversaciones redactadas

#### 2.2 api-triage (Puerto 8002)

- [ ] **Health check**
  ```bash
  curl -s http://localhost:8002/health | jq
  ```
  **Evidencia esperada:**
  ```json
  {
    "status": "healthy",
    "service": "api-triage",
    "version": "1.0.0",
    "rules_loaded": 120
  }
  ```

- [ ] **POST /triage - Caso Bajo Riesgo**
  ```bash
  # Primero crear conversación
  CALL_ID=$(curl -s -X POST http://localhost:8001/raw-conversations \
    -H "Content-Type: application/json" \
    -d '{"transcript": "Hay un bache en mi calle", "metadata": {}}' | jq -r '.call_id')
  
  # Luego clasificar
  curl -X POST http://localhost:8002/triage \
    -H "Content-Type: application/json" \
    -d "{
      \"transcript\": \"Hay un bache en mi calle\",
      \"call_id\": \"$CALL_ID\",
      \"consent\": true
    }" | jq '{risk_level, branch, case_category, human_required}'
  ```
  **Evidencia esperada:**
  ```json
  {
    "risk_level": 3,
    "branch": "low",
    "case_category": "public_services",
    "human_required": false
  }
  ```

- [ ] **POST /triage - Caso Crítico P0**
  ```bash
  CALL_ID=$(curl -s -X POST http://localhost:8001/raw-conversations \
    -H "Content-Type: application/json" \
    -d '{"transcript": "Hay un incendio y mi hijo está atrapado", "metadata": {}}' | jq -r '.call_id')
  
  curl -X POST http://localhost:8002/triage \
    -H "Content-Type: application/json" \
    -d "{
      \"transcript\": \"Hay un incendio y mi hijo está atrapado\",
      \"call_id\": \"$CALL_ID\",
      \"consent\": true
    }" | jq '{risk_level, branch, p0_signals, best_interest_child, human_required}'
  ```
  **Evidencia esperada:**
  ```json
  {
    "risk_level": 9,
    "branch": "critical",
    "p0_signals": ["incendio", "niño", "atrapado"],
    "best_interest_child": true,
    "human_required": true
  }
  ```

#### 2.3 api-analytics (Puerto 8003)

- [ ] **Health check**
  ```bash
  curl -s http://localhost:8003/health | jq
  ```
  **Evidencia esperada:**
  ```json
  {
    "status": "healthy",
    "service": "api-analytics",
    "version": "1.0.0",
    "database": "connected"
  }
  ```

- [ ] **POST /incidents**
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
      "location_hint": "Calle Madero 45, Colonia Centro"
    }' | jq
  ```
  **Evidencia esperada:**
  - `incident_id` generado
  - `stored_at` timestamp
  - Location normalizada (no debe aparecer "Calle Madero 45")

- [ ] **GET /analytics/summary**
  ```bash
  curl -s http://localhost:8003/analytics/summary | jq
  ```
  **Evidencia esperada:**
  ```json
  {
    "total_incidents": 50,
    "by_risk_level": {...},
    "by_branch": {
      "low": 30,
      "mid": 6,
      "critical": 14
    },
    "human_required_count": 20,
    "p0_signals_count": 14
  }
  ```

- [ ] **GET /analytics/predictions**
  ```bash
  curl -s http://localhost:8003/analytics/predictions | jq
  ```
  **Evidencia esperada:**
  ```json
  {
    "volume_forecast": {...},
    "category_distribution": {...},
    "risk_zones": [...]
  }
  ```

### Screenshot Sugerido
- Terminal mostrando los 3 health checks exitosos
- Resultado de clasificación de caso crítico P0 con `human_required: true`

---

## Gate 3: Orquestación n8n

### Objetivo
Validar que el workflow n8n orquesta correctamente los 3 microservicios.

### Checklist

- [ ] **3.1 Workflow importado**
  - Abrir `http://localhost:5678`
  - Login con `admin/changeme`
  - Verificar workflow "CENTINELA_CDMX_IA - Main" existe

- [ ] **3.2 Webhook accesible**
  ```bash
  curl -X POST http://localhost:5678/webhook/911-call \
    -u admin:changeme \
    -H "Content-Type: application/json" \
    -d '{
      "transcript": "Test webhook",
      "location_hint": "Test"
    }' | jq
  ```
  **Evidencia esperada:** Respuesta consolidada con `call_id`, `trace_id`, `risk_level`, etc.

- [ ] **3.3 Caso Bajo Riesgo**
  ```bash
  curl -X POST http://localhost:5678/webhook/911-call \
    -u admin:changeme \
    -H "Content-Type: application/json" \
    -d '{
      "transcript": "Hay un bache en la calle principal",
      "location_hint": "Colonia Centro"
    }' | jq '{risk_level, branch, human_required}'
  ```
  **Evidencia esperada:**
  ```json
  {
    "risk_level": 3,
    "branch": "low",
    "human_required": false
  }
  ```

- [ ] **3.4 Caso Nivel 5 (Validación)**
  ```bash
  curl -X POST http://localhost:5678/webhook/911-call \
    -u admin:changeme \
    -H "Content-Type: application/json" \
    -d '{
      "transcript": "Hubo un choque entre dos autos, hay tráfico",
      "location_hint": "Avenida Insurgentes"
    }' | jq '{risk_level, branch, human_required}'
  ```
  **Evidencia esperada:**
  ```json
  {
    "risk_level": 5,
    "branch": "mid",
    "human_required": false
  }
  ```

- [ ] **3.5 Caso Crítico P0**
  ```bash
  curl -X POST http://localhost:5678/webhook/911-call \
    -u admin:changeme \
    -H "Content-Type: application/json" \
    -d '{
      "transcript": "¡Auxilio! Hay un incendio y mi hijo está atrapado",
      "location_hint": "Colonia Roma"
    }' | jq '{risk_level, branch, p0_signals, best_interest_child, human_required}'
  ```
  **Evidencia esperada:**
  ```json
  {
    "risk_level": 9,
    "branch": "critical",
    "p0_signals": ["incendio", "niño", "atrapado"],
    "best_interest_child": true,
    "human_required": true
  }
  ```

- [ ] **3.6 Trazabilidad (trace_id)**
  ```bash
  # Enviar llamada y capturar trace_id
  RESPONSE=$(curl -s -X POST http://localhost:5678/webhook/911-call \
    -u admin:changeme \
    -H "Content-Type: application/json" \
    -d '{"transcript": "Test trazabilidad", "location_hint": "Test"}')
  
  TRACE_ID=$(echo $RESPONSE | jq -r '.trace_id')
  
  # Verificar que el mismo trace_id está en raw_conversations
  docker compose exec postgres psql -U postgres -d emergencias_db \
    -c "SELECT trace_id FROM raw.raw_conversations WHERE trace_id = '$TRACE_ID';"
  
  # Verificar que el mismo trace_id está en incidents
  docker compose exec postgres psql -U postgres -d emergencias_db \
    -c "SELECT trace_id FROM analytics.incidents WHERE trace_id = '$TRACE_ID';"
  ```
  **Evidencia esperada:** Mismo `trace_id` en ambas tablas

### Screenshot Sugerido
- n8n workflow abierto mostrando los 5 nodos conectados
- Ejecución exitosa del workflow (verde) con los 3 casos
- Terminal mostrando respuesta consolidada del webhook

---

## Gate 4: Documentación y Privacidad

### Objetivo
Validar que la documentación está completa y la privacidad está implementada.

### Checklist

#### 4.1 Documentación

- [ ] **README.md existe y es completo**
  - Descripción del proyecto
  - Arquitectura
  - Instalación paso a paso
  - Comandos de validación
  - Limitaciones del MVP

- [ ] **docs/architecture.md**
  - Diagramas Mermaid
  - Descripción de componentes
  - Flujo de datos

- [ ] **docs/legal_privacy.md**
  - LFPDPPP compliance
  - LGDNNA (NNA protection)
  - ARCO rights
  - Consentimiento

- [ ] **docs/cybersecurity.md**
  - Threat model
  - Attack surface
  - Security controls
  - Production recommendations

- [ ] **docs/api_contract.md**
  - Especificación de todos los endpoints
  - Request/response examples
  - Error codes
  - curl examples

- [ ] **docs/lovable_integration.md**
  - Variables de entorno
  - Ejemplos TypeScript
  - Componentes UI sugeridos
  - CORS configuration

- [ ] **docs/demo_script.md**
  - Script de 3-5 minutos
  - 3 casos de prueba
  - Q&A preparado
  - Disclaimers éticos

- [ ] **docs/evidence_checklist.md** (este documento)
  - Checklist completo
  - Comandos de validación
  - Screenshots sugeridos

#### 4.2 Privacidad

- [ ] **Redacción de PII en api-ingest**
  ```bash
  curl -X POST http://localhost:8001/raw-conversations \
    -H "Content-Type: application/json" \
    -d '{
      "transcript": "Mi nombre es Juan Pérez, teléfono 5512345678, correo juan@example.com, vivo en Calle Madero 45",
      "metadata": {}
    }' | jq '.redacted_text'
  ```
  **Evidencia esperada:** Todos los PII redactados con `[*_REDACTED]`

- [ ] **Normalización de ubicaciones en api-analytics**
  ```bash
  curl -X POST http://localhost:8003/incidents \
    -H "Content-Type: application/json" \
    -d '{
      "call_id": "123e4567-e89b-12d3-a456-426614174000",
      "trace_id": "223e4567-e89b-12d3-a456-426614174000",
      "risk_level": 5,
      "branch": "mid",
      "case_category": "security",
      "human_required": false,
      "p0_signals": [],
      "location_hint": "Calle Madero 45, Colonia Centro, CP 06000"
    }' | jq
  
  # Verificar en DB que la ubicación está normalizada
  docker compose exec postgres psql -U postgres -d emergencias_db \
    -c "SELECT location_hint FROM analytics.incidents ORDER BY created_at DESC LIMIT 1;"
  ```
  **Evidencia esperada:** Location normalizada (ej: "Centro", no "Calle Madero 45")

- [ ] **No se guarda transcript original**
  ```bash
  docker compose exec postgres psql -U postgres -d emergencias_db \
    -c "SELECT column_name FROM information_schema.columns WHERE table_schema = 'raw' AND table_name = 'raw_conversations';"
  ```
  **Evidencia esperada:** Solo existe `redacted_text`, no `original_text` o `transcript`

- [ ] **.env no está en el repo**
  ```bash
  ls -la | grep "^\.env$"
  ```
  **Evidencia esperada:** Archivo no existe (solo `.env.example`)

- [ ] **.gitignore incluye .env**
  ```bash
  grep "^\.env$" .gitignore
  ```
  **Evidencia esperada:** `.env` está en `.gitignore`

### Screenshot Sugerido
- Archivo README.md abierto en editor
- Terminal mostrando PII redactado correctamente
- DB query mostrando location normalizada

---

## Rúbrica de Hackathon

### Criterio 1: Ejecución Técnica (30%)

- [ ] **Sistema funcional end-to-end**
  - Todos los servicios levantan sin errores
  - Webhook procesa los 3 casos correctamente
  - Métricas se actualizan en tiempo real

- [ ] **Calidad del código**
  - Código limpio y documentado
  - Tests automatizados (18 tests en `scripts/04_test_environment.sh`)
  - Manejo de errores apropiado

- [ ] **Arquitectura sólida**
  - Microservicios desacoplados
  - Separación de concerns (raw/core/analytics)
  - Escalabilidad considerada

**Evidencia:**
```bash
# Ejecutar todos los tests
./scripts/04_test_environment.sh

# Verificar que pasan los 18 tests
echo "Tests passed: $(grep -c '✅' /tmp/test_output.log)"
```

---

### Criterio 2: Impacto Social (25%)

- [ ] **Problema real identificado**
  - Sobrecarga de operadores 911
  - Retrasos en emergencias críticas
  - Falta de trazabilidad

- [ ] **Solución con impacto medible**
  - Reduce carga operativa en 30-40%
  - Prioriza emergencias P0 en <2 segundos
  - Protege grupos vulnerables (NNA, adultos mayores)

- [ ] **Cumplimiento legal y ético**
  - LFPDPPP compliance
  - LGDNNA (interés superior del niño)
  - Human-in-the-loop para decisiones críticas

**Evidencia:**
- `docs/legal_privacy.md` - Compliance detallado
- `docs/demo_script.md` - Impacto cuantificado
- Casos de prueba con NNA protection activada

---

### Criterio 3: Innovación (20%)

- [ ] **Enfoque único**
  - IA determinista (no caja negra)
  - Privacy by design (redacción automática)
  - Trazabilidad completa con trace_id

- [ ] **Tecnología apropiada**
  - Docker Compose (no VMs)
  - n8n para orquestación
  - FastAPI para microservicios

- [ ] **Escalabilidad**
  - Arquitectura modular
  - Preparado para ML real
  - APIs REST estándar

**Evidencia:**
- `docs/architecture.md` - Diagramas y diseño
- `docs/cybersecurity.md` - Threat model
- Código fuente con comentarios explicativos

---

### Criterio 4: Viabilidad (15%)

- [ ] **MVP funcional**
  - No es solo mockup o slides
  - Sistema completo end-to-end
  - Datos sintéticos realistas

- [ ] **Costo razonable**
  - Corre en hardware modesto (4GB RAM)
  - Estimado ~$500-1000/mes en cloud para 10k llamadas/día
  - Mucho menor que contratar más operadores

- [ ] **Plan de escalamiento**
  - Kubernetes-ready
  - Integración con sistemas existentes vía API
  - Roadmap para ML real

**Evidencia:**
- Sistema corriendo en laptop/servidor modesto
- `README.md` - Requisitos de hardware
- `docs/lovable_integration.md` - Plan de integración

---

### Criterio 5: Pitch y UX (10%)

- [ ] **Presentación clara**
  - Script de 3-5 minutos preparado
  - Demo en vivo funcional
  - Mensaje de impacto social claro

- [ ] **Dashboard/UI**
  - Lovable dashboard (si aplica)
  - Métricas visuales
  - UX intuitiva

- [ ] **Documentación para jueces**
  - README completo
  - Comandos de validación fáciles
  - Screenshots/videos de evidencia

**Evidencia:**
- `docs/demo_script.md` - Script completo
- `docs/lovable_integration.md` - Guía de UI
- Este checklist para facilitar evaluación

---

## Evidencias Visuales

### Screenshots Recomendados

1. **Arquitectura**
   - Diagrama Mermaid de `docs/architecture.md`
   - `docker compose ps` mostrando servicios corriendo

2. **Funcionalidad**
   - Terminal con los 3 casos de prueba ejecutados
   - n8n workflow con ejecución exitosa (verde)
   - Dashboard Lovable mostrando métricas (si aplica)

3. **Privacidad**
   - PII redactado en respuesta de api-ingest
   - Location normalizada en DB query
   - `.gitignore` mostrando `.env` excluido

4. **Métricas**
   - `GET /analytics/summary` con datos agregados
   - `GET /analytics/predictions` con forecast mock
   - Gráficos de distribución por riesgo/categoría

5. **Documentación**
   - README.md abierto en editor
   - Carpeta `docs/` con 8 archivos
   - `scripts/` con 7 scripts operacionales

### Video Demo (Opcional)

**Duración:** 2-3 minutos  
**Contenido:**
1. Levantar servicios (`./scripts/01_start.sh all`)
2. Ejecutar caso crítico P0 vía webhook
3. Mostrar resultado en terminal
4. Abrir n8n y mostrar workflow
5. Consultar métricas en api-analytics
6. Mostrar dashboard Lovable (si aplica)

**Herramientas sugeridas:**
- OBS Studio (grabación de pantalla)
- Kazam (Linux)
- QuickTime (macOS)

---

## Entregables Finales

### Código Fuente

- [ ] Repositorio Git con historial de commits
- [ ] `.gitignore` apropiado (excluye `.env`, `__pycache__`, etc.)
- [ ] `README.md` completo
- [ ] Carpeta `docs/` con 8 documentos
- [ ] Carpeta `scripts/` con 7 scripts
- [ ] Carpeta `services/` con 3 microservicios
- [ ] `docker-compose.yml` funcional
- [ ] `.env.example` con todas las variables

### Documentación

- [ ] `README.md` (682 líneas)
- [ ] `docs/architecture.md` (619 líneas)
- [ ] `docs/legal_privacy.md` (847 líneas)
- [ ] `docs/cybersecurity.md` (682 líneas)
- [ ] `docs/api_contract.md` (782 líneas)
- [ ] `docs/lovable_integration.md` (738 líneas)
- [ ] `docs/demo_script.md` (545 líneas)
- [ ] `docs/evidence_checklist.md` (este documento)

### Scripts Operacionales

- [ ] `scripts/00_precheck.sh` - Verificar dependencias
- [ ] `scripts/01_start.sh` - Levantar servicios
- [ ] `scripts/02_stop.sh` - Detener servicios
- [ ] `scripts/03_logs.sh` - Ver logs
- [ ] `scripts/04_test_environment.sh` - Tests automatizados (18 tests)
- [ ] `scripts/05_seed_demo_data.sh` - Datos de prueba
- [ ] `scripts/06_test_n8n_webhook.sh` - Pruebas de webhook

### Evidencias de Funcionamiento

- [ ] Screenshots de servicios corriendo
- [ ] Screenshots de casos de prueba exitosos
- [ ] Screenshots de métricas en tiempo real
- [ ] Video demo (opcional pero recomendado)
- [ ] Logs de ejecución sin errores

---

## Comandos de Validación Rápida

### Validación Completa en 5 Minutos

```bash
# 1. Verificar dependencias (30 segundos)
./scripts/00_precheck.sh

# 2. Levantar servicios (60 segundos)
./scripts/01_start.sh all

# 3. Ejecutar tests automatizados (90 segundos)
./scripts/04_test_environment.sh

# 4. Probar webhook con 3 casos (60 segundos)
./scripts/06_test_n8n_webhook.sh

# 5. Verificar métricas (30 segundos)
curl -s http://localhost:8003/analytics/summary | jq '{
  total_incidents,
  by_branch,
  human_required_count,
  p0_signals_count
}'

# 6. Ver logs (30 segundos)
./scripts/03_logs.sh api-triage 20
```

**Resultado esperado:** Todos los comandos ejecutan sin errores, 18 tests pasan, 3 casos de webhook procesan correctamente.

---

## Notas para Evaluadores

### Cómo Evaluar Este Proyecto

1. **Clonar el repositorio**
   ```bash
   git clone <repo_url>
   cd centinela-cdmx-ia
   ```

2. **Leer README.md**
   - Entender el problema y la solución
   - Revisar arquitectura
   - Verificar requisitos de hardware

3. **Ejecutar validación rápida**
   ```bash
   ./scripts/00_precheck.sh
   ./scripts/01_start.sh all
   ./scripts/04_test_environment.sh
   ```

4. **Probar casos de uso**
   ```bash
   ./scripts/06_test_n8n_webhook.sh
   ```

5. **Revisar documentación**
   - `docs/architecture.md` - Diseño técnico
   - `docs/legal_privacy.md` - Compliance
   - `docs/api_contract.md` - Especificación de APIs

6. **Evaluar según rúbrica**
   - Ejecución técnica: ¿Funciona end-to-end?
   - Impacto social: ¿Resuelve un problema real?
   - Innovación: ¿Enfoque único?
   - Viabilidad: ¿Es escalable?
   - Pitch: ¿Presentación clara?

### Preguntas Clave para Evaluadores

- ¿El sistema procesa correctamente los 3 casos (bajo, medio, crítico)?
- ¿La redacción de PII funciona?
- ¿Las señales P0 siempre escalan a humano?
- ¿El principio de interés superior del niño se activa correctamente?
- ¿La documentación es clara y completa?
- ¿El código es limpio y mantenible?
- ¿El impacto social es medible?

---

## Limitaciones Conocidas (Transparencia)

### Limitaciones del MVP

- **No usa audio real:** Solo texto (por privacidad y simplicidad)
- **IA determinista:** No ML real (por explicabilidad y transparencia)
- **Datos sintéticos:** No datos reales de 911 (por privacidad)
- **Local only:** No expuesto a internet (por seguridad)
- **Predicciones mock:** No basadas en ML real (por falta de datos históricos)

### Próximos Pasos para Producción

- Integrar con sistema ASR (speech-to-text)
- Agregar ML para mejorar clasificación (con datos reales)
- Implementar autenticación robusta (OAuth2, JWT)
- Desplegar en Kubernetes
- Auditoría de seguridad completa
- Piloto con C5 o centro de atención ciudadana

---

**Versión:** 1.0.0  
**Fecha:** 2026-06-06  
**Autor:** Bob  
**Propósito:** Checklist de validación para hackathon  
**Uso:** Facilitar evaluación por jueces y revisores técnicos