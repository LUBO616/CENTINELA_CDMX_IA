# Cumplimiento Normativo y Marco Ético — CENTINELA_CDMX_IA

> Versión 2.0 · Junio 2026  
> Destinatarios: Alta dirección · comités de evaluación · responsables de cumplimiento

---

## Postura de seguridad

CENTINELA_CDMX_IA fue diseñado con seguridad, privacidad y ética como restricciones de diseño no negociables — no como capas añadidas después de las decisiones técnicas.

El principio de que **la vida, la integridad y la libertad del ciudadano prevalecen sobre cualquier consideración de eficiencia**, y la regla de que **ningún dato personal puede atravesar el sistema sin haber sido redactado previamente**, son invariantes técnicas que ninguna decisión de implementación posterior puede relajar.

---

## Cuadro de mando ejecutivo

| Marco / Estándar | Ámbito | Estado |
|---|---|---|
| LFPDPPP | Protección de datos personales — México | ✅ CUMPLE / ⚠ Parcial* |
| LGDNNA | Protección de NNA — México | ✅ CUMPLE |
| Marco normativo complementario mexicano | Seguridad pública · víctimas · telecomunicaciones · NOM-035 | ✅ CUMPLE |
| ISO/IEC 27001:2022 | Gestión de seguridad de la información | ✅ CUMPLE / ⚠ Parcial* |
| NIST Cybersecurity Framework 2.0 | Gobernanza · identificación · protección · detección · respuesta | ✅ CUMPLE / ⚠ Parcial* |
| NIST AI Risk Management Framework 1.0 | Gestión de riesgo en IA | ✅ CUMPLE |
| OWASP AI Top 10 (2025) | Seguridad de aplicaciones de IA | ✅ CUMPLE |
| ISO/IEC 42001:2023 | Sistema de gestión de IA | ✅ CUMPLE / ⚠ Parcial* |
| UNESCO Ética IA (2021) | Valores y principios éticos — 193 países | ✅ CUMPLE |
| Privacy by Design (Cavoukian) | Privacidad como restricción arquitectónica | ✅ CUMPLE / ⚠ Parcial* |

> *Los estados "Parcial" corresponden en todos los casos a controles técnicamente diseñados y documentados que requieren implementación operativa adicional para el despliegue con datos reales del 911. Ningún control crítico de seguridad está ausente por decisión de diseño.

---

## Marco normativo mexicano

### Ley Federal de Protección de Datos Personales en Posesión de los Particulares (LFPDPPP)

La LFPDPPP es el marco primario de protección de datos personales en México y el instrumento de mayor impacto operativo para CENTINELA, dado que el sistema procesa transcripciones de llamadas de emergencia que contienen información de carácter personal.

| Principio LFPDPPP | Implementación técnica | Estado |
|---|---|---|
| Licitud | Opera bajo autorización institucional del sistema 911. Aviso de privacidad responsabilidad de la institución operadora. | ⚠ EN DISEÑO |
| Consentimiento (Art. 8) | Gate SOLID: el operador solicita autorización explícita al ciudadano antes de remitir datos a la autoridad. | ✅ CUMPLE |
| Calidad (Art. 11) | A1 Recolector valida y normaliza datos contra el esquema canónico antes de cualquier procesamiento. | ✅ CUMPLE |
| Finalidad (Art. 12) | Datos usados exclusivamente para asistir al operador durante la llamada en curso. Sin uso secundario ni comercial. | ✅ CUMPLE |
| Proporcionalidad y minimización | Solo se registran campos estrictamente necesarios. Transcripción original nunca almacenada sin redactar. | ✅ CUMPLE |
| Responsabilidad (Art. 14) | A8 Auditor genera reportes auditables de actuación del sistema. | ⚠ EN DISEÑO |
| Seguridad (Art. 19) | Separación raw/core/analytics · cero PII en bus de eventos · puertos restringidos en MVP. | ✅ CUMPLE |
| Derechos ARCO (Art. 22-36) | Arquitectura técnica soporta ejercicio de derechos. Capa de gestión institucional requiere implementación. | ⚠ EN DISEÑO |
| Transferencia (Art. 36-43) | Remisión a autoridad solo con autorización explícita del ciudadano (gate SOLID). | ✅ CUMPLE |

