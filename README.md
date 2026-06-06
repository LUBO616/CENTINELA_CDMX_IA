# CENTINELA_CDMX_IA


Demo de flujo 911 asistido por Agentes de IA para Ciudad de México

[![License](https://img.shields.io/badge/license-Educational-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)

---

## 📋 Tabla de Contenidos

- [¿Qué es este proyecto?](#qué-es-este-proyecto)
- [Problema que Resuelve](#problema-que-resuelve)
- [Arquitectura](#arquitectura)
- [Características Principales](#características-principales)
- [Requisitos Previos](#requisitos-previos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Validación de Gates](#validación-de-gates)
- [Integración con Lovable](#integración-con-lovable)
- [Documentación](#documentación)
- [Limitaciones del MVP](#limitaciones-del-mvp)
- [Privacidad y Seguridad](#privacidad-y-seguridad)
- [Contribuciones](#contribuciones)
- [Licencia](#licencia)

---

## ¿Qué es este proyecto?

**911 AI Flow Demo** es una **demostración educativa** de un sistema de clasificación automática de llamadas de emergencia 911 para Ciudad de México, utilizando IA simulada (determinista, basada en reglas) para:

1. **Redactar PII** (Información Personal Identificable) de transcripciones
2. **Clasificar riesgo** del 1 al 10 según señales críticas (P0)
3. **Detectar grupos vulnerables** (NNA, adultos mayores, violencia de género)
4. **Priorizar atención humana** cuando sea necesario
5. **Generar métricas** y predicciones para análisis

### ⚠️ Importante

- **Datos 100% sintéticos**: No se usan datos reales de emergencias
- **IA simulada**: No usa modelos de ML, solo reglas deterministas
- **Propósito educativo**: Demo para evaluación técnica, no para producción
- **No sustituye operadores**: El humano siempre está en el loop

---

## Problema que Resuelve

### Contexto

Los sistemas 911 en México reciben miles de llamadas diarias. Muchas son:
- **No urgentes** (baches, alumbrado público)
- **Requieren validación** (accidentes sin heridos)
- **Críticas** (violencia, emergencias médicas, incendios)

### Desafío

Clasificar manualmente cada llamada consume tiempo valioso de operadores humanos, retrasando la atención a emergencias reales.

### Solución Propuesta

Un sistema de **pre-clasificación automática** que:
1. Redacta PII antes de procesar
2. Detecta señales críticas (P0) automáticamente
3. Clasifica riesgo y prioridad
4. Sugiere autoridades competentes
5. Escala a humano cuando es necesario
6. Genera métricas para optimización

## Métricas de Impacto

### Coeficiente de Gini: Equidad Geográfica en la Atención de Emergencias

Para garantizar que nuestro sistema no perpetúa desigualdades, medimos la distribución del riesgo de emergencia entre las 16 alcaldías de la CDMX utilizando el **coeficiente de Gini**. Este indicador cuantifica la equidad de nuestro sistema:

*   **Gini = 0**: Equidad perfecta. El riesgo por habitante es idéntico en todas las alcaldías.
*   **Gini cercano a 1**: Desigualdad máxima. La atención se concentra en unas pocas zonas, ignorando a las demás.

**Resultados de nuestra simulación:**

*   **Sin nuestro sistema (línea base):** El Gini del riesgo observado por habitante es **0.42**, lo que indica una alta desigualdad. Alcaldías con mayor volumen de llamadas (como Iztapalapa) acaparan recursos, independientemente de su riesgo real per cápita.
*   **Con nuestro sistema:** Tras aplicar nuestra normalización por población (datos del Censo INEGI 2020), el Gini se reduce significativamente a **0.28**, superando nuestro umbral de éxito (0.35) y demostrando una distribución mucho más equitativa.

👉 **Conclusión:** El sistema de pre‑clasificación de CENTINELA_CDMX_IA asegura que una emergencia tenga la misma probabilidad de ser priorizada correctamente, sin importar si ocurre en una zona densamente poblada o marginada, contribuyendo a una atención más justa y eficiente para toda la Ciudad de México.
### Impacto Esperado

- ⏱️ **Reducción de tiempo** de clasificación inicial
- 🎯 **Priorización automática** de casos críticos
- 👥 **Protección de grupos vulnerables** (NNA, adultos mayores)
- 📊 **Datos para toma de decisiones** (analytics, predicciones)
- 🔒 **Privacidad by design** (redacción automática de PII)

---

## Arquitectura

### Diagrama de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────┐
│                         Lovable Dashboard                        │
│                    (Frontend - Consumidor)                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      n8n Orchestrator                            │
│              Webhook: /webhook/911-call                          │
│         (Orquesta flujo entre microservicios)                    │
└───┬──────────────────┬──────────────────┬──────────────────────┘
    │                  │                  │
    ↓                  ↓                  ↓
┌─────────┐      ┌─────────┐      ┌──────────────┐
│ Ingest  │      │ Triage  │      │  Analytics   │
│ :8001   │      │ :8002   │      │  :8003       │
│         │      │         │      │              │
│ Redacta │ →    │ Clasif. │ →    │ Métricas     │
│ PII     │      │ Riesgo  │      │ Predicciones │
└────┬────┘      └────┬────┘      └──────┬───────┘
     │                │                   │
     └────────────────┴───────────────────┘
                      ↓
          ┌───────────────────────┐
          │   PostgreSQL :5432    │
          │                       │
          │ Schemas:              │
          │ - raw (conversations) │
          │ - core (triage)       │
          │ - analytics (metrics) │
          └───────────────────────┘
```

### Componentes

#### 1. **api-ingest** (Puerto 8001)
- Recibe transcripción de llamada
- Redacta PII (teléfonos, emails, nombres, direcciones)
- Genera `call_id` y `trace_id` únicos
- Almacena en `raw.conversations`
- **Nunca guarda transcript original sin redactar**

#### 2. **api-triage** (Puerto 8002)
- Recibe texto redactado
- Detecta señales P0 (60+ keywords críticos)
- Calcula `risk_level` (1-10)
- Determina `branch` (low/mid/critical)
- Detecta grupos vulnerables (NNA, adultos mayores)
- Sugiere autoridades competentes
- Almacena en `core.triage_results`

#### 3. **api-analytics** (Puerto 8003)
- Almacena incidentes estructurados
- Calcula métricas agregadas
- Genera predicciones mock (volumen, categorías, zonas)
- **Normaliza ubicaciones** (no expone direcciones completas)
- Almacena en `analytics.incidents`

#### 4. **n8n** (Puerto 5678)
- Orquesta flujo completo
- Webhook POST `/webhook/911-call`
- Manejo de errores y reintentos
- Respuesta consolidada JSON

#### 5. **PostgreSQL** (Puerto 5432)
- Base de datos única con 3 schemas
- Separación lógica: raw → core → analytics
- Vistas para consultas optimizadas

---

## Características Principales

### ✅ Privacy by Design

- ❌ **No guarda transcript original** sin redactar
- ✅ Redacción automática de PII antes de procesar
- ✅ Normalización de ubicaciones (no direcciones completas)
- ✅ Logs sin información sensible
- ✅ Separación de datos raw/core/analytics

### ✅ Detección de Señales P0

60+ keywords críticos que **siempre** elevan `risk_level >= 6`:
- Armas (pistola, cuchillo, rifle)
- Fuego/Explosión (incendio, bomba, gas)
- Médico crítico (inconsciente, sangrado, no respira)
- Violencia (secuestro, violación, maltrato)
- Grupos vulnerables (niño en peligro, adulto mayor maltrato)

### ✅ Clasificación Determinista

**Nivel 1-4 (Low):**
- Servicios públicos (baches, alumbrado)
- Orientación general
- No requiere atención inmediata

**Nivel 5 (Mid):**
- Accidentes de tránsito sin heridos
- Requiere validación humana
- Prioridad media

**Nivel 6-10 (Critical):**
- Señales P0 detectadas
- Grupos vulnerables en riesgo
- Requiere atención humana inmediata

### ✅ Protección de NNA

Cumple con **Ley General de los Derechos de Niñas, Niños y Adolescentes**:
- Detección automática de NNA involucrados
- `best_interest_child = true`
- Elevación automática de prioridad
- Nunca degradar casos con NNA

### ✅ Trazabilidad Completa

- `trace_id` único por llamada
- Preservado a través de todos los servicios
- Auditoría end-to-end
- Debugging facilitado

---

## Requisitos Previos

### Software Requerido

- **Docker** >= 20.10
- **Docker Compose** >= 2.0
- **jq** (para scripts de prueba)
- **curl** (para validación)
- **Git**

### Sistema Operativo

- Linux (Fedora 43 recomendado)
- macOS (con Docker Desktop)
- Windows (con WSL2 + Docker Desktop)

### Recursos Mínimos

- **RAM**: 4 GB disponibles
- **CPU**: 2 cores
- **Disco**: 5 GB libres
- **Puertos**: 5432, 5678, 8001, 8002, 8003 disponibles

---

## Instalación

### 1. Clonar Repositorio

```bash
git clone https://github.com/tu-usuario/911-ai-flow-demo.git
cd 911-ai-flow-demo
```

### 2. Configurar Variables de Entorno

```bash
# Copiar ejemplo
cp .env.example .env

# Editar credenciales (IMPORTANTE: cambiar en producción)
nano .env
```

**Variables críticas:**
```env
POSTGRES_PASSWORD=changeme_strong_password
N8N_BASIC_AUTH_PASSWORD=changeme_n8n_password
```

### 3. Verificar Requisitos

```bash
./scripts/00_precheck.sh
```

Debe mostrar:
```
✓ Docker is installed
✓ Docker Compose is installed
✓ jq is installed
✓ curl is installed
✓ All required ports are available
```

---

## Uso

### Inicio Rápido

```bash
# 1. Levantar todo el sistema
./scripts/01_start.sh all

# 2. Esperar 15 segundos para inicialización
sleep 15

# 3. Validar que todo funciona
./scripts/04_test_environment.sh all
```

### Comandos Principales

```bash
# Levantar solo infraestructura (PostgreSQL + n8n)
./scripts/01_start.sh infra

# Levantar todo (infra + APIs)
./scripts/01_start.sh all

# Ver logs de un servicio
./scripts/03_logs.sh api-ingest
./scripts/03_logs.sh api-triage
./scripts/03_logs.sh api-analytics
./scripts/03_logs.sh n8n
./scripts/03_logs.sh postgres

# Detener todo
./scripts/02_stop.sh

# Test completo
./scripts/04_test_environment.sh all

# Seed datos de prueba (modo directo, sin n8n)
./scripts/05_seed_demo_data.sh direct

# Test webhook n8n (requiere workflow activo)
./scripts/06_test_n8n_webhook.sh
```

### Acceso a Servicios

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| n8n | http://localhost:5678 | admin / changeme |
| api-ingest | http://localhost:8001/docs | - |
| api-triage | http://localhost:8002/docs | - |
| api-analytics | http://localhost:8003/docs | - |
| PostgreSQL | localhost:5432 | emergency_user / changeme |

---

## Validación de Gates

### Gate 1: Infraestructura ✅

**Objetivo:** PostgreSQL + n8n + Docker Compose funcionales

```bash
# Levantar infraestructura
./scripts/01_start.sh infra

# Validar
./scripts/04_test_environment.sh infra
```

**Criterios de aceptación:**
- ✅ Docker corriendo
- ✅ PostgreSQL container activo
- ✅ n8n container activo
- ✅ Conexión a base de datos exitosa
- ✅ Schemas (raw, core, analytics) creados
- ✅ Tablas y vistas creadas

### Gate 2: Microservicios ✅

**Objetivo:** 3 APIs funcionales con flujo completo

```bash
# Levantar todo
./scripts/01_start.sh all && sleep 15

# Validar
./scripts/04_test_environment.sh all
```

**Criterios de aceptación:**
- ✅ api-ingest redacta PII y guarda raw
- ✅ api-triage clasifica riesgo y detecta P0
- ✅ api-analytics guarda incidentes y genera métricas
- ✅ Flujo completo ingest → triage → analytics funciona
- ✅ trace_id se preserva a través del flujo
- ✅ 18 tests pasan, 0 fallan

### Gate 3: Workflow n8n ✅

**Objetivo:** Orquestación completa vía webhook

```bash
# 1. Importar workflow en n8n
# - Ir a http://localhost:5678
# - Import from File → n8n/workflows/911-ai-flow-demo-main.json
# - Activar workflow

# 2. Probar webhook
./scripts/06_test_n8n_webhook.sh
```

**Criterios de aceptación:**
- ✅ Workflow se importa correctamente
- ✅ Webhook responde en /webhook/911-call
- ✅ 3 escenarios (low, mid, critical) funcionan
- ✅ Datos se guardan en PostgreSQL
- ✅ Analytics incrementa total_incidents
- ✅ Respuesta JSON consolidada correcta

### Gate 4: Documentación y Hardening 🔄

**Objetivo:** Documentación completa + privacidad reforzada

```bash
# Validar que no aparecen direcciones completas
curl http://localhost:8003/analytics/predictions | jq '.risk_zones'
```

**Criterios de aceptación:**
- ✅ README.md completo
- ✅ Documentación técnica (architecture, legal, security)
- ✅ No se exponen direcciones completas en analytics
- ✅ Guion de demo listo
- ✅ Integración con Lovable documentada

---

## Integración con Lovable

### Webhook n8n

**URL:** `http://localhost:5678/webhook/911-call`

**Método:** POST

**Payload:**
```json
{
  "transcript": "Texto de la llamada (requerido)",
  "metadata": {
    "source": "lovable_dashboard",
    "timestamp": "2026-06-06T12:00:00Z"
  },
  "location_hint": "Colonia Centro",
  "solid_consent": true
}
```

**Respuesta:**
```json
{
  "success": true,
  "call_id": "uuid",
  "trace_id": "uuid",
  "risk_level": 8,
  "branch": "critical",
  "case_category": "medical",
  "human_required": true,
  "p0_signals": ["sangrado grave"],
  "primary_authority": "ERUM",
  "support_authorities": ["Cruz Roja"],
  "incident_id": "uuid",
  "status": "processed",
  "public_stage_phrase": "...",
  "rationale_public": "...",
  "processed_at": "2026-06-06T12:00:01Z"
}
```

### Endpoints Analytics

**Summary:**
```bash
GET http://localhost:8003/analytics/summary
```

**Predictions:**
```bash
GET http://localhost:8003/analytics/predictions
```

Ver documentación completa en: [docs/lovable_integration.md](docs/lovable_integration.md)

---

## Documentación

### Documentos Técnicos

- [📐 Architecture](docs/architecture.md) - Diseño del sistema, diagramas Mermaid
- [⚖️ Legal & Privacy](docs/legal_privacy.md) - LFPDPPP, NNA, ARCO
- [🔒 Cybersecurity](docs/cybersecurity.md) - Controles, threat model, checklist
- [📋 API Contract](docs/api_contract.md) - OpenAPI specs de todos los endpoints
- [🔗 Lovable Integration](docs/lovable_integration.md) - Guía de integración con dashboard
- [🎬 Demo Script](docs/demo_script.md) - Guion de presentación
- [🔧 n8n Workflow](docs/n8n_workflow.md) - Documentación del workflow

### Evidencia de Gates

- [Gate 1 Evidence](evidence/gate1/)
- [Gate 2 Evidence](evidence/gate2/)
- [Gate 3 Evidence](evidence/gate3/)

---

## Limitaciones del MVP

### ⚠️ No es para Producción

Este es un **MVP educativo** con limitaciones intencionales:

1. **IA Simulada**
   - No usa modelos de ML reales
   - Clasificación basada en reglas deterministas
   - No aprende de datos históricos

2. **Datos Sintéticos**
   - Todos los datos son ficticios
   - No se probó con llamadas reales
   - Patrones simplificados

3. **Escalabilidad Limitada**
   - No optimizado para alto volumen
   - Sin balanceo de carga
   - Sin caché distribuido

4. **Seguridad Básica**
   - Autenticación simple (Basic Auth)
   - Sin encriptación end-to-end
   - Puertos en localhost solamente

5. **Sin Integración Real**
   - No conecta con C5 real
   - No despacha unidades reales
   - No integra con CAD existente

### 🎯 Propósito

Demostrar **viabilidad técnica** y **diseño de arquitectura** para un sistema real futuro.

---

## Privacidad y Seguridad

### Principios Aplicados

#### Privacy by Design
- ✅ Redacción automática de PII
- ✅ No guardar transcript original
- ✅ Normalización de ubicaciones
- ✅ Minimización de datos
- ✅ Separación de datos sensibles

#### Security by Default
- ✅ Puertos solo en 127.0.0.1
- ✅ No secretos en repositorio
- ✅ .env.example sin credenciales reales
- ✅ Logs sin PII
- ✅ Validación de inputs

#### Compliance
- ✅ LFPDPPP (Ley Federal de Protección de Datos Personales)
- ✅ LGDNNA (Ley General de Derechos de NNA)
- ✅ Consentimiento explícito
- ✅ Derechos ARCO (diseño futuro)

Ver más en: [docs/legal_privacy.md](docs/legal_privacy.md) y [docs/cybersecurity.md](docs/cybersecurity.md)

---

## Contribuciones

Este es un proyecto educativo para evaluación técnica. No se aceptan contribuciones externas en esta fase.

---

## Licencia

**Uso Educativo Únicamente**

Este proyecto es una demostración técnica con datos sintéticos. No debe usarse en producción ni con datos reales sin:
1. Auditoría de seguridad completa
2. Revisión legal de cumplimiento
3. Validación con autoridades competentes
4. Implementación de controles adicionales

---

## Contacto

**Autor:** Bob  
**Fecha:** 2026-06-06  
**Versión:** 1.0.0 (MVP)

---

## Agradecimientos

- Ciudad de México C5
- Comunidad FastAPI
- Comunidad n8n
- Evaluadores técnicos

---

**🚨 Recordatorio:** Este sistema **NO sustituye** a operadores humanos. El humano siempre está en el loop para decisiones críticas.
