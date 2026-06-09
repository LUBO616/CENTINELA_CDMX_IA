# CENTINELA_CDMX_IA

> **Sistema multiagente de asistencia en tiempo real para operadores del 911 — Ciudad de México**

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker Compose](https://img.shields.io/badge/docker--compose-ready-2496ED.svg)](https://docs.docker.com/compose/)
[![Stack: 100% Open Source](https://img.shields.io/badge/stack-100%25%20open%20source-brightgreen.svg)](#stack)
[![Human in the Loop](https://img.shields.io/badge/human--in--the--loop-invariable-critical.svg)](#principio-rector)

---

## El problema

El sistema 911 de la Ciudad de México recibe más de **13 millones de llamadas por trimestre**. Solo el **28.2% son emergencias reales** — el resto son llamadas mudas, incompletas, bromas o errores de marcación.

Dentro de ese 28%, cada operador debe clasificar, priorizar y canalizar en segundos, bajo presión intensa, con información parcial o ambigua, **sin apoyo automatizado para detectar señales críticas que pueden pasar desapercibidas**.

Una señal omitida en una llamada silenciosa, una emergencia médica confundida con una broma, un NNA en peligro clasificado como incidente menor — las consecuencias son irreversibles.

| Cifra | Fuente: SESNSP, Q1 2026 |
|---|---|
| Total de llamadas recibidas | **13,158,317** |
| Emergencias reales (procedentes) | **3,712,428** — 28.2% |
| Llamadas improcedentes | **9,445,889** — 71.8% |
| CDMX — proporción nacional en emergencias reales | **8.7%** (~323,000 llamadas) |
| Seguridad (incidente más frecuente) | **54%** de procedentes |
| Llamadas mudas (mayor categoría improcedente) | **58.6%** de improcedentes |

---

## Qué es CENTINELA

CENTINELA es un sistema de asistencia a operadores del 911. **No reemplaza al operador — trabaja en paralelo para que decida mejor, más rápido.**

Durante una llamada activa, el sistema:

- Transcribe el audio en tiempo real y **redacta automáticamente datos personales** antes de cualquier procesamiento
- **Detecta señales críticas** que no deben omitirse: armas, incendio, violencia, NNA en peligro, personas inconscientes
- **Sugiere un nivel de riesgo 1–10** con justificación visible y corregible por el operador en cualquier momento
- **Detecta si la voz es sintética o deepfake** — amenaza emergente real para líneas de emergencia
- **Detecta llamadas duplicadas** del mismo evento sin degradar el nivel de riesgo ante señales de vida
- **Propone la autoridad competente** con base legal documentada para que el operador decida la canalización
- **Muestra preguntas mínimas recomendadas** según el tipo de incidente

En paralelo, genera analítica geoespacial near-real-time para supervisión operativa y pre-posicionamiento de unidades.

### Principio rector

> **El operador humano tiene la decisión final en todo momento. La IA asiste y sugiere — nunca reemplaza, nunca descarta por su cuenta, nunca canaliza sin autorización del operador.**

Este principio no es una declaración de intenciones. Está implementado como restricción técnica verificable en cada componente del sistema.

---

## Lo que la IA hace y lo que no hace

| ✅ La IA hace | ❌ La IA NO hace |
|---|---|
| Transcribe la llamada en tiempo real | Hablar directamente con el ciudadano |
| Redacta PII antes de registrar | Tomar decisiones de despacho |
| Sugiere nivel de riesgo con justificación visible | Cerrar o descartar una llamada autónomamente |
| Detecta grupos vulnerables (NNA, adultos mayores, mujeres) | Degradar riesgo ante señales críticas P0 |
| Muestra preguntas mínimas recomendadas al operador | Reemplazar al operador en ningún punto del flujo |
| Alerta si detecta voz sintética o deepfake | Perfilar ni vigilar a personas identificables |
| Sugiere autoridad primaria y coadyuvantes con base legal | Emitir diagnóstico médico definitivo |
| Alimenta analítica geoespacial near-real-time | Compartir datos sin autorización explícita del ciudadano |

---

## Flujo de operación

```
CIUDADANO llama al 911
         │
         ▼
OPERADOR HUMANO recibe y conduce la llamada
         │
         ├─────────────────────────────────────────────────────────┐
         │              CENTINELA trabaja en paralelo              │
         │                                                         │
         │  [A1 Recolector]  → transcribe · redacta PII           │
         │  [A3 Centinela]   → detecta voz sintética / deepfake   │
         │  [A2 Correlador]  → detecta duplicados                 │
         │  [A4 Triador]     → sugiere nivel de riesgo 1–10       │
         │                      + autoridad competente             │
         │                      + preguntas mínimas                │
         └─────────────────────────────────────────────────────────┘
         │
         ▼
OPERADOR confirma, corrige y decide la canalización
         │
         ▼
┌─────────────────────────────────────────────┐
│  Gate SOLID — Consentimiento del ciudadano  │
│  Sí → remite datos a autoridad competente   │
│  No → atiende sin compartir datos           │
└─────────────────────────────────────────────┘
         │
         ▼
Datos ingresan a analítica
  [A5 Cartógrafo] → hotspots geoespaciales H3 · normalizado INEGI 2020
  [A6 Estratega]  → pre-posicionamiento de unidades · OR-Tools
         │
         ▼
Dashboard de supervisión · Seguimiento CDMX
```

---

## Arquitectura

El sistema opera en dos capas complementarias.

### Capa 1 — Prototipo funcional (disponible hoy)

Tres microservicios FastAPI orquestados por n8n. Se levanta con `docker compose up`. Datos sintéticos. Listo para demostración técnica y evaluación.

```
┌─────────────────────────────────────────────────────┐
│                  Dashboard (frontend)                │
│          Panel del operador en tiempo real           │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│           n8n — Orquestador central                  │
│        POST /webhook/911-call                        │
└────────┬──────────────┬──────────────┬──────────────┘
         │              │              │
         ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│  api-ingest  │ │  api-triage  │ │  api-analytics   │
│   :8001      │→│   :8002      │→│   :8003          │
│  Redacta PII │ │  Riesgo 1–10 │ │  Métricas · Gini │
└──────┬───────┘ └──────┬───────┘ └──────┬───────────┘
       └────────────────┴────────────────┘
                        │
                        ▼
           ┌────────────────────────┐
           │    PostgreSQL :5432    │
           │  raw · core · analytics│
           └────────────────────────┘
```

### Capa 2 — Arquitectura multiagente para producción

Sistema de 7+1 agentes MCP sobre BeeAI, orquestados por n8n, comunicados por Redis Streams. Cada agente es un servidor MCP independiente en Python diseñado para operar con datos reales del 911 en tiempo real.

```
CAMINO CALIENTE — tiempo de respuesta por llamada
─────────────────────────────────────────────────────────────────────
Audio ──▶ [A1 Recolector] ──▶ [A3 Centinela ∥ A2 Correlador]
                                            │
                                            ▼
                                      [A4 Triador]
                                            │
                                            ▼
                               Panel del operador humano
                               (confirma · corrige · canaliza)

CAMINO NEAR REAL-TIME — ventanas de minutos
─────────────────────────────────────────────────────────────────────
[A5 Cartógrafo] ──▶ [A6 Estratega]
       │                   │
 Hotspots H3          Pre-posicionamiento
 (INEGI norm.)        de unidades (OR-Tools)

COORDINACIÓN Y GOBERNANZA
─────────────────────────────────────────────────────────────────────
[A7 Bravo]    Orquesta A1–A6 · impide cierre sin operador en nivel ≥5
[A8 Auditor]  Auditoría semanal de equidad, sesgo y falsos negativos
              → Obligatorio con datos reales
```

---

## Roster de agentes (7 + 1)

| ID | Agente | Función operativa | Output clave |
|---|---|---|---|
| **A1** | **Recolector** — Data Steward | Transcribe en tiempo real · redacta PII · detecta señales de contexto del llamante | `transcript · caller_context_flags · medical_red_flags · speech_constraints` |
| **A2** | **Correlador** — Correlación | Detecta si la llamada es duplicado o probable broma · nunca degrada riesgo ante señales críticas | `trust_score · is_nonproc · duplicate_of` |
| **A3** | **Centinela** — Deepfake | **Red neuronal** (wav2vec2/WavLM → AASIST3): alerta si detecta voz sintética · nunca auto-descarta | `synthetic_prob · decision · fpr · fnr` |
| **A4** | **Triador** — Triage | Sugiere nivel 1–10 · detecta grupos vulnerables · propone autoridad competente · muestra preguntas mínimas | `risk_level · branch · primary_authority · best_interest_child · human_required` |
| **A5** | **Cartógrafo** — Geo-temporal | Hotspots H3 normalizados por población INEGI para supervisión y toma de decisiones | `hotspots[h3, risk_norm] · peaks[dim, intensity]` |
| **A6** | **Estratega** — Optimización | Pre-posicionamiento de unidades · proyecta minutos de respuesta ganados | `placements · projected_minutes_saved` |
| **A7** | **Bravo** — Coordinador | Orquesta A1–A6 · produce `primary_authority + legal_basis_tag` · bloquea cierre sin operador en nivel ≥5 | `trace_id · payload consolidado` |
| **A8*** | **Auditor** — Gobernanza | Auditoría semanal: disparidad alcaldía · sesgo Centinela · falsos negativos médicos / NNA / violencia de género | Reporte semanal de equidad |

> *A8 es **obligatorio** cuando el sistema opera con datos reales del 911.

---

## Prioridad P0 — Señales que nunca pueden ignorarse

El sistema identifica señales que ningún agente puede usar para clasificar una llamada como improcedente, cerrarla o degradar su nivel de riesgo:

**Señales P0:** arma · fuego · explosión · gas · sustancia química · intento suicida · persona inconsciente · dificultad respiratoria · sangrado grave · pérdida de libertad · desaparición · violencia sexual · violencia familiar · violencia contra mujeres · NNA en peligro · adulto mayor en abandono o maltrato · persona con discapacidad en riesgo · imposibilidad de hablar libremente.

Toda llamada **silenciosa, incompleta, interrumpida, con gritos, llanto, respiración agitada, clave verbal o terceros controlando la conversación** se trata como incidente incierto y genera alerta inmediata al operador.

### Escala de niveles de riesgo

| Nivel | Categoría | Ejemplos representativos | Acción del sistema |
|---|---|---|---|
| **10** | Riesgo extremo inmediato | Disparos activos · secuestro en curso · paro cardiorrespiratorio · incendio con personas atrapadas · feminicidio tentado · NNA en peligro inmediato | Alerta P0 · despacho prioritario sugerido · autoridad primaria + coadyuvante · CAD |
| **9** | Riesgo crítico alto | Violencia contra la mujer con amenaza activa · robo con violencia · convulsión prolongada · NNA extraviado | Despacho inmediato sugerido · seguimiento activo |
| **8** | Riesgo alto | Violencia familiar sin arma · crisis de salud mental con riesgo indirecto · embarazo con dolor intenso o sangrado | Validación asistida · transferencia inmediata ante cualquier agravante |
| **7** | Riesgo alto-medio | Hecho en curso sin lesión grave confirmada · llamada interrumpida con contexto riesgoso | Preguntas mínimas recomendadas · escalar si hay incertidumbre |
| **6** | Riesgo medio / posible escalamiento | Reportes ambiguos con señales de riesgo · accidente con NNA · olor a gas leve | Validación intermedia · canalización según competencia |
| **5** | Validación intermedia obligatoria | Reportes incompletos · posible broma con señales de fondo | Sistema repregunta · escalar si sube el riesgo |
| **4** | Bajo con seguimiento | Daños materiales menores · orientación · servicio público sin riesgo actual | Orientar · registrar · canalizar · ofrecer derivación |
| **3** | Bajo | Reporte informativo · incidente ya atendido sin nuevo riesgo | Orientar y registrar trazabilidad mínima |
| **2** | Mínimo | Error de marcación confirmado sin ruido de emergencia | Informar uso adecuado del 911 y cerrar con registro |
| **1** | No emergencia confirmada | Broma explícita · prueba técnica autorizada | Cierre con registro — **Nunca usar si la persona no puede hablar o cuelga abruptamente** |

### Matriz de cálculo — A4 Triador

| Dimensión | Peso |
|---|---|
| Severidad material del hecho | **40%** |
| Tiempo crítico de atención | **25%** |
| Riesgo de escalamiento | **20%** |
| Vulnerabilidad e interseccionalidad | **15%** |

Con histórico operativo: `Prioridad agregada = 75% riesgo normalizado + 25% volumen relativo`
El riesgo individual de la llamada en curso **siempre prevalece** sobre el volumen histórico.

### Grupos de protección reforzada

La IA detecta y alerta al operador cuando la llamada involucra:

**NNA · Jóvenes · Mujeres · Adultos mayores · Personas con discapacidad · Migrantes o con protección internacional · Pueblos indígenas · Defensores de derechos humanos · Periodistas · Personas en desplazamiento forzado · Personas en situación de calle · Comunidad LGBTTTI**

Estas categorías se usan **exclusivamente para priorización protectora** — nunca para perfilar, vigilar ni discriminar. Para NNA: `best_interest_child: true` como criterio de desempate. Para dos o más categorías en intersección: `vulnerability_multiplier` auditable.

### Canalización sugerida al operador por A7 Bravo

| Tipo de llamada | Autoridad primaria sugerida | Coadyuvantes sugeridas |
|---|---|---|
| Emergencia médica (paro, infarto, EVC, trauma, parto) | Secretaría de Salud CDMX / SEM | C5/C2 · Protección Civil · policía si hay riesgo |
| Crisis psicológica · suicidio · autolesión | Secretaría de Salud CDMX | SIBISO · DIF-CDMX · C5 · FGJ si hay delito |
| Violencia contra mujeres · violencia familiar · sexual | Fiscalía General de Justicia CDMX | Secretaría de las Mujeres · policía · salud · DIF |
| NNA en riesgo · abandono · maltrato · extravío | Procuraduría de Protección NNA / DIF-CDMX | FGJ · salud · educación |
| Incendio · explosión · fuga de gas · derrame químico | Protección Civil / bomberos / C5 | Salud · policía · alcaldía · autoridad ambiental |
| Hecho delictivo · arma · robo con violencia | Seguridad pública / policía competente | FGJ · salud · C5 |
| Servicio público con riesgo (cables, socavón) | Alcaldía o dependencia competente | Protección Civil · C5 · policía |
| Personas en calle · migrantes · abandono social | SIBISO | DIF-CDMX · salud · alcaldía · FGJ si hay delito |
| Llamada silenciosa o con coacción | C5/C2 — alerta inmediata al operador | Policía · salud · protección civil según señales acústicas |

---

## Métricas de impacto

### Equidad geográfica — Coeficiente de Gini

| Escenario | Gini | Significado |
|---|---|---|
| Sin sistema (línea base) | **0.42** | Alcaldías con mayor volumen acaparan recursos independientemente del riesgo per cápita real |
| Con CENTINELA | **0.28** | Supera el umbral de éxito (≤0.35) tras normalización INEGI 2020 |

Una emergencia tiene la misma probabilidad de ser priorizada correctamente sin importar si ocurre en una zona densamente poblada o marginada.

Datos de referencia poblacional: **Censo de Población y Vivienda INEGI 2020** — incluido en el repositorio como `ITER_09CSV20.csv` (Ciudad de México, 9.2M habitantes, desagregado por AGEB y localidad).

### Impacto operativo esperado

- Reducción de carga cognitiva del operador durante la llamada activa
- Detección de señales P0 que pueden omitirse en llamadas ambiguas, silenciosas o interrumpidas
- Protección activa de grupos vulnerables como factor de priorización, no de discriminación
- Detección de voz sintética e inundación automatizada del canal 911 (AASIST3)
- Analítica geoespacial near-real-time con normalización poblacional real
- Equidad auditada semanalmente (A8) con métricas verificables

---

## Stack tecnológico

Todo el sistema usa herramientas de código abierto. No hay dependencias de servicios propietarios en tiempo de ejecución.

| Capa | Referencia de diseño | Alternativas compatibles |
|---|---|---|
| **Runtime de agentes** | BeeAI + MCP | Cualquier framework compatible con MCP |
| **LLM local** | IBM Granite (via Ollama) | Llama 3 · Mistral · Qwen · cualquier modelo local vía Ollama |
| **Embeddings** | nomic-embed · bge | Cualquier modelo compatible con Qdrant |
| **Vector / RAG** | Qdrant | Weaviate · Milvus · pgvector |
| **STT** | faster-whisper · Vosk | Whisper.cpp · cualquier STT local |
| **TTS** | Piper · Kokoro | *(NO Coqui XTTS — licencia no-comercial)* |
| **Voz / transporte** | LiveKit · Asterisk/FreeSWITCH | — |
| **Detección deepfake** | wav2vec2/WavLM + AASIST3 | Distribución: ASVspoof5 / Codecfake / in-the-wild |
| **Geo** | H3 (Uber) · PostGIS · TimescaleDB | — |
| **Optimización** | OR-Tools (Apache 2.0) | — |
| **Bus de eventos** | Redis Streams · Valkey | Kafka a escala |
| **Orquestación** | n8n (fair-code) | Node-RED · Windmill |
| **Dashboards** | Grafana · Superset · MapLibre · Kepler.gl | — |
| **Base de datos** | PostgreSQL · TimescaleDB | — |
| **Contenedores** | Docker Compose | Kubernetes para producción |

> La arquitectura es agnóstica al LLM. IBM Granite es la referencia de diseño, pero cualquier modelo de lenguaje local con capacidad de razonamiento estructurado es compatible con A1, A2, A4, A6 y A7. A3 Centinela usa una red neuronal de audio (AASIST3) — no un LLM.

---

## Privacidad y cumplimiento normativo

### Privacy by Design — Implementación técnica

- La transcripción original **nunca se almacena sin redactar**
- PII (nombre, teléfono, dirección, datos de salud) se redacta automáticamente en A1 antes de cualquier procesamiento posterior
- **Cero PII** en logs, bus de mensajería y salidas de agentes — regla técnica absoluta
- Separación de datos en tres esquemas independientes: `raw` · `core` · `analytics`
- El ciudadano autoriza explícitamente antes de que sus datos se remitan a una autoridad (gate SOLID, LFPDPPP Art. 8)

### Marco normativo cubierto

| Marco | Cobertura técnica implementada |
|---|---|
| **LFPDPPP** | Redacción de PII · minimización de datos · consentimiento explícito (Art. 8) · separación de esquemas (Art. 19) |
| **LGDNNA** | `best_interest_child` · elevación automática de prioridad · bloqueo técnico de degradación en casos NNA |
| **Ley General de Seguridad Pública** | Opera como apoyo tecnológico sin sustituir atribuciones legales |
| **ISO/IEC 27001:2022** | Mínimo privilegio por agente · separación de capas · cero PII en bus |
| **NIST AI RMF 1.0** | MAP + MEASURE + MANAGE implementados como restricciones técnicas verificables |
| **OWASP AI Top 10 (2025)** | Sin inyección de instrucciones · salidas JSON estructurado validado · sin agencia excesiva |
| **ISO/IEC 42001:2023** | Sistema de gestión de IA con ciclo de mejora continua y auditoría |
| **UNESCO Ética IA (2021)** | 10 principios implementados como restricciones técnicas, no declaraciones |
| **Privacy by Design (Cavoukian)** | 7 principios fundacionales integrados en la arquitectura base |

Documentación de cumplimiento completa: [`docs/legal_compliance.md`](docs/legal_compliance.md)

---

## Estructura del repositorio

```
CENTINELA_CDMX_IA/
├── services/
│   ├── api-ingest/           A1 Recolector — STT + redacción PII
│   ├── api-triage/           A4 Triador — clasificación 1–10
│   └── api-analytics/        A5/A6 — métricas y predicciones geoespaciales
├── database/
│   └── init.sql              Schemas: raw · core · analytics
├── n8n/workflows/            WF-1 (cron) · WF-2 (webhook) · WF-3 (auditoría)
├── lovable-dashboard/        Frontend del panel de operador
├── scripts/                  Setup · start · stop · test · seed
├── docs/
│   ├── architecture.md       Diseño del sistema · decisiones
│   ├── agents/               Especificación canónica A1–A8
│   ├── api_contract.md       OpenAPI specs · JSON schemas
│   ├── legal_compliance.md   LFPDPPP · LGDNNA · UNESCO · NIST
│   ├── cybersecurity.md      Controles · threat model · AASIST3
│   └── data_sources.md       INEGI 2020 · SESNSP · fuentes normativas
├── evidence/                 Capturas del sistema en operación
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Instalación rápida

### Requisitos

```
Docker >= 20.10
Docker Compose >= 2.0
jq · curl · Git
```

### Levantar el sistema

```bash
git clone https://github.com/LUBO616/CENTINELA_CDMX_IA.git
cd CENTINELA_CDMX_IA

# Configurar variables de entorno
cp .env.example .env
# Editar POSTGRES_PASSWORD y N8N_BASIC_AUTH_PASSWORD

# Verificar requisitos del sistema
./scripts/00_precheck.sh

# Levantar todos los servicios
./scripts/01_start.sh all
sleep 15

# Validar instalación completa
./scripts/04_test_environment.sh all
```

### Acceso a servicios

| Servicio | URL | Credenciales por defecto |
|---|---|---|
| n8n (orquestador) | http://localhost:5678 | admin / changeme |
| api-ingest (docs) | http://localhost:8001/docs | — |
| api-triage (docs) | http://localhost:8002/docs | — |
| api-analytics (docs) | http://localhost:8003/docs | — |
| PostgreSQL | localhost:5432 | emergency_user / changeme |

### Comandos de operación

```bash
./scripts/01_start.sh infra           # Solo infraestructura
./scripts/01_start.sh all             # Sistema completo
./scripts/03_logs.sh api-triage       # Logs de un servicio específico
./scripts/02_stop.sh                  # Detener todo
./scripts/05_seed_demo_data.sh direct # Cargar datos de demostración
./scripts/06_test_n8n_webhook.sh      # Probar flujo completo
```

---

## API

### Webhook principal

**`POST http://localhost:5678/webhook/911-call`**

**Request de ejemplo — emergencia crítica:**
```json
{
  "transcript": "Hay un incendio en mi edificio, hay personas atrapadas en el tercer piso",
  "metadata": {
    "source": "operator_dashboard",
    "timestamp": "2026-06-08T14:30:00Z"
  },
  "location_hint": "Colonia del Valle, Benito Juárez",
  "solid_consent": true
}
```

**Response:**
```json
{
  "success": true,
  "call_id": "c8a4f1d2-...",
  "trace_id": "t9b3e2a1-...",
  "risk_level": 10,
  "branch": "critical",
  "case_category": "protection_civil",
  "human_required": true,
  "p0_signals": ["incendio", "personas atrapadas"],
  "primary_authority": "Protección Civil CDMX / Bomberos",
  "support_authorities": ["C5", "Secretaría de Salud CDMX"],
  "best_interest_child": false,
  "protected_group_flags": [],
  "public_stage_phrase": "Nivel 10. Incendio con personas atrapadas. Operador: despacho prioritario.",
  "rationale_public": "Señales P0: incendio activo con personas en el interior. Nivel sugerido: 10. Decisión final: operador.",
  "processed_at": "2026-06-08T14:30:01Z"
}
```

### Endpoints de analítica

```
GET http://localhost:8003/analytics/summary
GET http://localhost:8003/analytics/predictions
```

---

## Gates de validación

### Capa 1 — Prototipo funcional

| Gate | Criterio de éxito |
|---|---|
| **1 — Infraestructura** | PostgreSQL activo · schemas raw/core/analytics creados · n8n accesible |
| **2 — Microservicios** | Flujo ingest→triage→analytics · 18 tests pasan · trace_id preservado end-to-end |
| **3 — Workflow n8n** | Webhook `/webhook/911-call` activo · escenarios low/mid/critical funcionan correctamente |
| **4 — Privacidad** | Sin PII en analytics · sin direcciones completas expuestas · PII no aparece en ningún log |

### Capa 2 — Arquitectura multiagente

| Gate | Agentes | Criterio |
|---|---|---|
| **1** | Bus + esquema | Redis Streams activo · esquema canónico C5 validado contra diccionario |
| **2** | A1 + A2 | `test()` verde · flujo STT → correlación · cero PII en salidas |
| **3** | A3 Centinela | Checkpoint AASIST3 cargado · FPR/FNR declarados · distribución verificada — **requiere aprobación explícita** |
| **4** | A4 Triador | Triage 1–10 consumiendo trust de A2+A3 · todos los niveles probados |
| **5** | A5 + A6 | Normalización INEGI verificada · OR-Tools optimizando placements |
| **6** | A7 + integración | Workflows n8n exportados como JSON · bus integrado end-to-end |

### Definition of Done por agente

- Implementa los 6 componentes canónicos (o declara los ausentes con justificación documentada)
- `test()` pasa sin red externa · salida valida contra JSON schema del contrato
- Cero PII en código, logs, salidas y eventos del bus
- Modelo declara versión + distribución de entrenamiento + punto de operación (FPR/FNR cuando aplica)
- Emite `trace_id` y expone su plan en la traza

---

## Documentación completa

| Documento | Contenido |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Diseño del sistema · diagramas · decisiones de arquitectura |
| [`docs/agents/`](docs/agents/) | Especificación canónica A1–A8 con schemas y `test()` |
| [`docs/api_contract.md`](docs/api_contract.md) | OpenAPI specs · JSON schemas de todos los agentes |
| [`docs/legal_compliance.md`](docs/legal_compliance.md) | LFPDPPP · LGDNNA · NIST AI RMF · UNESCO · OWASP · ISO |
| [`docs/cybersecurity.md`](docs/cybersecurity.md) | Controles · threat model · A3 Centinela · análisis de amenazas |
| [`docs/data_sources.md`](docs/data_sources.md) | INEGI 2020 · SESNSP · fuentes normativas con DOI y URLs |
| [`docs/n8n_workflows.md`](docs/n8n_workflows.md) | WF-1 (cron) · WF-2 (webhook) · WF-3 (auditoría semanal) |

---

## Consideraciones para producción

Este repositorio contiene un prototipo funcional con datos sintéticos. Antes de operar con datos reales del 911, se requiere completar:

1. **Cifrado en tránsito (TLS)** en el bus de eventos y todas las interfaces de servicio
2. **Autenticación mutua entre agentes** MCP en entorno de producción
3. **A8 Auditor activo** como guarda transversal permanente — obligatorio con datos reales
4. **Calibración de A3 Centinela** con llamadas reales del 911 CDMX para ajustar FPR/FNR a la distribución local
5. **Aviso de privacidad institucional** conforme a LFPDPPP Art. 15 emitido por la institución operadora
6. **Auditoría de seguridad independiente** del sistema completo
7. **Validación con autoridades competentes** (C5 CDMX, SSA, FGJ) antes del despliegue

---

## Contribuir

Las contribuciones son bienvenidas. El proyecto está diseñado para ser tecnológicamente abierto.

Para contribuciones al modelo de detección de deepfake (A3 Centinela), verifica que el conjunto de datos de entrenamiento sea reciente — ASVspoof5 / Codecfake / in-the-wild. **ASVspoof 2019 no es suficiente** para distribuciones actuales de voz sintética.

---

## Licencia

**Apache License 2.0**

Este proyecto puede usarse, modificarse y distribuirse libremente bajo los términos de la licencia Apache 2.0. Ver [`LICENSE`](LICENSE) para el texto completo.

---

**CENTINELA_CDMX_IA** · Sistema multiagente para operadores del 911 · Ciudad de México  
Stack 100% open source · Privacy by Design · Human-in-the-Loop invariable  
Concienc.ia Hackathon 2026 · Young AI Leaders Community CDMX — origen del proyecto