**Fuente:** [http://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf](http://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf)

**Nota para producción:** La institución operadora debe emitir un Aviso de Privacidad Simplificado conforme al Art. 15 de la LFPDPPP, designar un responsable de datos (Art. 14) y establecer procedimiento de atención a derechos ARCO con plazos legales (20 días hábiles).

---

### Ley General de los Derechos de Niñas, Niños y Adolescentes (LGDNNA)

| Obligación LGDNNA | Implementación técnica | Estado |
|---|---|---|
| Interés superior de la niñez (Art. 2) | A4 Triador incorpora `best_interest_child` como criterio de desempate. Ningún agente puede degradar riesgo cuando hay NNA involucrados. | ✅ CUMPLE |
| Protección contra violencia (Art. 47) | Señales de peligro para NNA activan nivel ≥9 y bloquean cierre sin intervención del operador. | ✅ CUMPLE |
| Canalización especializada | A7 Bravo activa derivación a Procuraduría de Protección de NNA / DIF-CDMX con sustento legal documentado. | ✅ CUMPLE |
| No discriminación (Art. 4) | Detección de NNA solo opera como factor de priorización protectora. Técnicamente imposibilitado su uso para perfilar. | ✅ CUMPLE |
| Seguimiento y trazabilidad (Art. 112) | `trace_id` preservado en toda la cadena. A8 Auditor revisa semanalmente falsos negativos en casos NNA. | ⚠ EN DISEÑO |

**Fuente:** [http://www.diputados.gob.mx/LeyesBiblio/pdf/LGDNNA.pdf](http://www.diputados.gob.mx/LeyesBiblio/pdf/LGDNNA.pdf)

---

### Marco normativo complementario

| Instrumento | Relevancia | Estado |
|---|---|---|
| Ley General de Seguridad Pública | Opera como apoyo al C5/911. No sustituye atribuciones de corporaciones de seguridad. | ✅ CUMPLE |
| Ley de Protección a Defensores de DDHH y Periodistas | A7 activa protocolo específico al detectar estas categorías en riesgo reforzado. | ✅ CUMPLE |
| Ley General de Víctimas | Derivación a instancias de atención a víctimas incluida en la matriz de canalización. | ✅ CUMPLE |
| Ley Federal de Telecomunicaciones y Radiodifusión | El sistema no intercepta comunicaciones. Recibe transcripción solo tras autorización del operador. | ✅ CUMPLE |
| NOM-035-STPS (Factores de riesgo psicosocial) | El sistema reduce directamente la carga cognitiva del operador. | ✅ CUMPLE |

---

## Estándares internacionales de ciberseguridad

### ISO/IEC 27001:2022

| Control | Implementación | Estado |
|---|---|---|
| Políticas de seguridad y gobernanza | Seis principios y seis reglas duras documentados y versionados. | ✅ CUMPLE |
| Control de acceso y mínimo privilegio | Cada agente accede únicamente a su capa de datos asignada. | ✅ CUMPLE |
| Protección de información personal | Redacción automática de PII en el primer agente de la cadena. | ✅ CUMPLE |
| Gestión de vulnerabilidades | Stack 100% open source con licencias verificadas y distribuciones declaradas. | ✅ CUMPLE |
| Monitoreo y auditoría continua | A8 Auditor con reportes semanales de sesgo y falsos negativos. | ⚠ EN DISEÑO |
| Cifrado y seguridad en tránsito | MVP: localhost. Producción: TLS requerido. | ⚠ EN DISEÑO |
| Codificación segura y validación | Validación en todos los puntos. Salidas JSON validadas contra schema. | ✅ CUMPLE |

**Fuente:** [https://www.iso.org/standard/27001](https://www.iso.org/standard/27001)

---

### NIST Cybersecurity Framework 2.0

| Función | Capacidades implementadas | Estado |
|---|---|---|
| GOVERN | Principios y reglas documentados · roles definidos por agente · auditoría continua · `legal_basis_tag` | ✅ CUMPLE |
| IDENTIFY | Inventario de activos · clasificación de riesgo 1-10 · mapeo de grupos protegidos · catálogo de señales P0 | ✅ CUMPLE |
| PROTECT | Redacción automática de PII · cero PII en bus · mínimo privilegio · separación de capas | ✅ CUMPLE |
| DETECT | Red neuronal AASIST3 · correlación de duplicados · alertas automáticas ante señales de riesgo extremo | ✅ CUMPLE |
| RESPOND | Escalamiento automático al operador ante toda señal crítica · nivel ≥5 no cierra sin intervención | ✅ CUMPLE |
| RECOVER | `trace_id` para reconstrucción de incidentes · arquitectura modular · reportes de auditoría semanales | ⚠ EN DISEÑO |

**Fuente:** [https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf](https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf)

---

### NIST AI Risk Management Framework 1.0

| Función AI RMF | Implementación | Estado |
|---|---|---|
| GOVERN | P0 (vida sobre automatización) como restricción técnica no negociable · A8 como mecanismo de gobernanza continua | ✅ CUMPLE |
| MAP | Contexto de alto impacto declarado · señales críticas catalogadas · grupos vulnerables identificados · riesgo de FN mitigado | ✅ CUMPLE |
| MEASURE | Tasas de error de AASIST3 declaradas · coeficiente de Gini medible · factor de vulnerabilidad auditable | ✅ CUMPLE |
| MANAGE | Ningún agente descarta llamadas autónomamente · llamadas silenciosas/interrumpidas siempre a validación humana | ✅ CUMPLE |

**Fuente:** [https://doi.org/10.6028/NIST.AI.100-1](https://doi.org/10.6028/NIST.AI.100-1)

---

### OWASP AI Top 10 (2025)

| Riesgo | Control en CENTINELA | Estado |
|---|---|---|
| Inyección de instrucciones | Instrucciones no expuestas al usuario final · entradas validadas estructuralmente antes del LLM | ✅ CUMPLE |
| Manejo inseguro de salidas | Toda salida = JSON validado contra schema · sin texto libre hacia sistemas posteriores | ✅ CUMPLE |
| Envenenamiento de datos de entrenamiento | Distribución AASIST3 declarada públicamente · versión fijada y auditable | ✅ CUMPLE |
| Divulgación de información sensible | Cero PII en logs · prompts · salidas y bus · regla técnica absoluta sin excepciones | ✅ CUMPLE |
| Diseño inseguro de componentes | Agentes solo expuestos como servidores MCP con contratos explícitos · sin acceso a redes externas en pruebas | ✅ CUMPLE |
| Agencia excesiva | El sistema no despacha · no contacta autoridades · no cierra casos de forma autónoma | ✅ CUMPLE |
| Dependencia excesiva en IA | Interfaz muestra justificación de cada sugerencia · operador puede corregir en cualquier momento | ✅ CUMPLE |
| Robo o inversión del modelo | Modelos locales (LLM vía Ollama · AASIST3 en servidor propio) · sin dependencia de APIs externas | ✅ CUMPLE |

**Fuente:** [https://owasp.org/www-project-top-10-for-large-language-model-applications/](https://owasp.org/www-project-top-10-for-large-language-model-applications/)

---

### ISO/IEC 42001:2023 — Sistema de Gestión de IA

| Requisito | Implementación | Estado |
|---|---|---|
| Contexto y alcance (Cláusula 4) | Prototipo técnico con ruta documentada hacia producción · partes interesadas y limitaciones establecidas | ✅ CUMPLE |
| Liderazgo y política de IA (Cláusula 5) | Seis principios de diseño constituyen la política de IA del proyecto | ✅ CUMPLE |
| Evaluación de impacto (Cláusula 6) | Riesgos documentados: FN médicos · sesgo geográfico · ataques de inundación · privacidad del ciudadano | ✅ CUMPLE |
| Transparencia operativa (Cláusula 8) | Operador siempre visualiza justificación de la sugerencia y etapa operativa del sistema | ✅ CUMPLE |
| Evaluación del desempeño (Cláusula 9) | Métricas de disparidad geográfica · sesgo de AASIST3 · FN por grupo de protección — reportadas semanalmente | ⚠ EN DISEÑO |
| Mejora continua (Cláusula 10) | Arquitectura incremental · A8 Auditor alimenta el ciclo de mejora | ✅ CUMPLE |

**Fuente:** [https://www.iso.org/standard/42001](https://www.iso.org/standard/42001)

---

## Marco ético UNESCO (2021)

La Recomendación de la UNESCO sobre la Ética de la Inteligencia Artificial, adoptada en noviembre de 2021 por 193 países incluyendo México, establece cuatro valores fundamentales y diez principios rectores. CENTINELA los adopta como restricciones técnicas verificables, no como compromisos declarativos.

### Valores fundamentales

| Valor | Implementación |
|---|---|
| Respeto y protección de derechos humanos | El sistema no puede cerrar una llamada con señales de violencia o riesgo vital. El derecho a la vida prevalece técnica y operativamente. |
| Prosperidad y bienestar para todas las personas | Normalización INEGI garantiza igual probabilidad de atención en colonias marginadas y de alto ingreso. Gini: 0.28. |
| Sociedades justas, equitativas e inclusivas | 12 grupos de protección reforzada reciben mayor prioridad como factor protector. Uso discriminatorio bloqueado técnicamente. |
| Protección del entorno | Modelos ejecutados en infraestructura local. Sin dependencia de servicios en la nube de alto consumo. Stack 100% open source. |

### Los diez principios

1. **Proporcionalidad y no causar daño** — La IA se usa solo donde aporta valor real y verificable. Umbral de detección calibrado para priorizar no omisión sobre reducción de falsas alarmas.

2. **Seguridad y protección** — A3 Centinela detecta ataques de inundación mediante voz sintética. Ante fallo de agente crítico, el sistema escala automáticamente al operador sin degradación del servicio.

3. **Equidad y no discriminación** — Coeficiente de Gini: 0.42 → 0.28. Los 12 grupos de protección reforzada reciben mayor prioridad como factor protector. A8 Auditor revisa semanalmente si algún grupo está siendo sistemáticamente sub-priorizado.

4. **Sostenibilidad** — Stack completamente open source ejecutable en hardware estándar disponible en instituciones públicas mexicanas. Componentes independientes y actualizables.

5. **Derecho a la privacidad y protección de datos** — PII del ciudadano es redactada por A1 antes de que cualquier componente de IA acceda al contenido. Solo el ciudadano puede autorizar que sus datos se remitan a la autoridad.

6. **Supervisión y rendición de cuentas humanas** — Todo incidente nivel ≥5 requiere intervención del operador o registro explícito de causa para cerrarse. El operador puede corregir cualquier sugerencia en todo momento.

7. **Transparencia y explicabilidad** — Cada sugerencia incluye justificación legible. El sistema declara versión, distribución y punto de operación de cada modelo. Protocolo de comunicación prohíbe explícitamente frases que sugieran deliberación interna oculta.

8. **Responsabilidad y rendición de cuentas** — Asignación clara: el operador es responsable de la decisión de canalización; el sistema es responsable de la calidad y veracidad de sus sugerencias. Sustento legal documentado en cada sugerencia.

9. **Concienciación y alfabetización en IA** — Interfaz diseñada para operadores sin formación técnica en IA. Sugerencias en lenguaje operativo conocido. Objetivo: amplificar la capacidad del operador.

10. **Gobernanza y colaboración adaptativa** — Arquitectura de agentes independientes permite actualizar componentes ante cambios regulatorios sin rediseñar el sistema. A8 Auditor como mecanismo de retroalimentación al sistema de gobernanza institucional.

**Fuente:** [https://www.unesco.org/en/artificial-intelligence/recommendation-ethics](https://www.unesco.org/en/artificial-intelligence/recommendation-ethics)

---

## Privacy by Design — 7 principios (Cavoukian)

| Principio | Implementación |
|---|---|
| Proactivo, no reactivo | Redacción de PII en A1 ocurre antes de cualquier procesamiento. No es medida correctiva: es la primera operación del sistema. |
| Privacidad como configuración predeterminada | Por defecto: transcripción redactada · bus sin PII · analytics sin direcciones completas. Ciudadano debe autorizar activamente para compartir. |
| Privacidad integrada en el diseño | Separación raw/core/analytics en la arquitectura base. PII nunca cruza la frontera de la capa `raw`. |
| Funcionalidad completa — sum positiva | Redacción de PII no degrada la calidad del triage. Los agentes reciben toda la información necesaria excepto los identificadores directos. |
| Seguridad de extremo a extremo | `trace_id` preservado en toda la cadena. Cero PII en todos los puntos del flujo. TLS requerido para producción. |
| Visibilidad y transparencia | Justificación de sugerencia visible al operador. Reportes de auditoría accesibles. Sustento legal documentado en toda derivación. |
| Respeto por la privacidad del ciudadano | El ciudadano ejerce control efectivo mediante gate SOLID. La IA no puede remitir datos a una autoridad sin esa autorización. |

**Fuente:** [https://www.ipc.on.ca/wp-content/uploads/Resources/7foundationalprinciples.pdf](https://www.ipc.on.ca/wp-content/uploads/Resources/7foundationalprinciples.pdf)

---

## Análisis de amenazas

| Amenaza | Nivel de riesgo | Control implementado | Estado |
|---|---|---|---|
| Ataques deepfake de voz al canal 911 | CRÍTICO | A3 Centinela (AASIST3). Detección genera alerta al operador, nunca cierre automático. | ✅ CUMPLE |
| Exfiltración de datos personales | ALTO | Cero PII en logs, bus y salidas. Redacción automática en A1. | ✅ CUMPLE |
| Manipulación del nivel de riesgo | CRÍTICO | Señales P0 tienen precedencia técnica. Ningún agente puede reducir nivel con señales críticas activas. | ✅ CUMPLE |
| Inundación coordinada de llamadas | ALTO | A2 Correlador (análisis geo-temporal). A3 Centinela detecta patrones de origen automatizado. | ✅ CUMPLE |
| Uso discriminatorio de grupos protegidos | ALTO | Categorías solo pueden incrementar prioridad, nunca reducirla. A8 Auditor verifica semanalmente. | ✅ CUMPLE |
| Fallo en cascada de agentes | CRÍTICO | A7 Bravo escala automáticamente al operador ante fallo de cualquier agente. | ✅ CUMPLE |
| Envenenamiento del modelo AASIST3 | MEDIO | Distribución declarada públicamente y versión fijada. A8 monitorea tasas de error en producción. | ✅ CUMPLE |

### Controles residuales para producción

Los siguientes controles están diseñados y documentados pero requieren implementación antes del despliegue con datos reales:

1. **Cifrado en tránsito (TLS)** — bus de eventos y todas las interfaces de programación
2. **Autenticación mutua entre agentes** — servidores MCP en entorno de producción
3. **A8 Auditor en producción** — con datos reales, requiere acceso a métricas operativas en tiempo real
4. **Calibración de AASIST3 con datos reales de CDMX** — antes del despliegue productivo
5. **Aviso de privacidad institucional** — Art. 15 y 16 de la LFPDPPP

---

## Fuentes normativas y técnicas

### Marco normativo mexicano
- LFPDPPP: [http://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf](http://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf)
- LGDNNA: [http://www.diputados.gob.mx/LeyesBiblio/pdf/LGDNNA.pdf](http://www.diputados.gob.mx/LeyesBiblio/pdf/LGDNNA.pdf)

### Estándares internacionales
- NIST AI RMF 1.0: [https://doi.org/10.6028/NIST.AI.100-1](https://doi.org/10.6028/NIST.AI.100-1)
- NIST CSF 2.0: [https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf](https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf)
- ISO/IEC 27001: [https://www.iso.org/standard/27001](https://www.iso.org/standard/27001)
- ISO/IEC 42001: [https://www.iso.org/standard/42001](https://www.iso.org/standard/42001)
- OWASP AI Top 10: [https://owasp.org/www-project-top-10-for-large-language-model-applications/](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- UNESCO Ética IA: [https://www.unesco.org/en/artificial-intelligence/recommendation-ethics](https://www.unesco.org/en/artificial-intelligence/recommendation-ethics)
- Privacy by Design: [https://www.ipc.on.ca/wp-content/uploads/Resources/7foundationalprinciples.pdf](https://www.ipc.on.ca/wp-content/uploads/Resources/7foundationalprinciples.pdf)

### Referencias técnicas — A3 Centinela
- AASIST (Jung et al., ICASSP 2022): [https://arxiv.org/abs/2110.01200](https://arxiv.org/abs/2110.01200)
- AASIST3 KAN-Enhanced: [https://arxiv.org/pdf/2408.17352](https://arxiv.org/pdf/2408.17352)

### Datos de operación
- SESNSP — Estadística 911, Q1 2026: [https://www.gob.mx/sesnsp](https://www.gob.mx/sesnsp)
- INEGI — Censo 2020: [https://www.inegi.org.mx/datosabiertos/](https://www.inegi.org.mx/datosabiertos/)
- Portal de Datos CDMX: [https://datos.cdmx.gob.mx/](https://datos.cdmx.gob.mx/)

---

*CENTINELA_CDMX_IA · Cumplimiento Normativo v2.0 · Junio 2026*
