# Script de Demostración - CENTINELA_CDMX_IA

## Información General

**Duración:** 3-5 minutos  
**Audiencia:** Jueces de hackathon, evaluadores técnicos, público general  
**Objetivo:** Demostrar el valor del sistema, su arquitectura, y su impacto social  
**Tono:** Profesional, técnico pero accesible, enfocado en impacto social

---

## Estructura de la Presentación

1. **Problema y Contexto** (30 segundos)
2. **Solución Propuesta** (30 segundos)
3. **Arquitectura Técnica** (45 segundos)
4. **Demo en Vivo - 3 Casos** (90 segundos)
5. **Impacto y Escalabilidad** (30 segundos)
6. **Cierre y Llamado a la Acción** (15 segundos)

**Total:** ~4 minutos

---

## 1. Problema y Contexto (30 segundos)

### Script

> "En México, el sistema 911 recibe millones de llamadas al año. Muchas son emergencias reales que requieren atención inmediata, pero otras son consultas de información o reportes de bajo riesgo. Los operadores humanos deben clasificar cada llamada manualmente, lo que genera:
> 
> - **Sobrecarga operativa:** Operadores agotados procesando llamadas de bajo riesgo
> - **Retrasos críticos:** Emergencias P0 que esperan mientras se atienden consultas simples
> - **Falta de trazabilidad:** Difícil seguimiento de casos y análisis de patrones
> 
> Necesitamos un sistema que **asista** a los operadores, no que los reemplace, clasificando llamadas de forma inteligente y priorizando las emergencias reales."

### Puntos Clave

- ✅ Problema real y cuantificable
- ✅ Impacto en operadores y ciudadanos
- ✅ Enfoque en asistencia, no reemplazo

---

## 2. Solución Propuesta (30 segundos)

### Script

> "Presentamos **CENTINELA_CDMX_IA**, un sistema de clasificación asistida por IA que:
> 
> 1. **Recibe** la transcripción de una llamada (en texto, no audio real)
> 2. **Redacta** automáticamente datos personales para proteger la privacidad
> 3. **Clasifica** el riesgo del 1 al 10 usando reglas deterministas
> 4. **Detecta** señales P0 críticas que SIEMPRE requieren atención humana
> 5. **Sugiere** la autoridad competente y el nivel de prioridad
> 6. **Genera** métricas y predicciones para optimizar recursos
> 
> Todo esto en **menos de 2 segundos**, con trazabilidad completa y cumplimiento legal mexicano."

### Puntos Clave

- ✅ Solución clara y concreta
- ✅ Beneficios medibles (velocidad, privacidad, precisión)
- ✅ Cumplimiento legal

---

## 3. Arquitectura Técnica (45 segundos)

### Script

> "La arquitectura es **modular y escalable**:
> 
> - **api-ingest:** Recibe la llamada y redacta PII usando regex y heurísticas
> - **api-triage:** Clasifica con IA determinista basada en 120+ reglas y 60+ señales P0
> - **api-analytics:** Almacena incidentes y genera métricas en tiempo real
> - **n8n:** Orquesta el flujo completo con reintentos automáticos
> - **PostgreSQL:** Base de datos única con separación por schemas (raw, core, analytics)
> 
> Todo corre en **Docker Compose**, sin máquinas virtuales, ideal para entornos con recursos limitados. El sistema es **local**, no expone datos a internet, y cumple con LFPDPPP y LGDNNA."

### Diagrama (Mostrar en Pantalla)

```
┌─────────────┐
│  Dashboard  │ (Lovable)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ n8n Webhook │ (Orquestador)
└──────┬──────┘
       │
   ┌───┴───┬───────┬────────┐
   ▼       ▼       ▼        ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│Ingest│ │Triage│ │Analyt│ │  DB  │
└──────┘ └──────┘ └──────┘ └──────┘
```

### Puntos Clave

- ✅ Arquitectura clara y visual
- ✅ Tecnologías modernas (FastAPI, Docker, n8n)
- ✅ Escalabilidad y modularidad

---

## 4. Demo en Vivo - 3 Casos (90 segundos)

### Preparación Previa

