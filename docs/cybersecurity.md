# Ciberseguridad — CENTINELA_CDMX_IA

> Documento técnico · Versión 1.0 · Junio 2026

---

## Contexto del threat model

CENTINELA opera en un entorno de alto riesgo: procesa información de emergencias activas en tiempo real, tiene acceso a transcripciones de llamadas del 911, y sus decisiones de clasificación tienen consecuencias directas sobre la seguridad y la vida de las personas.

Los vectores de ataque relevantes para este sistema no son los mismos que para una aplicación empresarial estándar. Los atacantes pueden tener motivaciones específicas para degradar o manipular la respuesta de emergencia de una ciudad.

---

## Modelo de amenazas

### Amenazas críticas

#### 1. Ataques deepfake de voz al canal 911

**Descripción:** Generación masiva de llamadas falsas con voz sintética para saturar el sistema, obtener respuesta de emergencia para eventos inexistentes, o probar los umbrales del sistema.

**Por qué es relevante ahora:** Los modelos de síntesis de voz han alcanzado un nivel de realismo que los hace indistinguibles para el oído humano bajo presión. El canal 911 es un objetivo de alto impacto para actores que buscan saturar recursos de seguridad pública.

**Control implementado:** A3 Centinela usa la arquitectura wav2vec2/WavLM → AASIST3, una red neuronal de audio diseñada específicamente para detectar voz sintética. La detección produce una bandera para el operador — nunca un descarte automático.

**Guarda crítica:** El umbral está calibrado con FNR bajo (baja tasa de falsos negativos) porque el costo de una llamada real clasificada como sintética es irreversible. Es preferible un falso positivo que un falso negativo.

#### 2. Inundación coordinada de llamadas duplicadas

**Descripción:** Múltiples llamadas coordinadas sobre el mismo evento inexistente, diseñadas para saturar al operador y hacer que recursos de emergencia sean enviados a una ubicación falsa.

**Control implementado:** A2 Correlador detecta patrones geo-temporales de llamadas al mismo evento, correlaciona por motivo + ubicación + ventana temporal, y detecta comportamiento de inundación coordinada.

#### 3. Manipulación del nivel de riesgo asignado

**Descripción:** Cualquier vector que intente hacer que el sistema clasifique una emergencia real con un nivel de riesgo bajo, haciendo que el operador la atienda con menor urgencia.

**Control implementado:** Las señales P0 tienen precedencia técnica absoluta sobre cualquier otro factor. Ningún agente — incluyendo A2 y A3 — puede reducir el nivel de riesgo cuando hay señales críticas activas. Esta restricción está implementada como condición de código, no como parámetro configurable.

#### 4. Exfiltración de datos personales

**Descripción:** Acceso no autorizado a transcripciones de llamadas de emergencia que contienen información médica, de ubicación, de violencia familiar, o datos de víctimas.

**Control implementado:** Redacción automática de PII en A1 como primera operación del sistema. La transcripción redactada es la única versión que persiste en la cadena de procesamiento. Cero PII en logs, bus de mensajería y salidas de agentes — regla técnica sin excepciones.

#### 5. Fallo en cascada de agentes críticos

**Descripción:** Fallo de uno o más agentes que provoque que el sistema proporcione información incorrecta al operador en un momento crítico, o que deje de proporcionar asistencia cuando más se necesita.

**Control implementado:** A7 Bravo monitorea el estado de A1–A6 y escala automáticamente al operador humano ante cualquier fallo de agente, sin degradación del servicio de emergencia. El sistema falla de forma segura: en caso de duda, el operador recibe control completo.

---

### Amenazas medias

| Amenaza | Descripción | Control |
|---|---|---|
| Uso discriminatorio de categorías protegidas | Manipulación del sistema para que categorías de protección reforzada sean usadas para perfilar o discriminar en lugar de proteger | Categorías técnicamente bloqueadas para reducir prioridad · A8 Auditor verifica semanalmente |
| Envenenamiento del modelo AASIST3 | Introducción de datos de entrenamiento contaminados para degradar la capacidad de detección | Distribución de entrenamiento declarada públicamente y versión fijada · monitoreo de tasas de error en producción |
| Inyección en el flujo de transcripción | Intentos de inyectar instrucciones o datos maliciosos a través del audio de la llamada | Instrucciones del sistema no expuestas al usuario final · entradas validadas estructuralmente antes de alcanzar el LLM |

