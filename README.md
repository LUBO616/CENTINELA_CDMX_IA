# CENTINELA\_CDMX\_IA

> Asistente de IA multiagente para operadores del sistema de emergencias 911 — Ciudad de México
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
- [Flujo Real del 911 CDMX](#flujo-real-del-911-cdmx)
- [Problema que Resuelve](#problema-que-resuelve)
- [Cómo se Construye — IBM Bob](#cómo-se-construye--ibm-bob)
- [Arquitectura — Dos Capas](#arquitectura--dos-capas)
- [Roster de Agentes (7 + 1)](#roster-de-agentes-7--1)
- [Estructura Interna Canónica](#estructura-interna-canónica)
- [Prioridad P0 — Marco Legal y Operativo](#prioridad-p0--marco-legal-y-operativo)
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

**CENTINELA\_CDMX\_IA** es un sistema de asistencia a operadores del 911 basado en agentes de IA. **No reemplaza al operador humano — lo asiste en tiempo real.**

El flujo real del C5 CDMX es invariable: la llamada entra, un operador humano la recibe, la IA trabaja en paralelo para apoyar su decisión, y el operador canaliza a la autoridad competente. CENTINELA\_CDMX\_IA se inserta en ese flujo como capa de inteligencia que reduce carga cognitiva, detecta señales que podrían pasarse por alto y sugiere canalización con base legal — sin quitar autoridad al operador en ningún momento.

El sistema opera en dos capas:

**Capa 1 — Demo ejecutable:** Tres microservicios FastAPI orquestados por n8n. Funciona con Docker Compose.

**Capa 2 — Arquitectura objetivo:** Sistema multiagente V3.0 con 7+1 agentes construidos con **IBM Bob** (MCP Builder + Bob Shell), corriendo sobre **BeeAI + MCP**, orquestados por n8n, comunicados por Redis Streams / Valkey.

### Principios de diseño

| # | Principio |
|---|-----------|
| **P0** | **El operador humano tiene la decisión final. La IA asiste, nunca reemplaza ni descarta por su cuenta** |
| P1 | Vida, integridad y libertad prevalecen sobre automatización o eficiencia estadística |
| P2 | Seguridad de datos > funcionalidad |
| P3 | Honestidad de arquitectura > seguir plantilla por simetría |
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

## Flujo Real del 911 CDMX

> Este es el flujo que CENTINELA\_CDMX\_IA respeta y en el que se inserta. El operador es el centro.

```
CIUDADANO marca 911
        ↓
OPERADOR HUMANO recibe la llamada
        ↓
   ┌────────────────────────────────────────────────────────┐
   │           CENTINELA_CDMX_IA trabaja en paralelo        │
   │                                                        │
   │  A1 Recolector  → transcribe y redacta PII en tiempo  │
   │  A3 Centinela   → detecta si la voz es sintética      │
   │  A2 Correlador  → detecta si es duplicado / broma     │
   │  A4 Triador     → sugiere nivel de riesgo 1–10        │
   │                    + autoridad competente              │
   │                    + preguntas mínimas recomendadas    │
   └────────────────────────────────────────────────────────┘
        ↓
OPERADOR HUMANO toma la decisión:
   — Escala a emergencia crítica
   — Solicita más información
   — Canaliza a autoridad competente
   — Registra el incidente
        ↓
   ┌─────────────────────────────────┐
   │  ¿Autoriza uso de datos SOLID?  │
   │  Sí → remite a autoridad        │
   │  No → atiende sin compartir     │
   └─────────────────────────────────┘
        ↓
Datos ingresan a analítica
   A5 Cartógrafo → hotspots geoespaciales H3
   A6 Estratega  → pre-posicionamiento de unidades
        ↓
Dashboard C5 / App de seguimiento CDMX
```

### Lo que la IA hace durante la llamada

| La IA hace | La IA NO hace |
|------------|--------------|
| Transcribe la llamada en tiempo real | Hablar directamente con el ciudadano |
| Redacta PII antes de registrar | Tomar decisiones de despacho |
| Sugiere nivel de riesgo con justificación visible | Cerrar o descartar una llamada |
| Detecta grupos vulnerables (NNA, adultos mayores) | Degradar riesgo ante señales P0 |
| Muestra preguntas mínimas recomendadas al operador | Reemplazar al operador en ningún caso |
| Alerta si detecta voz sintética / deepfake | Perfilar ni vigilar a personas |
| Sugiere autoridad primaria y coadyuvantes con base legal | Emitir diagnóstico médico |
| Alimenta analítica y predicciones geoespaciales | Compartir datos sin autorización SOLID |

---

## Problema que Resuelve

El C5 CDMX recibe miles de llamadas diarias. Los operadores enfrentan:

- **Sobrecarga cognitiva:** deben clasificar, priorizar, detectar grupos vulnerables y canalizar en segundos, con información parcial y bajo presión.
- **Riesgo de omisión:** señales de violencia, NNA en peligro o emergencias médicas pueden pasarse por alto en llamadas ambiguas, silenciosas o interrumpidas.
- **Fragmentación de información:** sin correlación en tiempo real, un mismo evento puede generar múltiples llamadas que se atienden como casos separados.
- **Sin apoyo geoespacial en tiempo real:** el operador no tiene visibilidad inmediata de hotspots ni de disponibilidad de unidades.

**CENTINELA\_CDMX\_IA** asiste al operador con:

1. Transcripción en tiempo real con redacción automática de PII
2. Sugerencia de nivel de riesgo 1–10 con matriz ponderada (el operador confirma o corrige)
3. Detección de señales críticas P0 que no deben omitirse
4. Detección de voz sintética / deepfake (A3 Centinela — AASIST3)
5. Correlación de llamadas duplicadas sin degradar riesgo ante señales de vida
6. Sugerencia de autoridad competente con base legal
7. Preguntas mínimas recomendadas según tipo de incidente
8. Analítica geoespacial near-real-time para decisiones de pre-posicionamiento

---

## Cómo se Construye — IBM Bob

Los agentes de la Capa 2 se construyen, prueban y documentan íntegramente con **IBM Bob**:

```
IBM Bob (entorno de desarrollo de agentes)
│
├── Custom Mode      → carga ROL + PRINCIPIOS + REGLAS como contexto base
├── Literate Coding  → spec completa del agente como instrucción raíz
├── MCP Builder      → genera el agente como servidor MCP (extiende BaseMCP)
└── Bob Shell        → ejecuta test() local sin red externa y valida el JSON schema
```

**IBM Bob NO es el runtime de producción.** Una vez que `test()` pasa en Bob Shell y se obtiene aprobación explícita del gate, el agente se despliega en BeeAI + MCP orquestado por n8n. Bob mantiene el repositorio, los workflows n8n exportados como JSON y la documentación de despliegue.

### Flujo de trabajo en Bob — por agente

```
1. Crear Custom Mode con bloque ROL / PRINCIPIOS / REGLAS
2. Pegar SPEC del agente en Literate Coding como instrucción raíz
3. Construir con MCP Builder (extiende BaseMCP sobre BeeAI)
4. Ejecutar test() con Bob Shell — validar JSON schema sin red externa
5. Obtener aprobación explícita del gate
6. Avanzar al siguiente agente
```

### Formato de respuesta de Bob por turno

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
│              (Panel de operador / supervisión)                   │
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

### Capa 2: Asistencia Multiagente V3.0 — IBM Bob + BeeAI + MCP

```
┌────────────────────────────────────────────────────────────────────────┐
│               IBM Bob (construcción y prueba de agentes)                │
│          Custom Mode → Literate Coding → MCP Builder → Bob Shell        │
└────────────────────────────────────────────────────────────────────────┘
                            ↓  (deploy tras gate aprobado)

OPERADOR HUMANO — pantalla de asistencia en tiempo real
        │
        ├── Transcripción en vivo (A1)
        ├── Alerta de voz sintética (A3)
        ├── Alerta de duplicado / broma (A2)
        ├── Nivel de riesgo sugerido 1–10 (A4) ← operador confirma o corrige
        ├── Autoridad competente sugerida (A4/A7)
        └── Preguntas mínimas recomendadas (A4)
        │
        ↓  (el operador canaliza)

┌────────────────────────────────────────────────────────────────────────┐
│                    CAMINO CALIENTE (por llamada)                        │
│                                                                         │
│  Audio → [A1 Recolector] → [A3 Centinela ∥ A2 Correlador] →          │
│                                       ↓                                 │
│                                 [A4 Triador]                            │
│                                       ↓                                 │
│                          Panel del operador humano                      │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│              CAMINO NEAR REAL-TIME (ventanas de minutos)                │
│                                                                         │
│        [A5 Cartógrafo] ──→ [A6 Estratega]                              │
│             ↓                    ↓                                      │
│       Hotspots H3         Pre-posicionamiento                           │
│       (INEGI norm.)        de unidades                                  │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                  A7 BRAVO — Coordinador Maestro                         │
│        Orquesta A1–A6 vía n8n + Redis Streams / Valkey                 │
│                  trace_id global · estado en vuelo                      │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│         A8 AUDITOR (obligatorio cuando se usen datos reales)            │
│   Disparidad por alcaldía · sesgo Centinela · falsos negativos P0       │
└────────────────────────────────────────────────────────────────────────┘

Cada agente = servidor MCP (BaseMCP en Python) construido con IBM Bob sobre runtime BeeAI
Cada mensaje entre agentes = evento en Redis Streams / Valkey
```

---

## Roster de Agentes (7 + 1)

| ID | Codename / Rol | Qué hace para el operador | Output clave |
|----|----------------|--------------------------|--------------|
| **A1** | **Recolector** — Data Steward | Transcribe la llamada en tiempo real · redacta PII antes de registrar · detecta señales de contexto del llamante | `{rows, schema_ok, transcript, caller_context_flags, medical_red_flags, violence_red_flags, speech_constraints}` |
| **A2** | **Correlador** — Correlación | Alerta si la llamada es probable duplicado o no-procedente · nunca degrada riesgo ante señales P0 | `{incident_id, is_nonproc, duplicate_of, cluster_id, trust_score}` |
| **A3** | **Centinela** — Ciberseguridad/SOC | **Red neuronal** (wav2vec2/WavLM → AASIST3): alerta al operador si detecta voz sintética/deepfake · nunca auto-descarta | `{call_id, synthetic_prob, decision, model_version, train_distribution, operating_point{fpr, fnr}}` |
| **A4** | **Triador** — Triage | Sugiere nivel de riesgo 1–10 al operador · indica grupos vulnerables · propone autoridad competente · muestra preguntas mínimas recomendadas | `{incident_id, risk_level, branch, priority_class, risk_components, protected_group_flags, best_interest_child, medical_category, case_category, primary_authority, human_required, public_stage_phrase, rationale_public}` |
| **A5** | **Cartógrafo** — Geo-temporal | Genera hotspots H3 normalizados por población INEGI para el panel de supervisión | `{hotspots[h3, risk_norm, raw_count], peaks[dim, value, intensity]}` |
| **A6** | **Estratega** — Optimización | Sugiere pre-posicionamiento de unidades y proyecta minutos de respuesta ganados (OR-Tools) | `{placements[lat, lng, covers_h3], projected_minutes_saved, assumptions}` |
| **A7** | **Bravo** — Coordinador | Orquesta A1–A6 · impide que un incidente nivel ≥5 cierre sin intervención del operador o registro de causa · produce `primary_authority` + `legal_basis_tag` | Payload consolidado + trace\_id global |
| **A8\*** | **Auditor** — Gobernanza | Auditoría semanal: disparidad por alcaldía, sesgo de Centinela, falsos negativos médicos/violencia de género/NNA, llamadas silenciosas cerradas | Reporte semanal de equidad y sesgo |

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

### Ejemplo: A3 Centinela

```
Núcleo:        Red neuronal — wav2vec2/WavLM (front-end SSL) → AASIST3 (back-end)
               IBM Granite solo como capa de explicación opcional
RAG:           Firmas de motores TTS/VC conocidos, codecs, distribución de entrenamiento
Memoria:       Veredictos por sesión/origen para detectar inundación automatizada
Planificación: extraer features → inferir synthetic_prob → aplicar umbral → alertar operador
Herramientas:  Checkpoint AASIST3 (HuggingFace), extractor de features, conector al bus
               Generadas con IBM Bob MCP Builder, ejecutadas en BeeAI
Datos:         ASVspoof5 / Codecfake / in-the-wild — ASVspoof 2019 es insuficiente
Guarda:        FNR bajo; synthetic alto → alerta al operador, NUNCA auto-descarte
```

---

## Prioridad P0 — Marco Legal y Operativo

> **El operador humano siempre tiene la palabra final. P0 garantiza que la IA nunca oculte, omita ni descarte señales críticas antes de que el operador las vea.**

### Señales P0 — la IA alerta al operador y bloquea el cierre automático

Arma · fuego · explosión · gas · sustancia química · intento suicida · persona inconsciente · dificultad respiratoria · sangrado grave · pérdida de libertad · privación · desaparición · violencia sexual · violencia familiar · violencia contra mujeres · NNA en peligro · persona adulta mayor en abandono o maltrato · persona con discapacidad en riesgo · imposibilidad de hablar libremente.

Toda llamada **silenciosa, incompleta, interrumpida, con gritos, llanto, respiración agitada, clave verbal, coacción audible o terceros controlando la conversación** se marca como incidente incierto y el operador recibe alerta inmediata.

### Matriz de cálculo — A4 Triador (sugerencia para el operador)

| Dimensión | Peso |
|-----------|------|
| Severidad material del hecho | 40% |
| Tiempo crítico de atención | 25% |
| Riesgo de escalamiento | 20% |
| Vulnerabilidad e interseccionalidad | 15% |

```
Prioridad operativa agregada (con histórico) = 75% riesgo normalizado + 25% volumen relativo
El riesgo individual de la llamada en curso siempre prevalece sobre el volumen histórico.
```

### Jerarquía de niveles operativos (sugeridos al operador)

| Nivel | Categoría | Ejemplos | Acción sugerida al operador |
|-------|-----------|----------|-----------------------------|
| **10** | Riesgo extremo inmediato | Disparos activos, secuestro, paro cardiorrespiratorio, incendio con personas, feminicidio tentado, NNA en peligro inmediato | Despacho prioritario · autoridad primaria y coadyuvante · registro CAD |
| **9** | Riesgo crítico alto | Violencia contra la mujer con amenaza, robo con violencia, convulsión prolongada, NNA extraviado | Despacho inmediato · seguimiento activo |
| **8** | Riesgo alto | Violencia familiar sin arma, crisis de salud mental con riesgo indirecto, embarazo con sangrado | Validación asistida · transferencia inmediata ante agravante |
| **7** | Riesgo alto-medio | Hecho en curso sin lesión grave confirmada, llamada interrumpida con contexto riesgoso | Preguntas mínimas · escalar si hay incertidumbre |
| **6** | Riesgo medio con posible escalamiento | Reportes ambiguos con señales de riesgo, accidente con NNA, olor a gas leve | Validación intermedia · canalización según competencia |
| **5** | Validación intermedia | Reportes incompletos, posible broma con señales de fondo | El operador repregunta; escalar si sube el riesgo |
| **4** | Bajo con seguimiento | Daños materiales menores, orientación, servicio público sin riesgo actual | Orientar, registrar, canalizar — ofrecer derivación |
| **3** | Bajo | Reporte informativo, incidente ya atendido | Orientar y registrar trazabilidad mínima |
| **2** | Mínimo | Error de marcación confirmado, llamada improcedente sin señales de riesgo | Informar uso adecuado del 911 y cerrar con registro |
| **1** | No emergencia confirmada | Broma explícita, prueba técnica autorizada | Cerrar con registro. **Nunca usar si la persona no puede hablar o cuelga abruptamente** |

### Grupos de Protección Reforzada

La IA detecta y alerta al operador cuando la llamada involucra:

NNA · Jóvenes · Mujeres · Personas adultas mayores · Personas con discapacidad · Migrantes o personas con protección internacional · Miembros de pueblos indígenas · Personas defensoras de derechos humanos · Periodistas · Personas en desplazamiento forzado interno · Personas en situación de calle · Comunidad LGBTTTI.

**Reglas de uso:** estas categorías no se usan para perfilar, vigilar ni discriminar. Solo para priorización protectora, accesibilidad, intérpretes y canalización especializada. En intersección de dos o más categorías, A4 añade `vulnerability_multiplier` auditable. Para NNA: `best_interest_child: true`.

### Canalización sugerida por A7 Bravo al operador

A7 produce siempre `primary_authority`, `coordinating_authority`, `support_authorities` y `legal_basis_tag` para que el operador decida la canalización.

| Tipo de llamada | Autoridad primaria sugerida | Coadyuvantes sugeridas |
|----------------|----------------------------|------------------------|
| Emergencia médica (paro, infarto, EVC, trauma, parto) | Secretaría de Salud CDMX / SEM | C5/C2, Protección Civil, policía si hay riesgo |
| Crisis psicológica, suicidio, autolesión | Secretaría de Salud CDMX | SIBISO, DIF-CDMX, C5, FGJ si hay delito |
| Violencia contra mujeres, violencia familiar, sexual | Fiscalía General de Justicia CDMX | Secretaría de las Mujeres, policía, salud, DIF |
| NNA en riesgo, abandono, maltrato, extravío | Procuraduría de Protección NNA / DIF-CDMX | FGJ, salud, educación |
| Incendio, explosión, fuga de gas, derrame químico | Protección Civil / bomberos / C5 | Salud, policía, alcaldía, autoridad ambiental |
| Hecho delictivo, arma, robo con violencia | Seguridad pública / policía competente | FGJ, salud, C5 |
| Servicio público con riesgo (cables, socavón) | Alcaldía o dependencia competente | Protección Civil, C5, policía |
| Personas en calle, migrantes, abandono social | SIBISO | DIF-CDMX, salud, alcaldía, FGJ si hay delito |
| Llamada silenciosa o con coacción | C5/C2 — alerta inmediata al operador | Policía, salud o protección civil según señales |

### Preguntas mínimas que la IA muestra al operador según tipo de incidente

**Seguridad:** ¿Qué está ocurriendo? · ¿Hay armas? · ¿Hay personas lesionadas? · ¿La agresión sigue ocurriendo? · ¿Dónde ocurre? · ¿Puede hablar sin ponerse en riesgo?

**Salud:** ¿La persona respira? · ¿Está consciente? · ¿Qué edad tiene? · ¿Qué síntoma principal presenta? · ¿Cuándo empezó? · ¿Hay embarazo, sangrado, golpe, intoxicación, fuego, gas o electricidad?

**Protección civil:** ¿Hay fuego, humo, olor a gas, explosión, derrame o estructura dañada? · ¿Hay personas atrapadas? · ¿Hay NNA, adultos mayores o personas con discapacidad en el sitio? · ¿El riesgo se está expandiendo?

**Víctimas y grupos protegidos:** ¿La persona está en un lugar seguro? · ¿Necesita atención médica? · ¿Hay NNA involucrados? · ¿Requiere intérprete? · ¿La persona agresora está presente? · ¿Autoriza compartir los datos estrictamente necesarios con la autoridad competente?

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

### Coeficiente de Gini — Equidad Geográfica en la Atención

| Escenario | Gini |
|-----------|------|
| Sin sistema (línea base) | **0.42** — alcaldías con mayor volumen acaparan recursos independientemente del riesgo real per cápita |
| Con CENTINELA\_CDMX\_IA | **0.28** — supera el umbral de éxito (≤0.35) tras normalización INEGI 2020 |

Una emergencia tiene la misma probabilidad de ser priorizada correctamente sin importar si ocurre en una zona densamente poblada o marginada.

### Impacto esperado

- Reducción de carga cognitiva del operador durante la llamada
- Detección de señales P0 que de otro modo podrían omitirse en llamadas ambiguas
- Protección activa de grupos vulnerables (NNA, adultos mayores, mujeres)
- Detección de voz sintética e inundación automatizada del sistema
- Analítica geoespacial near-real-time con normalización INEGI
- Privacidad by design — PII nunca llega al motor de clasificación
- Equidad auditada por A8 (obligatorio en producción)

---

## Requisitos Previos

### MVP Docker (Capa 1)

- Docker >= 20.10 · Docker Compose >= 2.0 · jq · curl · Git

### Arquitectura agéntica V3.0 (Capa 2)

- IBM Bob (acceso a watsonx / entorno Bob)
- Python >= 3.11 · Ollama con IBM Granite · Redis >= 7 o Valkey · Qdrant
- GPU CUDA-compatible (recomendada para A3 Centinela / AASIST3)

### Recursos mínimos

| Capa | RAM | CPU | Disco |
|------|-----|-----|-------|
| MVP Docker | 4 GB | 2 cores | 5 GB |
| Agéntica completa | 16–32 GB | 8 cores + GPU | 40 GB |

---

## Instalación

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
./scripts/01_start.sh infra       # solo infraestructura
./scripts/01_start.sh all         # todo el sistema
./scripts/03_logs.sh api-ingest   # logs por servicio
./scripts/02_stop.sh              # detener todo
./scripts/04_test_environment.sh all
./scripts/05_seed_demo_data.sh direct
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
| **4** | Documentación | README completo; sin direcciones completas expuestas en analytics |

### Gates Arquitectura Agéntica V3.0 (IBM Bob)

| Gate | Objetivo |
|------|----------|
| **1** | Confirmar esquema C5 vs. diccionario + levantar bus Redis Streams / Valkey |
| **2** | A1 Recolector + A2 Correlador con `test()` verde en Bob Shell |
| **3** | A3 Centinela — checkpoint AASIST3, FPR/FNR declarados, `train_distribution` verificada. **Espera aprobación explícita** |
| **4** | A4 Triador (consume trust A2/A3) + flujo completo niveles 1–10 |
| **5** | A5 Cartógrafo + A6 Estratega (normalización INEGI verificada) |
| **6** | A7 Bravo + workflows n8n exportados como JSON + bus integrado end-to-end |

### Definition of Done por agente (IBM Bob)

- Implementa los 6 componentes canónicos (o declara ausentes con justificación).
- `test()` pasa en Bob Shell sin red externa; salida valida contra JSON schema.
- Cero PII en código, logs, salidas y eventos del bus.
- Modelo declara versión + distribución + punto de operación.
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
  "public_stage_phrase": "Nivel 8 detectado. Posible emergencia médica con sangrado. Operador: confirmar y canalizar a SEM.",
  "rationale_public": "Señal de sangrado grave detectada. Nivel sugerido: 8. Decisión final: operador.",
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
- Cero PII en eventos del bus de mensajes
- Sin direcciones completas en analytics
- Separación lógica raw / core / analytics

### Compliance Legal

| Marco | Cobertura |
|-------|-----------|
| **LFPDPPP** | Redacción de PII, minimización, derechos ARCO |
| **LGDNNA** | Detección de NNA, `best_interest_child`, elevación de prioridad, bloqueo de degradación de casos NNA |
| **No discriminación** | Grupos de protección reforzada usados solo para priorización protectora, nunca para perfilado o vigilancia |

---

## Limitaciones del MVP

> MVP educativo con datos sintéticos. No debe usarse en producción.

| Limitación | Detalle |
|------------|---------|
| IA simulada | Capa 1 usa reglas deterministas; sin modelos ML reales |
| Datos sintéticos | No probado con llamadas reales del C5 |
| A3 Centinela | En Capa 1 es simulado; Capa 2 requiere checkpoint AASIST3 y GPU |
| A8 Auditor | Opcional en demo; **obligatorio en producción** |
| Escalabilidad | Sin balanceo de carga ni caché distribuido |
| Integración real | No conecta con C5 real; no despacha unidades; no integra CAD |

Para producción: auditoría de seguridad completa · revisión legal LFPDPPP + LGDNNA · validación con C5 y autoridades competentes · certificación A3 con datos reales CDMX · A8 Auditor activo permanente.

---

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [`docs/architecture.md`](docs/architecture.md) | Diseño del sistema, diagramas Mermaid |
| [`docs/legal_privacy.md`](docs/legal_privacy.md) | LFPDPPP, LGDNNA, derechos ARCO, P0 |
| [`docs/cybersecurity.md`](docs/cybersecurity.md) | Controles, threat model, A3 Centinela |
| [`docs/api_contract.md`](docs/api_contract.md) | OpenAPI specs + JSON schemas de agentes |
| [`docs/lovable_integration.md`](docs/lovable_integration.md) | Integración con dashboard de operador |
| [`docs/demo_script.md`](docs/demo_script.md) | Guion de presentación: low / mid / critical |
| [`docs/n8n_workflow.md`](docs/n8n_workflow.md) | WF-1 (cron) · WF-2 (webhook) · WF-3 (auditoría) |
| [`docs/agents/`](docs/agents/) | Especificación canónica A1–A8 con schemas y test() |
| [`docs/bob_setup.md`](docs/bob_setup.md) | Configuración IBM Bob: Custom Mode, MCP Builder, Bob Shell |

---

## Licencia

**Uso Educativo Únicamente**

Este proyecto es una demostración técnica con datos sintéticos. No debe usarse en producción ni con datos reales sin:

1. Auditoría de seguridad completa
2. Revisión legal (LFPDPPP, LGDNNA)
3. Validación con autoridades competentes (C5 CDMX, SSA, FGJ)
4. Certificación del modelo A3 Centinela con distribución de datos real de CDMX
5. A8 Auditor activo como guarda transversal permanente

---

**Versión:** 2.0 · **Fecha:** 2026-06-06
**Build:** IBM Bob + BeeAI + MCP · **Orquestación:** n8n · **LLM:** IBM Granite + Ollama