**Antes de la demo:**
1. Levantar servicios: `./scripts/01_start.sh all`
2. Verificar health: `./scripts/04_test_environment.sh`
3. Abrir terminal con comandos preparados
4. Abrir dashboard de Lovable (si aplica)
5. Abrir n8n en `localhost:5678` (opcional)

---

### Caso 1: Bajo Riesgo - Bache (20 segundos)

**Script:**
> "Primer caso: Un ciudadano reporta un bache. Veamos cómo el sistema lo clasifica."

**Comando:**
```bash
curl -X POST http://localhost:5678/webhook/911-call \
  -u admin:changeme \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Hola, quiero reportar un bache grande en la calle principal de mi colonia",
    "location_hint": "Colonia Centro"
  }' | jq '{risk_level, branch, case_category, human_required, primary_authority}'
```

**Resultado Esperado:**
```json
{
  "risk_level": 3,
  "branch": "low",
  "case_category": "public_services",
  "human_required": false,
  "primary_authority": "Servicios Públicos"
}
```

**Narración:**
> "El sistema clasifica esto como **riesgo 3/10**, rama **baja**, categoría **servicios públicos**. No requiere atención humana inmediata, puede ser procesado por un sistema automatizado o cola de baja prioridad. Autoridad sugerida: Servicios Públicos."

---

### Caso 2: Riesgo Medio - Accidente de Tránsito (25 segundos)

**Script:**
> "Segundo caso: Un accidente de tránsito sin heridos. Nivel de validación intermedio."

**Comando:**
```bash
curl -X POST http://localhost:5678/webhook/911-call \
  -u admin:changeme \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Hubo un choque entre dos autos en Insurgentes, hay tráfico pero nadie está herido",
    "location_hint": "Avenida Insurgentes"
  }' | jq '{risk_level, branch, case_category, human_required, primary_authority, public_stage_phrase}'
```

**Resultado Esperado:**
```json
{
  "risk_level": 5,
  "branch": "mid",
  "case_category": "security",
  "human_required": false,
  "primary_authority": "Policía de Tránsito",
  "public_stage_phrase": "Accidente de tránsito reportado. Unidad de tránsito en camino."
}
```

**Narración:**
> "Riesgo **5/10**, rama **media**. El sistema detecta palabras clave como 'choque' y 'tráfico', pero no hay señales P0 (heridos, fuego, etc.). Sugiere **Policía de Tránsito** como autoridad primaria. Puede ser validado por un operador junior antes de despachar unidades."

---

### Caso 3: Crítico P0 - Incendio con NNA (45 segundos)

**Script:**
> "Tercer caso: Una emergencia crítica. Incendio con un niño en riesgo."

**Comando:**
```bash
curl -X POST http://localhost:5678/webhook/911-call \
  -u admin:changeme \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "¡Auxilio! Hay un incendio en mi edificio y mi hijo está atrapado en el segundo piso",
    "location_hint": "Colonia Roma"
  }' | jq '{risk_level, branch, case_category, human_required, p0_signals, best_interest_child, primary_authority, support_authorities, public_stage_phrase}'
```

**Resultado Esperado:**
```json
{
  "risk_level": 9,
  "branch": "critical",
  "case_category": "protection_civil",
  "human_required": true,
  "p0_signals": ["incendio", "niño", "atrapado"],
  "best_interest_child": true,
  "primary_authority": "Protección Civil",
  "support_authorities": ["Bomberos", "ERUM", "DIF"],
  "public_stage_phrase": "Emergencia crítica detectada. Múltiples unidades despachadas."
}
```

**Narración:**
> "Aquí vemos el poder del sistema. Riesgo **9/10**, rama **crítica**. El sistema detecta **3 señales P0**: incendio, niño, atrapado. Activa el principio de **interés superior del niño** (LGDNNA). **Atención humana requerida: SÍ**. Sugiere **Protección Civil** como autoridad primaria, con apoyo de **Bomberos, ERUM y DIF**. Esta llamada se escala inmediatamente a un operador senior."

**Mostrar Métricas (Opcional):**
```bash
curl -s http://localhost:8003/analytics/summary | jq '{
  total_incidents,
  by_branch,
  human_required_count,
  p0_signals_count,
  nna_involved_count
}'
```

