# Fuentes de Datos — CENTINELA_CDMX_IA

---

## Datos operativos del 911

### Estadística Nacional de Llamadas de Emergencia al 9-1-1

**Organismo:** Secretariado Ejecutivo del Sistema Nacional de Seguridad Pública (SESNSP)  
**Portal oficial:** [https://www.gob.mx/sesnsp](https://www.gob.mx/sesnsp)  
**Último corte utilizado:** 31 de marzo de 2026 (publicado en abril 2026)

| Dato | Valor Q1 2026 |
|---|---|
| Total de llamadas | 13,158,317 |
| Procedentes (emergencias reales) | 3,712,428 (28.2%) |
| Improcedentes | 9,445,889 (71.8%) |
| CDMX en procedentes | 8.7% (~323,000) |

**Distribución de procedentes por tipo:**

| Tipo | Total | Proporción |
|---|---|---|
| Seguridad | 2,004,921 | 54% |
| Asistencia | 629,607 | 17% |
| Médico | 548,962 | 14.8% |
| Protección Civil | 318,009 | 8.6% |
| Otros servicios | 169,647 | 4.6% |
| Servicios públicos | 41,282 | 1.1% |

**Distribución de improcedentes por tipo:**

| Tipo | Total | Proporción |
|---|---|---|
| Llamada muda | 5,538,774 | 58.6% |
| Llamada incompleta | 1,347,834 | 14.3% |
| Otras no emergencia | 1,156,555 | 12.2% |
| Broma por niños | 533,340 | 5.6% |
| Jóvenes/adultos jugando | 412,760 | 4.4% |
| Transferencia | 245,106 | 2.6% |

**Nota técnica:** Este contexto es el que motiva la arquitectura dual de CENTINELA — el A2 Correlador trabaja sobre el 71.8% de improcedentes para filtrarlas sin degradar riesgo, mientras que A3 Centinela protege contra el vector emergente de llamadas automatizadas con voz sintética.

---

## Datos de población — Normalización geoespacial

### Censo de Población y Vivienda INEGI 2020

**Organismo:** Instituto Nacional de Estadística y Geografía (INEGI)  
**Portal oficial:** [https://www.inegi.org.mx/](https://www.inegi.org.mx/)  
**Datos abiertos INEGI:** [https://www.inegi.org.mx/datosabiertos/](https://www.inegi.org.mx/datosabiertos/)  
**Dataset CDMX:** [https://datos.cdmx.gob.mx/organization/instituto-nacional-de-estadistica-y-geografia-inegi](https://datos.cdmx.gob.mx/organization/instituto-nacional-de-estadistica-y-geografia-inegi)

**Archivo incluido en el repositorio:** `ITER_09CSV20.csv`

| Campo ITER | Descripción | Uso en CENTINELA |
|---|---|---|
| ENTIDAD / NOM_ENT | Clave y nombre de la entidad | Filtro: entidad 09 = Ciudad de México |
| MUN / NOM_MUN | Municipio (alcaldía en CDMX) | Normalización por alcaldía en A5 y A8 |
| LOC / NOM_LOC | Localidad | Granularidad geoespacial |
| LONGITUD / LATITUD | Coordenadas geográficas | Indexación H3 en A5 Cartógrafo |
| POBTOT | Población total | Denominador para normalización de riesgo |
| POBFEM / POBMAS | Población por sexo | Factor de vulnerabilidad en A4 |
| P_0A2 ... P_85YMAS | Pirámide de edad por grupos | Factores de vulnerabilidad por grupo etario |
| PCON_DISC | Personas con discapacidad | Factor de protección reforzada |
| P3YM_HLI | Hablantes de lengua indígena | Factor: necesidad de intérprete |
| POB_AFRO | Población afrodescendiente | Factor de vulnerabilidad interseccional |

**Datos de CDMX (totales de entidad):**
- Población total: 9,209,944
- Mujeres: 4,805,017 (52.2%)
- Hombres: 4,404,927 (47.8%)
- Personas con discapacidad: 493,589
- Hablantes de lengua indígena: 125,153
- Personas de 60 años o más: 1,022,105 (11.1%)
- Personas de 0-14 años: 1,652,773 (17.9%)

**Uso técnico en A5 Cartógrafo:**
El agente A5 usa la población por hexágono H3 como denominador para calcular `risk_norm` — el riesgo normalizado por habitante. Esto evita que las alcaldías más densamente pobladas (Iztapalapa, Gustavo A. Madero) acaparen recursos por volumen bruto de llamadas cuando el riesgo per cápita puede ser equivalente o menor que en alcaldías menos densas.

**Impacto medido:** Coeficiente de Gini de atención geográfica: 0.42 (sin normalización) → 0.28 (con normalización INEGI). Umbral de éxito establecido: ≤0.35.

---

## Portal de Datos Abiertos CDMX

**Portal:** [https://datos.cdmx.gob.mx/](https://datos.cdmx.gob.mx/)

Fuente complementaria para datos históricos de incidentes reportados al 911 en la Ciudad de México, a nivel de alcaldía y tipo de incidente. Útil para calibración del modelo base de A5 Cartógrafo y validación del Coeficiente de Gini.

---

## Referencias académicas — A3 Centinela

### AASIST — Audio Anti-Spoofing Using Integrated Spectro-Temporal Graph Attention Networks

**Autores:** Jung et al.  
**Publicado:** ICASSP 2022  
**arXiv:** [https://arxiv.org/abs/2110.01200](https://arxiv.org/abs/2110.01200)

AASIST es el modelo de referencia para detección de anti-spoofing de voz. Usa redes de atención de grafos espectro-temporales para detectar artefactos en voz sintética generada por sistemas TTS y Voice Conversion modernos.

### AASIST3 — KAN-Enhanced AASIST para ASVspoof 2024

**arXiv:** [https://arxiv.org/pdf/2408.17352](https://arxiv.org/pdf/2408.17352)

AASIST3 extiende AASIST con Kolmogorov-Arnold Networks (KAN) para mejorar el rendimiento en distribuciones modernas de voz sintética (ASVspoof 2024 / in-the-wild).

**Nota crítica sobre distribución de entrenamiento:**  
El modelo implementado en A3 debe usar distribuciones de entrenamiento recientes: **ASVspoof5, Codecfake o in-the-wild**. ASVspoof 2019 no cubre los codecs modernos de síntesis de voz utilizados en ataques actuales y produciría tasas de falsos negativos inaceptables en producción.

### Datasets de referencia

| Dataset | Descripción | Uso |
|---|---|---|
| ASVspoof 2019 | Benchmark histórico | **Insuficiente para producción** |
| ASVspoof 2024 / ASVspoof5 | Distribución moderna con codecs actuales | Recomendado para entrenamiento |
| Codecfake | Voz sintética generada con codecs de compresión moderna | Complementario |
| In-the-wild | Grabaciones reales de voz sintética en circulación | Recomendado para validación |

---

## Fuentes normativas completas

### Marco normativo mexicano

| Instrumento | URL |
|---|---|
| LFPDPPP (texto completo) | [http://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf](http://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf) |
| Reglamento LFPDPPP | [https://www.diputados.gob.mx/LeyesBiblio/regley/Reg_LFPDPPP.pdf](https://www.diputados.gob.mx/LeyesBiblio/regley/Reg_LFPDPPP.pdf) |
| LGDNNA (texto completo) | [http://www.diputados.gob.mx/LeyesBiblio/pdf/LGDNNA.pdf](http://www.diputados.gob.mx/LeyesBiblio/pdf/LGDNNA.pdf) |
| Reglamento LGDNNA | [https://www.diputados.gob.mx/LeyesBiblio/regley/Reg_LGDNNA.pdf](https://www.diputados.gob.mx/LeyesBiblio/regley/Reg_LGDNNA.pdf) |

### Estándares internacionales

| Estándar | URL |
|---|---|
| NIST AI RMF 1.0 (PDF) | [https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf) |
| NIST CSF 2.0 (PDF) | [https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf](https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf) |
| ISO/IEC 27001:2022 | [https://www.iso.org/standard/27001](https://www.iso.org/standard/27001) |
| ISO/IEC 42001:2023 | [https://www.iso.org/standard/42001](https://www.iso.org/standard/42001) |
| OWASP AI Top 10 (2025) | [https://owasp.org/www-project-top-10-for-large-language-model-applications/](https://owasp.org/www-project-top-10-for-large-language-model-applications/) |
| OWASP AI Top 10 (PDF) | [https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf](https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf) |
| UNESCO Ética IA | [https://www.unesco.org/en/artificial-intelligence/recommendation-ethics](https://www.unesco.org/en/artificial-intelligence/recommendation-ethics) |
| Privacy by Design | [https://www.ipc.on.ca/wp-content/uploads/Resources/7foundationalprinciples.pdf](https://www.ipc.on.ca/wp-content/uploads/Resources/7foundationalprinciples.pdf) |

---

*CENTINELA_CDMX_IA · Fuentes de Datos v1.0 · Junio 2026*