---

## Controles de seguridad por capa

### Capa de datos

| Control | Implementación |
|---|---|
| Redacción de PII | Primera operación del sistema en A1 · antes de cualquier procesamiento posterior |
| Separación de esquemas | `raw` (transcripciones redactadas) · `core` (resultados de triage) · `analytics` (métricas) · PII nunca cruza la frontera de `raw` |
| Cero PII en bus | Regla técnica absoluta en Redis Streams / Valkey · verificable en cada mensaje |
| Sin perfilado individual | Prohibido técnicamente · A8 Auditor verifica ausencia de perfiles individuales |

### Capa de agentes

| Control | Implementación |
|---|---|
| Mínimo privilegio | Cada agente accede únicamente a su capa de datos asignada · sin acceso cruzado |
| Sin agencia autónoma | Ningún agente puede cerrar, degradar o canalizar una llamada sin intervención del operador |
| Contratos de interfaz | Toda comunicación entre agentes = JSON validado contra schema · sin texto libre |
| `test()` sin red | Cada agente define función de prueba ejecutable sin red externa |

### Capa de modelos

| Control | Implementación |
|---|---|
| Modelos locales | LLM vía Ollama + modelo local · AASIST3 en servidor propio · sin APIs externas en runtime |
| Declaración de distribución | Todo modelo declara versión + distribución de entrenamiento + punto de operación (FPR/FNR) |
| Versión fijada | Modelos con versión fijada y auditable · sin actualización automática sin validación |

### Capa de acceso (producción)

| Control | Estado en prototipo | Requisito para producción |
|---|---|---|
| Cifrado en tránsito (TLS) | Puertos restringidos a localhost | TLS obligatorio en bus y todas las interfaces |
| Autenticación mutua entre agentes | Básica en MVP | Autenticación mutua entre servidores MCP |
| Autenticación de operadores | Sin autenticación en MVP | Integración con sistema de autenticación del C5 |

---

## Controles OWASP AI Top 10 (2025)

### LLM01 — Prompt Injection

**Riesgo:** Un atacante podría inyectar instrucciones maliciosas en el texto de la llamada para manipular el comportamiento de los agentes LLM.

**Control:** Las instrucciones del sistema no son accesibles al usuario final. Las entradas de texto se validan estructuralmente antes de alcanzar el modelo. Los agentes esperan un formato JSON canónico como entrada, no texto libre arbitrario.

### LLM02 — Insecure Output Handling

**Riesgo:** Salidas del LLM que no son validadas podrían contener código, PII o datos que downstream provoquen comportamiento no esperado.

**Control:** Toda salida de cada agente es JSON validado contra su schema de contrato antes de ser enviada al bus o al siguiente agente. Sin texto libre hacia sistemas posteriores.

### LLM03 — Training Data Poisoning

**Riesgo:** Datos de entrenamiento contaminados que degraden la capacidad del modelo.

**Control:** AASIST3 usa distribución de entrenamiento declarada públicamente (ASVspoof5 / Codecfake / in-the-wild) con versión fijada. El LLM de razonamiento usa Ollama con modelo local de distribución pública conocida.

### LLM06 — Sensitive Information Disclosure

**Riesgo:** El modelo podría incluir en sus respuestas información personal del ciudadano.

**Control:** PII redactada por A1 antes de que cualquier LLM acceda al contenido. Cero PII en los inputs de los agentes de razonamiento. Verificable en los logs del bus.

### LLM08 — Excessive Agency

**Riesgo:** Un sistema de IA que puede tomar acciones de alto impacto de forma autónoma, sin supervisión humana.

**Control:** Este es el control más importante de CENTINELA. El sistema no puede despachar unidades, contactar autoridades, cerrar casos ni tomar ninguna acción operativa de forma autónoma. Solo sugiere — el operador actúa. Todo nivel ≥5 requiere intervención humana para cerrar.