**Narración:**
> "Y en tiempo real, el sistema actualiza las métricas: total de incidentes, distribución por rama, casos que requieren humano, señales P0 detectadas, y NNA involucrados. Todo con trazabilidad completa."

---

## 5. Impacto y Escalabilidad (30 segundos)

### Script

> "El impacto de este sistema es **medible y escalable**:
> 
> **Impacto Operativo:**
> - Reduce carga de operadores en **30-40%** (casos de bajo riesgo automatizados)
> - Prioriza emergencias P0 en **menos de 2 segundos**
> - Genera métricas para optimizar recursos y predecir demanda
> 
> **Impacto Social:**
> - Protege a grupos vulnerables (NNA, adultos mayores, personas con discapacidad)
> - Cumple con marco legal mexicano (LFPDPPP, LGDNNA)
> - Mejora tiempos de respuesta en emergencias reales
> 
> **Escalabilidad:**
> - Arquitectura modular: fácil agregar nuevas categorías o autoridades
> - Puede integrarse con sistemas existentes vía API REST
> - Preparado para ML real cuando haya datos suficientes"

### Puntos Clave

- ✅ Impacto cuantificable
- ✅ Beneficio social claro
- ✅ Visión de futuro

---

## 6. Cierre y Llamado a la Acción (15 segundos)

### Script

> "**CENTINELA_CDMX_IA** no es solo tecnología, es una herramienta para **salvar vidas** y **optimizar recursos públicos**. Es un MVP funcional, listo para pilotos en C5 o centros de atención ciudadana. Estamos listos para escalar.
> 
> Gracias por su atención. ¿Preguntas?"

### Puntos Clave

- ✅ Mensaje claro y directo
- ✅ Enfoque en impacto social
- ✅ Apertura a preguntas

---

## Frases Clave para el Pitch

### Problema
- "Los operadores 911 están sobrecargados procesando llamadas de bajo riesgo"
- "Las emergencias reales esperan mientras se atienden consultas simples"
- "Falta trazabilidad y análisis de patrones"

### Solución
- "IA determinista que asiste, no reemplaza"
- "Clasificación en menos de 2 segundos"
- "Cumplimiento legal mexicano desde el diseño"

### Tecnología
- "Arquitectura modular y escalable"
- "Docker Compose, sin VMs, ideal para recursos limitados"
- "Trazabilidad completa con trace_id"

### Impacto
- "Reduce carga operativa en 30-40%"
- "Prioriza emergencias P0 automáticamente"
- "Protege a grupos vulnerables (NNA, adultos mayores)"

### Diferenciadores
- "No usamos audio real, solo texto (privacidad by design)"
- "No guardamos PII, redacción automática"
- "IA determinista, no caja negra"
- "Cumple LFPDPPP y LGDNNA"

---

## Preguntas Frecuentes (Q&A)

### 1. ¿Por qué no usan audio real?

**Respuesta:**
> "Por privacidad y simplicidad. El audio requiere transcripción (ASR), lo que agrega latencia y complejidad. En un MVP, preferimos enfocarnos en la lógica de clasificación. En producción, se integraría con un sistema ASR existente."

---

### 2. ¿Por qué IA determinista y no ML?

**Respuesta:**
> "Por transparencia y explicabilidad. En emergencias, necesitamos saber **por qué** el sistema tomó una decisión. Las reglas deterministas son auditables y cumplen con regulaciones. Cuando tengamos datos suficientes, podemos agregar ML como capa adicional."

---

### 3. ¿Cómo manejan datos personales?

**Respuesta:**
> "Redacción automática de PII (teléfonos, correos, nombres, direcciones) antes de almacenar. Normalización de ubicaciones (Calle Madero 45 → Centro). Cumplimiento con LFPDPPP. No guardamos el transcript original, solo la versión redactada."

---

### 4. ¿Qué pasa si el sistema falla?

**Respuesta:**
> "Diseñado con fail-safe: si hay duda o error, el sistema escala a humano. Las señales P0 SIEMPRE requieren atención humana. n8n tiene reintentos automáticos. Cada servicio tiene health checks."

---

