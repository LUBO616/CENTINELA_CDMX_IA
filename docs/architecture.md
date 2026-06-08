# Arquitectura del Sistema — CENTINELA_CDMX_IA

> Documento técnico · Versión 4.0 · Junio 2026

---

## Principios de diseño

El sistema fue diseñado desde cero con estas restricciones no negociables:

| # | Principio | Implementación técnica |
|---|---|---|
| **P0** | Vida, integridad y libertad prevalecen sobre automatización o eficiencia estadística | Restricción en cada agente: ninguno puede cerrar, degradar o canalizar autónomamente |
| **P1** | El operador humano tiene la decisión final | Nivel ≥5 requiere intervención humana o registro explícito de causa para cerrarse |
| **P2** | Seguridad de datos > funcionalidad | PII se redacta en A1 antes de que cualquier otro componente acceda al contenido |
| **P3** | Honestidad de arquitectura | Si un componente canónico no aporta valor a un agente, se declara `none` con justificación — nunca se añade por simetría |
| **P4** | Solo herramientas abiertas, enlazables en tiempo real | Stack 100% open source, sin dependencias de APIs externas en runtime |
| **P5** | Equidad geográfica medible | Riesgo normalizado por población INEGI 2020 · Gini 0.28 verificable |
| **P6** | Incremental y verificable | Cada agente define `test()` sin red externa antes de integrarse al sistema |

---

## Visión general del sistema

CENTINELA se inserta en el flujo operativo del 911 como capa de inteligencia de asistencia. El flujo del operador es invariable — la IA trabaja en paralelo y enriquece las decisiones sin alterar la cadena de mando.

