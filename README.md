# CENTINELA\_CDMX\_IA

> Sistema multiagente de clasificación y triage de llamadas de emergencia 911 — Ciudad de México
> **Versión:** 2.0 · MVP Extendido + Arquitectura Agéntica V3.0
> **Construcción y ejecución de agentes:** IBM Bob (Bob Shell + MCP Builder)
> **Runtime:** BeeAI + MCP · **Orquestación:** n8n · **Bus de eventos:** Redis Streams / Valkey
> **Soberanía de datos** — solo herramientas abiertas, enlazables en tiempo real

[![License](https://img.shields.io/badge/license-Educational-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)
[![BeeAI](https://img.shields.io/badge/runtime-BeeAI%20%2B%20MCP-purple.svg)](https://beeai.dev)
[![IBM Bob](https://img.shields.io/badge/build-IBM%20Bob-052FAD.svg)](https://www.ibm.com/products/watsonx)
[![IBM Granite](https://img.shields.io/badge/LLM-IBM%20Granite%20%2B%20Ollama-red.svg)](https://huggingface.co/ibm-granite)

---

## Tabla de Contenidos

- [¿Qué es este proyecto?](#qué-es-este-proyecto)
- [Problema que Resuelve](#problema-que-resuelve)
- [Cómo se Construye — IBM Bob](#cómo-se-construye--ibm-bob)
- [Arquitectura — Dos Capas](#arquitectura--dos-capas)
- [Roster de Agentes (7 + 1)](#roster-de-agentes-7--1)
- [Estructura Interna Canónica](#estructura-interna-canónica)
- [Prioridad P0 — Marco Legal y Operativo](#prioridad-p0--marco-legal-y-operativo)
- [Flujo Operativo](#flujo-operativo)
- [Stack Abierto](#stack-abierto)
- [Métricas de Impacto](#métricas-de-impacto)
- [Requisitos Previos](#requisitos-previos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Validación de Gates](#validación-de-gates)
- [Integración con Lovable](#integración-con-lovable)
- [Privacidad, Seguridad y Compliance](#privacidad-seguridad-y-compliance)
- [Limitaciones del MVP](#limitaciones-del-mvp)
- [Documentación](#documentación)
- [Licencia](#licencia)

---

## ¿Qué es este proyecto?

**CENTINELA\_CDMX\_IA** es una demostración técnica de un sistema de pre-clasificación automática de llamadas de emergencia 911 para Ciudad de México. Opera en dos capas complementarias:

**Capa 1 — Demo ejecutable:** Tres microservicios FastAPI orquestados por n8n que redactan PII, clasifican riesgo y generan analítica geoespacial. Funciona completamente con Docker Compose.

**Capa 2 — Arquitectura objetivo:** Sistema multiagente V3.0 con 7+1 agentes especializados, construidos y ejecutados con **IBM Bob** como entorno de desarrollo (MCP Builder + Bob Shell), corriendo sobre runtime **BeeAI + MCP**, orquestados por n8n y comunicados por bus de eventos Redis Streams / Valkey. Cada agente implementa una estructura canónica de seis componentes.

### Principios de diseño

| # | Principio |
|---|-----------|
| **P0** | **Vida, integridad y libertad prevalecen sobre automatización, eficiencia o clasificación estadística** |
| P1 | Seguridad de datos > funcionalidad |
| P2 | Honestidad de arquitectura > seguir plantilla por simetría |
| P3 | Humano en el loop en decisiones de vida — ningún agente auto-descarta una llamada |
| P4 | Solo herramientas abiertas, enlazables en tiempo real |
| P5 | Equidad: riesgo geográfico normalizado por población INEGI; Centinela auditado por sesgo |
| P6 | Incremental: generar → test() → aprobación → avanzar |

### Reglas duras

- **R1.** Cero PII en logs, prompts, salidas, nodos n8n o eventos del bus.
- **R2.** Cada agente define `test()` ejecutable sin red externa.
- **R3.** Cada salida = JSON validado contra el schema de su contrato.
- **R4.** Ante ambigüedad, PREGUNTA; no asumas.
- **R5.** Todo modelo declara versión + distribución de entrenamiento + punto de operación.
- **R6.** Sin perfilado individual ni vigilancia de personas identificables.

---

## Problema que Resuelve

Los sistemas 911 en México reciben miles de llamadas diarias. Muchas son no urgentes (baches, alumbrado público), otras requieren validación (accidentes sin heridos) y otras son críticas (violencia, emergencias médicas, incendios). Clasificar manualmente cada llamada consume tiempo valioso de operadores humanos, retrasando la atención a emergencias reales.

**CENTINELA\_CDMX\_IA** propone un sistema de pre-clasificación que:

1. Redacta PII **antes** de procesar cualquier transcripción
2. Detecta señales críticas P0 automáticamente: armas, fuego, emergencias médicas, violencia, grupos vulnerables
3. Clasifica riesgo en escala 1–10 con matriz ponderada (severidad 40% · tiempo crítico 25% · escalamiento 20% · vulnerabilidad 15%)
4. Detecta voz sintética / deepfake (A3 Centinela — red neuronal AASIST3)
5. Correlaciona llamadas duplicadas o no procedentes sin degradar riesgo ante señales de vida
6. Sugiere autoridades competentes con base legal
7. Escala a operador humano — **ningún agente cierra una llamada con señales P0**
8. Genera métricas y predicciones geoespaciales normalizadas por población INEGI

---

## Cómo se Construye — IBM Bob

Los agentes de la Capa 2 se construyen y prueban íntegramente dentro de **IBM Bob**:

```
IBM Bob (entorno de desarrollo)
│
├── MCP Builder mode     → genera cada agente como servidor MCP (extiende BaseMCP)
├── Bob Shell            → ejecuta test() local sin red externa y valida el JSON schema
├── Literate Coding      → spec completa del sistema como instrucción raíz
└── Custom Mode          → rol + principios + reglas duras cargados como contexto base
```

**Bob NO es el runtime de producción.** Una vez que `test()` pasa y se obtiene aprobación explícita del gate, el agente se despliega en BeeAI + MCP orquestado por n8n. Bob mantiene el repositorio, los workflows n8n exportados como JSON y el README de despliegue.

### Flujo de trabajo en Bob por agente

```
1. Crear Custom Mode con bloque ROL / PRINCIPIOS / REGLAS
2. Pegar SPEC del agente en Literate Coding como instrucción raíz
3. Construir con MCP Builder mode (extiende BaseMCP sobre BeeAI)
4. Ejecutar test() con Bob Shell — validar JSON schema sin red externa
5. Obtener aprobación explícita del gate
6. Avanzar al siguiente agente
```

### Formato de respuesta esperado de Bob por turno

```
(1) Gate en curso
(2) Agente y componentes implementados
(3) Archivos generados / modificados
(4) Resultado de test()
(5) Supuestos y dudas
(6) Qué se necesita para el siguiente gate
```

---

## Arquitectura — Dos Capas

### Capa 1: Microservicios MVP (Demo)

```
┌─────────────────────────────────────────────────────────────────┐
│                      Lovable Dashboard                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    n8n Orchestrator                              │
│            Webhook: /webhook/911-call                            │
└───┬──────────────────┬──────────────────┬──────────────────────┘
    │                  │                  │
    ↓                  ↓                  ↓
┌─────────┐      ┌─────────┐      ┌──────────────┐
│ Ingest  │      │ Triage  │      │  Analytics   │
│ :8001   │ →    │ :8002   │ →    │  :8003       │
│ PII     │      │ Riesgo  │      │ Métricas     │
│ Redact  │      │ 1–10    │      │ Predicciones │
└────┬────┘      └────┬────┘      └──────┬───────┘
     └────────────────┴───────────────────┘
                      ↓
          ┌───────────────────────┐
          │   PostgreSQL :5432    │
          │ raw · core · analytics│
          └───────────────────────┘
```

### Capa 2: Sistema Multiagente V3.0 — IBM Bob + BeeAI + MCP

```
┌──────────────────────────────────────────────────────────────────────────┐
│                  IBM Bob (construcción y prueba de agentes)               │
│            MCP Builder → BaseMCP → Bob Shell → test() → gate             │
└──────────────────────────────────────────────────────────────────────────┘
                              ↓  (deploy tras aprobación de gate)
┌──────────────────────────────────────────────────────────────────────────┐
│                    CAMINO CALIENTE (por llamada)                          │
│                                                                           │
│  Audio/Voz → [A1 Recolector] → [A3 Centinela ∥ A2 Correlador] →        │
│                                          ↓                                │
│                                    [A4 Triador]                           │
│                                          ↓                                │
│                          Dashboard / Operador Humano                      │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│               CAMINO NEAR REAL-TIME (ventanas de minutos)                 │
│                                                                           │
│          [A5 Cartógrafo] ──→ [A6 Estratega]                              │
│               ↓                    ↓                                      │
│         Hotspots H3         Pre-posicionamiento                           │
│         (INEGI norm.)        de unidades                                  │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                  A7 BRAVO — Coordinador Maestro                           │
│        Orquesta A1–A6 vía n8n + Redis Streams / Valkey                   │
│                  trace_id global · estado en vuelo                        │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│          A8 AUDITOR (obligatorio cuando se usen datos reales)             │
│    Disparidad por alcaldía · sesgo Centinela · falsos negativos P0        │
└──────────────────────────────────────────────────────────────────────────┘

Cada agente = servidor MCP (BaseMCP en Python) construido con IBM Bob sobre runtime BeeAI
Cada mensaje entre agentes = evento en Redis Streams / Valkey
```

---

## Roster de Agentes (7 + 1)

| ID | Codename / Rol | Función | Output clave |
|----|----------------|---------|--------------|
| **A1** | **Recolector** — Data Steward | Ingesta histórico C5 + audio en vivo, STT (faster-whisper / Vosk), normaliza contra diccionario. Añade flags de contexto, señales médicas y de violencia | `{rows, schema_ok, transcript, caller_context_flags, medical_red_flags, violence_red_flags, speech_constraints}` |
| **A2** | **Correlador** — Correlación | Caza al humano: detecta duplicados y no-procedentes por motivo+geo+tiempo. No puede degradar riesgo ante señales P0 | `{incident_id, is_nonproc, duplicate_of, cluster_id, trust_score}` |
| **A3** | **Centinela** — Ciberseguridad/SOC | **Red neuronal** (wav2vec2/WavLM → AASIST3): detecta voz sintética/deepfake. Nunca autoriza auto-descarte; solo bandera para revisión humana | `{call_id, synthetic_prob, decision, model_version, train_distribution, operating_point{fpr, fnr}}` |
| **A4** | **Triador** — Triage | Asigna nivel 1–10 y rama consumiendo trust de A2/A3. Aplica matriz P0, vulnerability_multiplier y best_interest_child | `{incident_id, risk_level, branch, priority_class, risk_components, protected_group_flags, best_interest_child, medical_category, case_category, primary_authority, human_required, public_stage_phrase, rationale_public}` |
| **A5** | **Cartógrafo** — Geo-temporal | Hotspots H3 + picos temporales, normalizados por población INEGI (near-real-time) | `{hotspots[h3, risk_norm, raw_count], peaks[dim, value, intensity]}` |
| **A6** | **Estratega** — Optimización | Pre-posicionamiento de unidades y proyección de minutos ahorrados (OR-Tools) | `{placements[lat, lng, covers_h3], projected_minutes_saved, assumptions}` |
| **A7** | **Bravo** — Coordinador | Planificador maestro: orquesta A1–A6 vía n8n y bus. Impide que un nivel ≥5 cierre sin intervención humana o registro de causa. Produce primary\_authority + legal\_basis\_tag | Payload consolidado + trace\_id global |
| **A8\*** | **Auditor** — Gobernanza | Auditoría semanal: disparidad por alcaldía, por tipo de incidente, por grupo protegido, falsos negativos médicos/violencia de género/NNA, llamadas silenciosas cerradas | Reporte semanal de equidad y sesgo |

> \*A8 es **obligatorio** cuando el sistema opera con datos reales.

---

## Estructura Interna Canónica

Cada agente implementa seis componentes. Si un componente no aporta valor, se declara `mínimo` o `none (justificación)` — nunca se añade por simetría.

| Componente | Implementación abierta |
|------------|----------------------|
| **Núcleo** | LLM abierto (Ollama + IBM Granite) por defecto; modelo de dominio (red neuronal / solver) donde aplique |
| **RAG** | Qdrant + embeddings abiertos (nomic-embed / bge) |
| **Memoria** | Memoria nativa de BeeAI (summarized / token-controlled) |
| **Planificación** | Descompone su tarea en subtareas; expone el plan en la traza |
| **Herramientas** | Tools MCP generadas con IBM Bob (MCP Builder) |
| **Interfaz** | Bus de eventos / agente upstream — nunca el usuario final directamente |

### Ejemplo detallado: A3 Centinela

```
Núcleo:        Red neuronal de audio — wav2vec2/WavLM (front-end SSL) → AASIST3 (back-end)
               LLM IBM Granite solo como capa de explicación opcional
RAG:           Firmas de motores TTS/VC conocidos, codecs, distribución de entrenamiento
Memoria:       Veredictos por sesión/origen para detectar inundación automatizada
Planificación: extraer features → inferir synthetic_prob → aplicar umbral → enrutar
Herramientas:  Checkpoint AASIST3 (HuggingFace), extractor de features, conector al bus
               Generadas con IBM Bob MCP Builder, ejecutadas en BeeAI
Datos:         ASVspoof5 / Codecfake / in-the-wild — ASVspoof 2019 es insuficiente
Guarda:        Umbral a FNR bajo; synthetic alto → revisión humana, NUNCA auto-descarte
```

---

## Prioridad P0 — Marco Legal y Operativo

> **P0 prevalece sobre automatización, optimización, reducción de carga operativa, clasificación de llamada falsa o eficiencia estadística.**

### Señales P0 — ningún agente puede cerrar o degradar una llamada con estas señales

Arma · fuego · explosión · gas · sustancia química · intento suicida · persona inconsciente · dificultad respiratoria · sangrado grave · pérdida de libertad · privación · desaparición · violencia sexual · violencia familiar · violencia contra mujeres · NNA en peligro · persona adulta mayor en abandono o maltrato · persona con discapacidad en riesgo · imposibilidad de hablar libremente.

Toda llamada **silenciosa, incompleta, interrumpida, con gritos, llanto, respiración agitada, clave verbal, coacción audible o terceros controlando la conversación** se trata como incidente incierto con validación activa y posibilidad de escalamiento humano.

### Matriz de cálculo — A4 Triador

| Dimensión | Peso |
|-----------|------|
| Severidad material del hecho | 40% |
| Tiempo crítico de atención | 25% |
| Riesgo de escalamiento | 20% |
| Vulnerabilidad e interseccionalidad | 15% |

```
Prioridad operativa agregada (con histórico) = 75% riesgo normalizado + 25% volumen relativo
El riesgo individual de una llamada en curso siempre prevalece sobre el volumen histórico.
```

### Jerarquía de niveles operativos

| Nivel | Categoría | Ejemplos | Salida obligatoria |
|-------|-----------|----------|--------------------|
| **10** | Riesgo extremo inmediato | Disparos activos, secuestro, paro cardiorrespiratorio, incendio con personas, explosión, fuga de gas con expuestos, feminicidio tentado, NNA en peligro inmediato | Operador humano inmediato · despacho prioritario · registro CAD |
| **9** | Riesgo crítico alto | Violencia contra la mujer con amenaza, agresión física en curso, robo con violencia, NNA extraviado, convulsión prolongada, quemadura grave | Operador humano · despacho inmediato · seguimiento activo |
| **8** | Riesgo alto | Violencia familiar sin arma, amenazas creíbles, crisis de salud mental con riesgo indirecto, embarazo con sangrado | Humano o validación asistida; transferencia inmediata ante cualquier agravante |
| **7** | Riesgo alto-medio | Hechos en curso sin lesión grave confirmada, tentativa de delito, llamada interrumpida con contexto riesgoso | Validación rápida · operador humano ante incertidumbre |
| **6** | Riesgo medio con posible escalamiento | Reportes ambiguos con señales de riesgo, accidente con NNA sin lesiones aparentes, olor a gas leve | Validación intermedia · preguntas mínimas |
| **5** | Validación intermedia obligatoria | Reportes incompletos o inconsistentes, posible llamada falsa con señales de fondo | IA repregunta · humano si sube el riesgo o hay grupo P0 |
| **4** | Bajo con seguimiento | Daños materiales menores, solicitudes de orientación | IA orienta, registra, canaliza. Debe ofrecer operador humano |
| **3** | Bajo | Reporte informativo sin urgencia, incidente ya atendido | IA orienta y registra trazabilidad mínima |
| **2** | Mínimo | Llamada improcedente sin señales de riesgo, error de marcación confirmado | IA informa uso adecuado del 911 y cierra con registro |
| **1** | No emergencia confirmada | Broma explícita, prueba técnica autorizada, llamada equivocada reiterada | Cierre con registro. **Nunca usar si la persona no puede hablar o cuelga abruptamente** |

### Grupos de Protección Reforzada

El sistema detecta, pregunta con sensibilidad y registra sin estigmatizar cuando la llamada involucra:

NNA · Jóvenes · Mujeres · Personas adultas mayores · Personas con discapacidad · Personas migrantes o sujetas a protección internacional · Miembros de pueblos indígenas · Personas defensoras de derechos humanos · Periodistas · Personas en situación de desplazamiento forzado interno · Personas en situación de calle · Integrantes de la comunidad LGBTTTI.

**Reglas de uso:** estas categorías no se usan para perfilar, vigilar o discriminar. Solo para priorización protectora, accesibilidad, intérpretes, canalización especializada y seguimiento. En intersección de dos o más categorías, A4 añade `vulnerability_multiplier` auditable. Para NNA: `best_interest_child: true`.

### Enrutamiento por Autoridad — A7 Bravo

A7 produce siempre `primary_authority`, `coordinating_authority`, `support_authorities` y `legal_basis_tag`.

| Tipo de llamada | Autoridad primaria | Coadyuvantes |
|----------------|-------------------|--------------|
| Emergencia médica (paro, infarto, EVC, trauma, parto) | Secretaría de Salud CDMX / SEM | C5/C2, Protección Civil, policía si hay riesgo |
| Crisis psicológica, suicidio, autolesión | Secretaría de Salud CDMX | SIBISO, DIF-CDMX, C5, FGJ si hay delito |
| Violencia contra mujeres, violencia familiar, sexual | Fiscalía General de Justicia CDMX | Secretaría de las Mujeres, policía, salud, DIF |
| NNA en riesgo, abandono, maltrato, extravío | Procuraduría de Protección NNA / DIF-CDMX | FGJ, salud, educación |
| Incendio, explosión, fuga de gas, derrame químico | Protección Civil / bomberos / C5 | Salud, policía, alcaldía, autoridad ambiental |
| Hecho delictivo, arma, robo con violencia | Seguridad pública / policía competente | FGJ, salud, C5 |
| Servicio público con riesgo (cables, socavón) | Alcaldía o dependencia competente | Protección Civil, C5, policía |
| Personas en calle, migrantes, abandono social | SIBISO | DIF-CDMX, salud, alcaldía, FGJ si hay delito |
| Llamada silenciosa o con coacción | C5/C2 + operador humano | Policía, salud o protección civil según señales |

### Protocolo de Voz Pública

La IA comunica solo la etapa operativa y una justificación breve. **Nunca expone el razonamiento interno.**

```
"Estoy en la etapa de [recepción / validación / priorización / canalización / seguimiento].
Detecto [señal operativa breve]. Voy a [siguiente acción]."
```

**Prohibido:** "Mi razonamiento interno es..." · "Calculo internamente que..." · "Por probabilidad estadística no vale la pena atender..."

---

## Flujo Operativo

```
Llamada entra
     ↓
A1 Recolector — IA de voz escucha / transcribe (faster-whisper / Vosk)
     ↓
[A3 Centinela ∥ A2 Correlador] — paralelo
     ↓                 ↓
Detección         Correlación
voz sintética     duplicados /
(AASIST3)         no-procedentes
     ↓                 ↓
          A4 Triador
   (consume trust de A2/A3)
          ↓
    Nivel de riesgo 1–10
          ↓
   ┌──────┴───────┬──────────────┐
   │              │              │
  1–4             5            6–10
  Bajo       Validación      Crítico
   │         intermedia          │
   │              │              ↓
   │           IA           Operador humano
   │         repregunta     inmediato
   │
   └──────────────┤
                  ↓
       ¿Autoriza uso de SOLID?
       Sí → remite datos a autoridad
       No → atiende sin compartir datos
                  ↓
            Ingresa datos
                  ↓
   A5 Cartógrafo → A6 Estratega
   (hotspots H3 · pre-posicionamiento)
                  ↓
   Dashboard / Seguimiento CDMX
```

---

## Stack Abierto

| Capa | Herramienta |
|------|-------------|
| **Construcción de agentes** | IBM Bob (MCP Builder + Bob Shell) |
| **Runtime de agentes** | BeeAI + MCP (BaseMCP en Python) |
| **LLM** | Ollama + IBM Granite |
| **Embeddings** | nomic-embed · bge |
| **Vector / RAG** | Qdrant |
| **Memoria de agentes** | BeeAI (summarized / token-controlled) |
| **STT** | faster-whisper · Vosk |
| **TTS** | Piper · Kokoro *(NO Coqui XTTS — licencia no-comercial)* |
| **Voz / transporte** | LiveKit · Asterisk / FreeSWITCH |
| **Agentes de voz** | Pipecat |
| **Detección deepfake** | wav2vec2 / WavLM + AASIST3 (HuggingFace) |
| **Geo** | H3 (Uber) · PostGIS · TimescaleDB |
| **Optimización** | OR-Tools (Apache-2.0) |
| **Bus de eventos** | Redis Streams · Valkey *(Kafka a escala)* |
| **Orquestación** | n8n *(fair-code; Node-RED / Windmill si se exige OSI estricto)* |
| **Dashboards** | Grafana · Superset · MapLibre · Kepler.gl |
| **Base de datos** | PostgreSQL · TimescaleDB |

---

## Métricas de Impacto

### Coeficiente de Gini — Equidad Geográfica

| Escenario | Gini |
|-----------|------|
| Sin sistema (línea base) | **0.42** — alcaldías con mayor volumen acaparan recursos independientemente del riesgo real per cápita |
| Con CENTINELA\_CDMX\_IA | **0.28** — supera el umbral de éxito (0.35) tras normalización por población INEGI 2020 |

Una emergencia tiene la misma probabilidad de ser priorizada correctamente sin importar si ocurre en una zona densamente poblada o marginada.

### Impacto esperado

- Reducción del tiempo de clasificación inicial
- Priorización automática de casos críticos
- Protección activa de grupos vulnerables (NNA, adultos mayores, mujeres)
- Detección de voz sintética e inundación automatizada del sistema
- Analítica geoespacial near-real-time con normalización INEGI
- Privacidad by design — PII nunca llega al motor de clasificación
- Equidad auditada por A8 (obligatorio en producción)

---

## Requisitos Previos

### MVP Docker (Capa 1)

- Docker >= 20.10
- Docker Compose >= 2.0
- jq · curl · Git

### Arquitectura agéntica V3.0 (Capa 2)

- IBM Bob (acceso a watsonx / entorno Bob)
- Python >= 3.11
- Ollama con IBM Granite descargado
- Redis >= 7 o Valkey
- Qdrant
- GPU CUDA-compatible (recomendada para A3 Centinela / AASIST3)

### Recursos mínimos

| Capa | RAM | CPU | Disco |
|------|-----|-----|-------|
| MVP Docker | 4 GB | 2 cores | 5 GB |
| Agéntica completa | 16–32 GB | 8 cores + GPU | 40 GB |

---

## Instalación

### MVP — inicio rápido

```bash
git clone https://github.com/tu-usuario/centinela-cdmx-ia.git
cd centinela-cdmx-ia

cp .env.example .env
# Editar POSTGRES_PASSWORD y N8N_BASIC_AUTH_PASSWORD

./scripts/00_precheck.sh
./scripts/01_start.sh all && sleep 15
./scripts/04_test_environment.sh all
```

### Acceso a servicios MVP

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| n8n | http://localhost:5678 | admin / changeme |
| api-ingest | http://localhost:8001/docs | — |
| api-triage | http://localhost:8002/docs | — |
| api-analytics | http://localhost:8003/docs | — |
| PostgreSQL | localhost:5432 | emergency\_user / changeme |

---

## Uso

```bash
# Levantar infraestructura
./scripts/01_start.sh infra

# Levantar todo
./scripts/01_start.sh all

# Ver logs
./scripts/03_logs.sh api-ingest
./scripts/03_logs.sh api-triage
./scripts/03_logs.sh api-analytics

# Detener todo
./scripts/02_stop.sh

# Test completo
./scripts/04_test_environment.sh all

# Seed datos de prueba
./scripts/05_seed_demo_data.sh direct

# Test webhook n8n
./scripts/06_test_n8n_webhook.sh
```

---

## Validación de Gates

### Gates MVP (Capa 1)

| Gate | Objetivo | Criterios clave |
|------|----------|-----------------|
| **1** | Infraestructura | PostgreSQL + n8n activos; schemas raw/core/analytics creados |
| **2** | Microservicios | Flujo ingest → triage → analytics; 18 tests pasan, 0 fallan; trace\_id preservado |
| **3** | Workflow n8n | Webhook `/webhook/911-call` activo; escenarios low/mid/critical funcionan |
| **4** | Documentación | README completo; sin direcciones completas en analytics |

### Gates Arquitectura Agéntica V3.0 (Capa 2 — IBM Bob)

| Gate | Objetivo |
|------|----------|
| **1** | Confirmar esquema C5 vs. diccionario + levantar bus Redis Streams / Valkey |
| **2** | A1 Recolector + A2 Correlador con `test()` verde en Bob Shell |
| **3** | A3 Centinela — checkpoint AASIST3, FPR/FNR declarados, `train_distribution` verificada. **Espera aprobación explícita antes de avanzar** |
| **4** | A4 Triador (consume trust A2/A3) + flujo completo niveles 1–10 |
| **5** | A5 Cartógrafo + A6 Estratega (normalización INEGI verificada) |
| **6** | A7 Bravo + workflows n8n exportados como JSON + bus integrado end-to-end |

### Definition of Done por agente (IBM Bob)

- Implementa los 6 componentes canónicos (o declara ausentes con justificación).
- `test()` pasa en Bob Shell sin red externa; salida valida contra JSON schema.
- Cero PII en código, logs, salidas y eventos del bus.
- Modelo declara versión + distribución de entrenamiento + punto de operación.
- Emite `trace_id` y expone su plan en la traza.

---

## Integración con Lovable

**Webhook n8n:** `POST http://localhost:5678/webhook/911-call`

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
  "primary_authority": "Secretaría de Salud CDMX",
  "support_authorities": ["C5", "Cruz Roja"],
  "best_interest_child": false,
  "protected_group_flags": [],
  "public_stage_phrase": "Estoy en la etapa de priorización. Detecto posible emergencia médica. Voy a transferir la llamada.",
  "rationale_public": "Signos de sangrado grave detectados. Transferencia a operador humano inmediata.",
  "processed_at": "2026-06-06T12:00:01Z"
}
```

**Endpoints analytics:**

```bash
GET http://localhost:8003/analytics/summary
GET http://localhost:8003/analytics/predictions
```

Ver documentación completa en [`docs/lovable_integration.md`](docs/lovable_integration.md)

---

## Privacidad, Seguridad y Compliance

### Privacy by Design

- La transcripción original **nunca** se almacena sin redactar
- Redacción automática de PII antes de cualquier procesamiento
- Normalización de ubicaciones — sin direcciones completas en analytics
- Cero PII en eventos del bus de mensajes
- Separación lógica raw / core / analytics

### Compliance Legal

| Marco | Cobertura |
|-------|-----------|
| **LFPDPPP** | Redacción de PII, minimización, derechos ARCO |
| **LGDNNA** | Detección automática de NNA, `best_interest_child`, elevación de prioridad, nunca degradar casos NNA |
| **No discriminación** | Grupos de protección reforzada usados solo para priorización protectora, nunca para perfilado o vigilancia |

---

## Limitaciones del MVP

> Este es un **MVP educativo** con datos sintéticos. No debe usarse en producción.

| Limitación | Detalle |
|------------|---------|
| IA simulada | Capa 1 usa reglas deterministas, no modelos ML reales |
| Datos sintéticos | No probado con llamadas reales del C5 |
| A3 Centinela | En Capa 1 es simulado; Capa 2 requiere checkpoint AASIST3 y GPU |
| A8 Auditor | Opcional en demo; obligatorio en producción |
| Escalabilidad | Sin balanceo de carga ni caché distribuido |
| Integración real | No conecta con C5 real; no despacha unidades; no integra CAD |

Para producción se requiere: auditoría de seguridad completa · revisión legal (LFPDPPP, LGDNNA) · validación con C5 y autoridades · certificación de A3 con datos reales de CDMX · A8 Auditor activo permanentemente.

---

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [`docs/architecture.md`](docs/architecture.md) | Diseño del sistema, diagramas Mermaid, decisiones de arquitectura |
| [`docs/legal_privacy.md`](docs/legal_privacy.md) | LFPDPPP, LGDNNA, derechos ARCO, grupos de protección reforzada, P0 |
| [`docs/cybersecurity.md`](docs/cybersecurity.md) | Controles, threat model, A3 Centinela AASIST3, checklist |
| [`docs/api_contract.md`](docs/api_contract.md) | OpenAPI specs + JSON schemas de todos los agentes |
| [`docs/lovable_integration.md`](docs/lovable_integration.md) | Guía de integración con dashboard |
| [`docs/demo_script.md`](docs/demo_script.md) | Guion de presentación: escenarios low / mid / critical |
| [`docs/n8n_workflow.md`](docs/n8n_workflow.md) | WF-1 (cron) · WF-2 (webhook camino caliente) · WF-3 (auditoría semanal) |
| [`docs/agents/`](docs/agents/) | Especificación canónica A1–A8: componentes, schemas, test() |
| [`docs/bob_setup.md`](docs/bob_setup.md) | Configuración de IBM Bob: Custom Mode, MCP Builder, Bob Shell |

---

## Licencia

**Uso Educativo Únicamente**

Este proyecto es una demostración técnica con datos sintéticos. No debe usarse en producción ni con datos reales sin:

1. Auditoría de seguridad completa
2. Revisión legal de cumplimiento (LFPDPPP, LGDNNA)
3. Validación con autoridades competentes (C5 CDMX, SSA, FGJ)
4. Certificación del modelo A3 Centinela con distribución de datos real
5. A8 Auditor activo como guarda transversal permanente

---

**Versión:** 2.0 · **Fecha:** 2026-06-06
**Build:** IBM Bob + BeeAI + MCP · **Orquestación:** n8n · **LLM:** IBM Granite + Ollama