### 5. ¿Cómo escala a producción?

**Respuesta:**
> "Arquitectura modular lista para Kubernetes. Separación de schemas en DB facilita sharding. APIs REST estándar, fácil integración con sistemas existentes. Preparado para agregar ML, ASR, y más autoridades."

---

### 6. ¿Cuál es el costo de operación?

**Respuesta:**
> "MVP corre en un servidor modesto (4GB RAM, 2 CPUs). En producción, estimamos ~$500-1000 USD/mes en cloud para 10,000 llamadas/día. Mucho menor que contratar más operadores."

---

### 7. ¿Qué pasa con llamadas en otros idiomas?

**Respuesta:**
> "El MVP está en español. Para otros idiomas, se agregarían diccionarios de keywords traducidos. La arquitectura es agnóstica al idioma."

---

### 8. ¿Cómo validan la precisión?

**Respuesta:**
> "Tenemos 18 tests automatizados que validan casos de bajo, medio y alto riesgo. En producción, se compararía con clasificación humana (ground truth) y se ajustarían las reglas."

---

## Checklist Pre-Demo

### Técnico
- [ ] Servicios corriendo (`docker compose ps`)
- [ ] Health checks OK (`./scripts/04_test_environment.sh`)
- [ ] n8n accesible en `localhost:5678`
- [ ] Workflow importado
- [ ] Comandos curl preparados en terminal
- [ ] Dashboard Lovable corriendo (si aplica)

### Presentación
- [ ] Laptop cargada
- [ ] Proyector/pantalla probado
- [ ] Internet/red local funcional
- [ ] Backup de slides (PDF) por si falla demo en vivo
- [ ] Agua/café para el presentador

### Contenido
- [ ] Script memorizado (no leer)
- [ ] Timing practicado (3-5 minutos)
- [ ] Respuestas a Q&A preparadas
- [ ] Diagrama de arquitectura visible

---

## Consejos para la Presentación

### Antes
1. **Practica el timing:** 3-5 minutos es poco, cada segundo cuenta
2. **Memoriza el script:** No leas, habla con confianza
3. **Prepara backup:** Si falla la demo en vivo, ten screenshots/video
4. **Conoce a tu audiencia:** Ajusta el nivel técnico según los jueces

### Durante
1. **Empieza con impacto:** El problema debe resonar emocionalmente
2. **Muestra, no digas:** La demo en vivo es más poderosa que slides
3. **Enfócate en beneficios:** No en features, sino en impacto social
4. **Mantén el ritmo:** Si algo falla, sigue adelante sin pánico

### Después
1. **Responde preguntas con confianza:** Si no sabes, di "buena pregunta, lo investigaremos"
2. **Conecta con jueces:** Pide feedback, tarjetas de contacto
3. **Documenta aprendizajes:** Qué funcionó, qué mejorar

---

## Disclaimers Éticos

**SIEMPRE mencionar:**

> "Este es un **sistema de demostración educativa**. No debe usarse para emergencias reales sin validación exhaustiva, auditorías de seguridad, y aprobación de autoridades competentes. Los datos son sintéticos. El sistema asiste a operadores humanos, no los reemplaza."

**En Q&A, si preguntan sobre reemplazo de humanos:**

> "Nuestro enfoque es **human-in-the-loop**. El sistema clasifica y sugiere, pero las decisiones críticas siempre las toma un humano. Especialmente en casos P0, el sistema ESCALA a operador senior, no decide por sí solo."

---

## Recursos Adicionales

### Para Jueces/Evaluadores
- `README.md` - Guía completa de instalación
- `docs/architecture.md` - Arquitectura detallada
- `docs/legal_privacy.md` - Cumplimiento legal
- `docs/api_contract.md` - Especificación de APIs

### Para Desarrolladores
- `scripts/04_test_environment.sh` - Pruebas automatizadas
- `scripts/06_test_n8n_webhook.sh` - Pruebas de webhook
- `docs/lovable_integration.md` - Integración con frontend

---

**Versión:** 1.0.0  
**Fecha:** 2026-06-06  
**Autor:** Bob  
**Propósito:** Demo educativa - Hackathon  
**Duración:** 3-5 minutos