```
Llamada 911
    │
    ▼
┌──────────────────────────────────────────────────────────────────────┐
│  CAPA 0 — Redacción automática de PII (primera operación del sistema)│
│  A1 Recolector — Nombre · teléfono · dirección · datos de salud      │
│  → [REDACTADO] antes de cualquier procesamiento posterior            │
│  LFPDPPP Art. 11 · minimización de datos                            │
└──────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────────────┐
│  CAPA 1 — Coordinación maestra · A7 Bravo · n8n · Redis Streams      │
│  Orquesta A1–A6 · fallo de agente → escala a humano                 │
│  Sin agencia autónoma · trace_id global                              │
└──────────────────────────────────────────────────────────────────────┘
    │
    ├─────────────────────────────────────────────────────────────────┐
    │  CAPA 2 — Camino caliente (tiempo real, por llamada)            │
    │                                                                  │
    │  [A1 Recolector]                                                 │
    │  Ingesta · STT en vivo · valida schema canónico                 │
    │  Out: rows · schema_ok · transcript · caller_context_flags       │
    │                                                                  │
    │  [A3 Centinela]          [A2 Correlador]                        │
    │  wav2vec2 + AASIST3      Caza duplicados · geo-temporal         │
    │  Deepfake · voz sintética Detecta inundación coordinada         │
    │  Out: synthetic_prob      Out: trust_score · is_nonproc          │
    │  ⚠ HiL si synthetic alto                                        │
    │                  └──────────────┘                               │
    │                         │                                        │
    │                         ▼                                        │
    │  [A4 Triador] — Triage 1–10                                     │
    │  Consume trust_score A2 + synthetic_prob A3                     │
    │  NNA → best_interest_child · nivel ≥9 → HiL obligatorio         │
    │                                                                  │
    │  ┌─────────────────────────────────────────────────────────┐    │
    │  │  Restricción técnica invariable:                         │    │
    │  │  Ningún agente puede cerrar, degradar o derivar          │    │
    │  │  una llamada de forma autónoma.                          │    │
    │  │  Nivel ≥5 → Human-in-the-Loop obligatorio               │    │
    │  └─────────────────────────────────────────────────────────┘    │
    └─────────────────────────────────────────────────────────────────┘
    │
    │  Gate SOLID — Consentimiento LFPDPPP Art. 8
    │  ¿Ciudadano autoriza PII?
    │  Sí → remite a autoridad con base legal documentada
    │  No → atiende sin compartir datos
    │
    ├─────────────────────────────────────────────────────────────────┐
    │  CAPA 3 — Analítica near-real-time (ventanas de minutos)        │
    │                                                                  │
    │  [A5 Cartógrafo]              [A6 Estratega]                    │
    │  Hotspots H3 + PostGIS        OR-Tools — cobertura              │
    │  Normalizado INEGI 2020       Pre-posiciona unidades            │
    │  LLM: none (determinista)     LLM: mínimo (explica)             │
    │  Gini 0.28 · equidad geo.     Out: placements · minutos         │
    └─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────────────┐
│  CAPA 4 — Gobernanza activa · A8 Auditor (obligatorio en producción) │
│  Equidad por alcaldía · sesgo A3 · FNR · falsos negativos P0         │
│  Disparidad NNA · violencia de género · llamadas silenciosas         │
│  Job semanal n8n · NIST AI RMF MEASURE                              │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Estructura interna canónica

Cada agente del sistema implementa seis componentes. Si un componente no aporta valor en un agente específico, se declara `mínimo` (presente pero trivial) o `none (justificación)` — nunca se añade por simetría formal.

| Componente | Descripción | Implementación de referencia |
|---|---|---|
| **Núcleo** | Motor de razonamiento del agente | LLM local (Ollama + cualquier modelo) por defecto; red neuronal o solver donde el LLM no aporta |
| **RAG** | Recuperación de documentos relevantes | Qdrant + embeddings abiertos (nomic-embed / bge) |
| **Memoria** | Estado entre llamadas y sesiones | BeeAI nativa (summarized / token-controlled) |
| **Planificación** | Descomposición de la tarea en subtareas | Expuesto en la traza de cada llamada |
| **Herramientas** | Programas que el agente acciona | Tools MCP en Python (BaseMCP sobre BeeAI) |
| **Interfaz** | Entrada y salida del agente | Bus de eventos Redis Streams / agente upstream — nunca el usuario final directamente |

---

## Especificación por agente

### A1 — Recolector · Data Steward

**Responsabilidad:** Primera operación del sistema. Transcribe el audio, redacta PII, valida el schema canónico y detecta señales de contexto del llamante.

| Componente | Implementación |
|---|---|
| Núcleo | LLM mínimo (solo desambigua mapeo de campo) · validación determinista |
| RAG | Diccionario de datos C5 + esquema canónico · catálogo de señales de contexto |
| Memoria | Cursores/offsets · hashes de lotes · desfases creación-cierre |
| Planificación | Recibir stream → transcribir → redactar PII → validar vs. esquema → emitir |
| Herramientas | faster-whisper / Vosk (STT) · conector CSV/PostGIS · validador de esquema |
| Interfaz | Bus Redis Streams → A2, A3 en paralelo |

**Output:**
```json
{
  "rows": "int",
  "schema_ok": "bool",
  "warnings": ["str"],
  "table_ref": "str",
  "transcript": "str",
  "caller_context_flags": {
    "child_or_adolescent": "bool|null",
    "woman": "bool|null",
    "older_adult": "bool|null",
    "disability": "bool|null",
    "migrant_or_international_protection": "bool|null",
    "indigenous_person": "bool|null"
  },
  "medical_red_flags": ["str"],
  "violence_red_flags": ["str"],
  "environmental_red_flags": ["str"],
  "speech_constraints": ["silent|whisper|third_party_control|hangup|panic|language_barrier"]
}
```

---

### A2 — Correlador · Correlación

**Responsabilidad:** Detectar si la llamada es duplicado del mismo evento o probable no-procedente. No puede reducir el nivel de riesgo cuando A1 o A4 detecten señales P0.

| Componente | Implementación |
|---|---|
| Núcleo | LLM para similitud semántica del motivo de llamada |
| RAG | Catálogo de motivos/sinónimos + patrones de no-procedente |
| Memoria | Ventana deslizante de incidentes recientes (vectores en Qdrant) |
| Planificación | Clasificar no-proc → buscar vecinos geo-temporales → asignar cluster |
| Herramientas | Qdrant · índice geoespacial · reloj de ventana temporal |
| Interfaz | Bus Redis Streams → A4 |

**Output:**
```json
{
  "incident_id": "str",
  "is_nonproc": "bool",
  "duplicate_of": "str|null",
  "cluster_id": "str",
  "trust_score": "float"
}
```

**Restricción crítica:** A2 detecta duplicidad o posible improcedencia, pero **no puede disminuir riesgo** cuando A1 o A4 detecten señales P0. Toda llamada posiblemente falsa con señales de vida, salud, violencia o grupo protegido pasa a revisión humana.

---

### A3 — Centinela · Detección de Deepfake

**Responsabilidad:** Detectar voz sintética o deepfake de audio. Es el único agente del sistema que usa una red neuronal de audio en lugar de un LLM.

| Componente | Implementación |
|---|---|
| Núcleo | **Red neuronal de audio** — NO LLM · wav2vec2/WavLM (front-end SSL) → AASIST3 (back-end KAN-enhanced) · LLM solo como capa de explicación opcional |
| RAG | Firmas de motores TTS/VC conocidos · codecs · notas de distribución de entrenamiento |
| Memoria | Veredictos por sesión/origen para detectar inundación automatizada |
| Planificación | Extraer features → inferir synthetic_prob → aplicar umbral → alertar operador |
| Herramientas | Checkpoint AASIST3 (HuggingFace) · extractor de features · conector al bus |
| Interfaz | Bus Redis Streams → A4 |

**Distribución de entrenamiento requerida:** ASVspoof5 / Codecfake / in-the-wild — ASVspoof 2019 no es suficiente para voz sintética moderna.

**Output:**
```json
{
  "call_id": "str",
  "synthetic_prob": "float",
  "decision": "human|synthetic|uncertain",
  "model_version": "str",
  "train_distribution": "str",
  "operating_point": {
    "fpr": "float",
    "fnr": "float"
  }
}
```

**Restricción crítica:** La detección de voz sintética, deepfake o automatización **nunca autoriza el descarte** de una llamada. Solo produce una bandera para revisión humana, protección del sistema y correlación de patrones de inundación.

**Referencias académicas:**
- Jung et al. (2022) — AASIST: Audio Anti-Spoofing Using Integrated Spectro-Temporal Graph Attention Networks — [arXiv:2110.01200](https://arxiv.org/abs/2110.01200)
- AASIST3: KAN-Enhanced AASIST para ASVspoof 2024 — [arXiv:2408.17352](https://arxiv.org/pdf/2408.17352)

---

### A4 — Triador · Triage 1–10

**Responsabilidad:** Sugerir al operador el nivel de riesgo, la rama de atención, los grupos vulnerables involucrados y la autoridad competente. El operador confirma o corrige.

| Componente | Implementación |
|---|---|
| Núcleo | LLM razona severidad desde transcripción + clasificación + trust_score de A2 + synthetic_prob de A3 |
| RAG | Protocolos de priorización · mapa clasificación→gravedad · categorías médicas · grupos protegidos |
| Memoria | Decisiones previas similares para consistencia de criterio |
| Planificación | Reunir señales → calcular severidad → asignar rama 1–4 / 5 / 6–10 |
| Herramientas | Motor de reglas + scorer ponderado |
| Interfaz | Bus Redis Streams → A7 Bravo |

**Matriz de cálculo:**
```
Nivel de riesgo = 
  0.40 × Severidad material del hecho +
  0.25 × Tiempo crítico de atención +
  0.20 × Riesgo de escalamiento +
  0.15 × Vulnerabilidad e interseccionalidad