### LLM09 — Overreliance

**Riesgo:** Operadores que confíen ciegamente en las sugerencias del sistema sin aplicar su juicio.

**Control:** La interfaz muestra siempre la justificación de cada sugerencia (`rationale_public`) y la etapa operativa en la que se encuentra el sistema (`public_stage_phrase`). El operador puede corregir cualquier sugerencia en cualquier momento sin restricciones.

---

## A3 Centinela — Especificación técnica de seguridad

### Arquitectura del modelo

```
Audio de llamada (WAV / stream en vivo)
           │
           ▼
   ┌───────────────────┐
   │  wav2vec2 / WavLM │  ← Front-end SSL: extracción de features espectrales
   │  (pre-entrenado)  │
   └─────────┬─────────┘
             │ Features de audio (representación latente)
             ▼
   ┌───────────────────┐
   │     AASIST3       │  ← Back-end KAN: clasificación humano/sintético
   │  (KAN-enhanced)   │
   └─────────┬─────────┘
             │
             ▼
   synthetic_prob: float
   decision: human | synthetic | uncertain
   operating_point: { fpr: float, fnr: float }
```

### Criterio de calibración del umbral

El umbral de decisión de AASIST3 se calibra para minimizar el FNR (False Negative Rate) — la probabilidad de clasificar voz sintética como humana.

**Justificación:** En el contexto del 911, el costo asimétrico de los errores es:
- Falso positivo (voz humana clasificada como sintética) → operador recibe alerta, la revisa, continúa atención → costo: fricción operativa
- Falso negativo (voz sintética clasificada como humana) → ataque de inundación no detectado → costo: saturación del sistema de emergencias

El sistema acepta más falsos positivos para reducir falsos negativos. El umbral exacto debe calibrarse con datos reales de CDMX antes del despliegue en producción.

### Distribución de entrenamiento requerida

| Dataset | Estado | Por qué |
|---|---|---|
| ASVspoof 2019 | ❌ Insuficiente | No cubre codecs de síntesis modernos (2022-2026) |
| ASVspoof 2024 / ASVspoof5 | ✅ Recomendado | Cubre distribuciones modernas de TTS y Voice Conversion |
| Codecfake | ✅ Complementario | Voz sintética generada con codecs de compresión modernos |
| In-the-wild | ✅ Recomendado para validación | Grabaciones reales de voz sintética en circulación pública |

---

## Protocolo de comunicación del operador

Durante la atención de una llamada, el sistema solo comunica al operador la etapa operativa y una justificación breve. Nunca expone la cadena interna de razonamiento.

### Formato obligatorio

```
"Estoy en la etapa de [recepción / validación / priorización / canalización / seguimiento].
Detecto [señal operativa breve].
Voy a [siguiente acción]."
```

### Frases explícitamente prohibidas

- "Mi razonamiento interno es..."
- "Estoy pensando paso por paso..."
- "La cadena de pensamiento indica..."
- "Por probabilidad estadística no vale la pena atender..."
- "Calculo internamente que..."

**Fundamento:** Estas frases podrían generar sobredependencia del operador en el razonamiento del sistema, revelar el proceso interno a actores que intenten manipularlo, y reducir la confianza institucional en la transparencia del sistema.

---

## Pendientes para producción

Antes de operar con datos reales del 911, se deben completar los siguientes controles:

| Control | Descripción | Prioridad |
|---|---|---|
| TLS en tránsito | Cifrado end-to-end en bus Redis y APIs | CRÍTICA |
| Autenticación mutua MCP | Autenticación entre servidores de agentes | CRÍTICA |
| A8 Auditor activo | Monitoreo semanal con datos reales | CRÍTICA |
| Calibración AASIST3 CDMX | Ajuste de umbrales con distribución local real | ALTA |
| Aviso de privacidad LFPDPPP | Publicación por institución operadora | ALTA |
| Prueba de penetración | Auditoría de seguridad independiente | ALTA |
| Autenticación de operadores | Integración con sistema de identidad del C5 | ALTA |

---

*CENTINELA_CDMX_IA · Ciberseguridad v1.0 · Junio 2026*