```

**Output:**
```json
{
  "incident_id": "str",
  "risk_level": "int 1-10",
  "branch": "low|mid|critical",
  "priority_class": "minimum|low|medium|high|critical",
  "risk_components": {
    "severity": "float",
    "time_criticality": "float",
    "escalation_probability": "float",
    "vulnerability": "float"
  },
  "protected_group_flags": ["str"],
  "best_interest_child": "bool",
  "medical_category": "cardiorespiratory|neurological|trauma|toxicological|obstetric|mental_health|environmental|general|none|unknown",
  "case_category": "security|medical|protection_civil|public_services|social_support|victim_attention|unknown",
  "primary_authority": "str",
  "support_authorities": ["str"],
  "human_required": "bool",
  "public_stage_phrase": "str",
  "rationale_public": "str",
  "trust_flags": ["str"]
}
```

---

### A5 — Cartógrafo · Geo-temporal

**Responsabilidad:** Generar mapa de hotspots geoespaciales normalizados por población INEGI 2020 para el panel de supervisión.

| Componente | Implementación |
|---|---|
| Núcleo | **Analítica determinista** (H3 + PostGIS) · LLM: `none` — no aporta a clustering geoespacial |
| RAG | Histórico agregado de incidentes + capas censales INEGI 2020 |
| Memoria | Baselines por hexágono H3 · ventanas temporales previas (TimescaleDB) |
| Planificación | Indexar lat/long a H3 → descomponer temporal → normalizar por población |
| Herramientas | H3 (Uber, Apache 2.0) · PostGIS · TimescaleDB |
| Interfaz | Bus Redis Streams → A6 Estratega · Dashboard |

**Output:**
```json
{
  "hotspots": [{"h3": "str", "risk_norm": "float", "raw_count": "int"}],
  "peaks": [{"dim": "hora|dia", "value": "str", "intensity": "float"}]
}
```

**Datos de referencia:** ITER_09CSV20.csv — Censo de Población y Vivienda INEGI 2020, Ciudad de México, 9,209,944 habitantes, desagregado por entidad/municipio/localidad.

---

### A6 — Estratega · Optimización

**Responsabilidad:** Sugerir pre-posicionamiento de unidades y proyectar minutos de respuesta ganados.

| Componente | Implementación |
|---|---|
| Núcleo | **Solver de optimización** (OR-Tools, Apache 2.0) · LLM mínimo (explica la recomendación) |
| RAG | Restricciones operativas + capacidades de unidades |
| Memoria | Asignaciones previas y su resultado real (retroalimentación para mejora) |
| Planificación | Leer hotspots A5 → formular problema de cobertura → resolver → proyectar |
| Herramientas | OR-Tools · PostGIS |
| Interfaz | Bus Redis Streams → Dashboard · A7 Bravo |

**Output:**
```json
{
  "placements": [{"lat": "float", "lng": "float", "covers_h3": ["str"]}],
  "projected_minutes_saved": "float",
  "assumptions": ["str"]
}
```

---

### A7 — Bravo · Coordinador maestro

**Responsabilidad:** Orquestar A1–A6, producir el payload consolidado con `trace_id`, e impedir que una llamada de nivel ≥5 se cierre sin intervención del operador.

| Componente | Implementación |
|---|---|
| Núcleo | LLM para ruteo y manejo de excepciones del flujo |
| RAG | Definición del flujo operativo + SOPs + matriz de canalización por autoridad |
| Memoria | Estado de cada incidente en vuelo + traza global |
| Planificación | Plan maestro — descompone el flujo en llamadas a A1–A6 |
| Herramientas | n8n (webhooks) · bus Redis Streams/Valkey · clientes MCP de todos los agentes |
| Interfaz | Panel del operador · autoridades competentes (con autorización SOLID) |

**Output:** Payload consolidado + `trace_id` + `primary_authority` + `coordinating_authority` + `support_authorities` + `legal_basis_tag`

**Restricción crítica:** A7 debe impedir que una llamada de nivel 5 o superior se cierre sin intervención humana o registro de causa operativa.

---

### A8 — Auditor · Gobernanza (obligatorio en producción)

**Responsabilidad:** Auditoría semanal de equidad, sesgo y falsos negativos.

| Auditoría | Métrica |
|---|---|
| Disparidad geográfica | Distribución de riesgo por alcaldía vs. población INEGI |
| Disparidad por tipo de incidente | Variaciones en clasificación por categoría |
| Disparidad por grupo protegido | Tasas de clasificación por grupo de protección reforzada |
| Falsos negativos médicos | Casos médicos graves clasificados con nivel bajo |
| Falsos negativos violencia de género | Casos de violencia contra mujeres sub-clasificados |
| Falsos negativos NNA | Casos con NNA involucrados sin activación de `best_interest_child` |
| Llamadas silenciosas cerradas | Llamadas sin respuesta verbal que cerraron sin revisión humana |
| Casos degradados por A2 o A3 | Niveles reducidos por el Correlador o Centinela |

---

## Orquestación n8n — Workflows

| Workflow | Trigger | Descripción |
|---|---|---|
| **WF-1** | Cron (periódico) | A7 Bravo → A1 Recolector en cada recarga del histórico |
| **WF-2** | Webhook POST `/webhook/911-call` | Llamada → A3 Centinela ∥ A2 Correlador → A4 Triador → Panel |
| **WF-3** | Cron semanal | A8 Auditor — disparidad por alcaldía + sesgo de Centinela |

Cada flecha del flujo operativo es un mensaje en Redis Streams / Valkey. Los workflows se entregan exportados como JSON e importables directamente en n8n.

---

## Controles OWASP AI Top 10 (2025) — transversales

| Riesgo OWASP | Control implementado |
|---|---|
| Inyección de instrucciones | Instrucciones no expuestas al usuario final · entradas validadas estructuralmente antes de alcanzar el LLM |
| Manejo inseguro de salidas | Toda salida = JSON validado contra schema de contrato · sin texto libre hacia sistemas posteriores |
| Envenenamiento de datos | Distribución de entrenamiento declarada públicamente y versión fijada |
| Divulgación de información sensible | Cero PII en logs, prompts, salidas y bus — regla técnica absoluta |
| Diseño inseguro de componentes | Agentes solo expuestos como servidores MCP con contratos de interfaz explícitos |
| Agencia excesiva | El sistema no despacha, no contacta autoridades ni cierra casos autónomamente |
| Dependencia excesiva en IA | Interfaz muestra justificación de cada sugerencia · operador puede corregir en cualquier momento |
| Robo o inversión del modelo | Modelos locales (Granite/Ollama · AASIST3 en servidor propio) · sin dependencia de APIs externas |

---

## Infraestructura transversal

| Capa | Componente | Nota |
|---|---|---|
| Runtime de agentes | BeeAI + MCP | Alternativa: cualquier framework compatible con MCP |
| LLM | Ollama + modelo local | IBM Granite es la referencia · compatible con Llama 3, Mistral, Qwen |
| Memoria / Bus | Qdrant · nomic-embed · Redis Streams / Valkey | Kafka como alternativa a escala |
| Separación de datos | `raw` / `core` / `analytics` | Mínimo privilegio por agente · PII nunca cruza la frontera de `raw` |
| Datos censales | INEGI 2020 (ITER_09CSV20.csv) | CDMX · 9.2M habitantes · por entidad/municipio/localidad |

---

*Versión 4.0 · Junio 2026 · CENTINELA_CDMX_IA*
