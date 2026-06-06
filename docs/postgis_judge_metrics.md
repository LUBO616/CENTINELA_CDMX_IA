# PostGIS Judge Metrics - 911 AI Flow Demo

## 📋 Resumen Ejecutivo

Este documento explica las métricas territoriales de equidad calculadas con PostGIS para demostrar capacidades de análisis geoespacial en el contexto de un sistema de emergencias 911 asistido por IA.

**⚠️ DISCLAIMER CRÍTICO:**
- **TODOS los datos son SINTÉTICOS** para propósitos educativos
- **NO representan límites oficiales** de alcaldías de CDMX
- **NO son incidentes reales** de emergencia
- **NO contienen PII** (Información Personal Identificable)
- Las métricas son **demostrativas**, no de producción

---

## 🎯 Objetivo

Demostrar a jueces de hackathon que el sistema puede:

1. **Analizar equidad territorial** usando datos geoespaciales
2. **Detectar sesgos de cobertura** correlacionando acceso digital con reportes
3. **Medir eficiencia operativa** calculando horas de operador liberadas
4. **Validar detección de señales críticas** (P0) en casos de alto riesgo

---

## 🗺️ ¿Por Qué PostGIS?

### Capacidades Geoespaciales

PostGIS extiende PostgreSQL con tipos de datos y funciones espaciales:

```sql
-- Tipo de dato: GEOMETRY
CREATE TABLE alcaldias (
    geom GEOMETRY(MultiPolygon, 4326)  -- SRID 4326 = WGS84 (lat/lon)
);

-- Función espacial: ST_Contains
SELECT COUNT(*) 
FROM incidents i
JOIN alcaldias a ON ST_Contains(a.geom, i.geom);
```

### Ventajas

1. **Consultas espaciales nativas**: `ST_Contains`, `ST_Within`, `ST_Distance`
2. **Índices GIST**: Búsquedas espaciales rápidas
3. **Estándares OGC**: Compatibilidad con GIS profesionales
4. **Integración SQL**: No requiere herramientas externas

---

## 📊 Métricas Calculadas

### 1. Gini Coefficient (Equidad Territorial)

**Qué mide:** Desigualdad en la distribución de carga de riesgo entre alcaldías.

**Fórmula:**
```
Gini = (2 * Σ(i * x_i)) / (n * Σ(x_i)) - (n + 1) / n

Donde:
- x_i = carga de riesgo por alcaldía (incident_count * avg_risk)
- n = número de alcaldías (16)
- i = índice ordenado
```

**Interpretación:**
- `0.0` = Perfecta igualdad (todas las alcaldías tienen la misma carga)
- `1.0` = Perfecta desigualdad (una alcaldía tiene toda la carga)
- **Umbral de éxito: ≤ 0.35**

**Consulta PostGIS:**
```sql
SELECT 
    a.alcaldia_norm,
    COUNT(p.id) AS incident_count,
    AVG(p.risk_level) AS avg_risk,
    COUNT(p.id) * AVG(p.risk_level) AS risk_load
FROM geo.alcaldias_geom a
LEFT JOIN geo.synthetic_incident_points p 
    ON p.alcaldia_joined = a.alcaldia_norm
GROUP BY a.alcaldia_norm;
```

**Por qué importa:**
- Detecta si el sistema concentra recursos en ciertas zonas
- Identifica alcaldías desatendidas
- Valida distribución equitativa de atención

---

### 2. P0 Detection Recall Rate

**Qué mide:** Tasa de detección de señales críticas (P0) en incidentes clasificados como críticos.

**Fórmula:**
```
Recall = (Críticos con P0) / (Total críticos)
```

**Interpretación:**
- `1.0` = 100% de casos críticos tienen señales P0 detectadas
- `0.0` = Ningún caso crítico tiene señales P0
- **Umbral de éxito: ≥ 0.95**

**Consulta PostGIS:**
```sql
-- Total críticos
SELECT COUNT(*) 
FROM geo.synthetic_incident_points 
WHERE branch = 'critical';

-- Críticos con P0
SELECT COUNT(*) 
FROM geo.synthetic_incident_points 
WHERE branch = 'critical' 
AND p0_signals IS NOT NULL 
AND p0_signals != '';
```

**⚠️ Nota Importante:**
Esta es una **métrica sintética para demo**. En producción, el recall se mediría contra ground truth validado por humanos, no contra la propia clasificación del sistema.

**Por qué importa:**
- Valida que el sistema no degrada casos críticos
- Asegura que señales P0 se detectan consistentemente
- Cumple con principio de "nunca degradar ni cerrar como falsa una llamada con señales P0"

---

### 3. Coverage Bias Correlation

**Qué mide:** Correlación entre acceso digital y cantidad de incidentes reportados.

**Fórmula:**
```
Pearson Correlation = cov(X, Y) / (σ_X * σ_Y)

Donde:
- X = digital_access_index por alcaldía
- Y = incident_count por alcaldía
```

**Interpretación:**
- `+1.0` = Correlación positiva perfecta (más acceso → más reportes)
- `0.0` = Sin correlación
- `-1.0` = Correlación negativa perfecta
- **Umbral de éxito: |correlation| ≤ 0.20**

**Consulta PostGIS:**
```sql
SELECT 
    a.alcaldia_norm,
    COUNT(p.id) AS incident_count,
    d.digital_access_index
FROM geo.alcaldias_geom a
LEFT JOIN geo.synthetic_incident_points p 
    ON p.alcaldia_joined = a.alcaldia_norm
LEFT JOIN economia.digital_access_alcaldia d 
    ON d.alcaldia_norm = a.alcaldia_norm
GROUP BY a.alcaldia_norm, d.digital_access_index;
```

**Por qué importa:**
- Detecta sesgo de cobertura (zonas con más acceso digital reportan más)
- Identifica alcaldías subrepresentadas
- Valida que el sistema no favorece zonas con mejor infraestructura

---

### 4. Operator Hours Freed Per Day

**Qué mide:** Horas de operador liberadas por día mediante automatización de llamadas de bajo riesgo.

**Fórmula:**
```
Hours Freed = (Low Risk Automated * Minutes Per Call) / 60

Donde:
- Low Risk Automated = llamadas low con human_required = false
- Minutes Per Call = 8 minutos (threshold configurable)
```

**Interpretación:**
- Valor alto = Mayor eficiencia operativa
- **Umbral de éxito: ≥ 2.0 horas/día**

**Consulta PostGIS:**
```sql
SELECT COUNT(*) 
FROM geo.synthetic_incident_points 
WHERE branch = 'low' 
AND human_required = false;
```

**Por qué importa:**
- Cuantifica beneficio operativo de la IA
- Justifica inversión en automatización
- Libera operadores para casos complejos

---

## 🔍 ST_Contains: Función Clave

### ¿Qué Hace?

`ST_Contains(polygon, point)` retorna `true` si el punto está completamente dentro del polígono.

```sql
-- Asignar alcaldía a cada incidente
UPDATE geo.synthetic_incident_points AS p
SET alcaldia_joined = a.alcaldia_norm
FROM geo.alcaldias_geom AS a
WHERE ST_Contains(a.geom, p.geom);
```

### Alternativas

- **ST_Within(point, polygon)**: Inverso de ST_Contains
- **ST_Intersects(geom1, geom2)**: Más permisivo (incluye bordes)
- **ST_DWithin(geom1, geom2, distance)**: Dentro de cierta distancia

### Por Qué ST_Contains

1. **Semántica clara**: "El punto está dentro del polígono"
2. **Eficiente con índices GIST**: Búsqueda espacial rápida
3. **Estándar OGC**: Compatible con herramientas GIS

---

## 🛡️ Fallback Sintético

### Problema

En un MVP, no tenemos:
- Límites oficiales de alcaldías
- Geocodificación real de direcciones
- Datos históricos de emergencias

### Solución

Generamos datos sintéticos que **simulan** la estructura real:

1. **Polígonos sintéticos**: Cuadrados de ~5.5 km alrededor de coordenadas aproximadas
2. **Incidentes sintéticos**: Puntos aleatorios dentro de polígonos
3. **Acceso digital sintético**: Índices basados en percentiles de desarrollo

### Limitaciones

- **NO son límites oficiales**: Los polígonos son cuadrados simplificados
- **NO reflejan realidad**: Distribución uniforme, no basada en datos reales
- **NO para producción**: Solo para demostración de capacidades técnicas

### Validación

```sql
-- Verificar que todos los puntos tienen alcaldía asignada
SELECT COUNT(*) 
FROM geo.synthetic_incident_points 
WHERE alcaldia_joined IS NULL;
-- Resultado esperado: 0
```

---

## 📈 Umbrales y Justificación

| Métrica | Umbral | Justificación |
|---------|--------|---------------|
| Gini | ≤ 0.35 | Basado en índices de desigualdad aceptables (similar a Gini de ingreso en países desarrollados ~0.30-0.40) |
| P0 Recall | ≥ 0.95 | Estándar de sistemas críticos (99% ideal, 95% aceptable para MVP) |
| Correlation | ≤ 0.20 | Correlación débil aceptable (< 0.30 = débil, < 0.20 = muy débil) |
| Hours Freed | ≥ 2.0 | Mínimo 2 horas/día para justificar inversión (equivale a ~25% de un turno) |

---

## 🚀 Comandos de Ejecución

### Generar Datos y Métricas

```bash
# Generar todo (datos + métricas)
./scripts/08_setup_postgis_demo.sh

# Solo regenerar métricas (si datos ya existen)
python3 tools/generate_judge_metrics_postgis.py
```

### Validar

```bash
# Validar PostGIS y métricas
./scripts/09_test_postgis_metrics.sh

# Ver métricas en terminal
curl http://localhost:8010/judge/metrics/postgis | jq

# Ver GeoJSON en terminal
curl http://localhost:8010/judge/geo/alcaldias | jq '.type, (.features | length)'
```

### Consultas SQL Directas

```bash
# Conectar a PostgreSQL
docker exec -it postgres psql -U ai911_user -d ai911_db

# Ver alcaldías
SELECT alcaldia, alcaldia_norm FROM geo.alcaldias_geom;

# Ver incidentes por alcaldía
SELECT 
    alcaldia_joined, 
    COUNT(*) as total,
    AVG(risk_level) as avg_risk
FROM geo.synthetic_incident_points
GROUP BY alcaldia_joined
ORDER BY total DESC;

# Ver incidentes sin alcaldía (debe ser 0)
SELECT COUNT(*) FROM geo.synthetic_incident_points WHERE alcaldia_joined IS NULL;
```

---

## 📁 Estructura de Archivos

```
911-ai-flow-demo/
├── data/
│   ├── geo/
│   │   └── alcaldias_cdmx_synthetic.geojson    # 16 polígonos sintéticos
│   ├── demo/
│   │   └── incidentes_demo_geocoded.csv        # ≥160 incidentes con lat/lon
│   └── economia/
│       ├── constants.json                       # Umbrales de métricas
│       └── digital_access_alcaldia.csv          # Índice de acceso digital
├── evidence/
│   └── judge_metrics/
│       └── judge_metrics_postgis.json           # Métricas calculadas
├── tools/
│   ├── generate_synthetic_geo.py                # Genera GeoJSON
│   ├── generate_synthetic_incidents.py          # Genera incidentes
│   ├── load_postgis_demo_data.py                # Carga en PostGIS
│   └── generate_judge_metrics_postgis.py        # Calcula métricas
├── scripts/
│   ├── 08_setup_postgis_demo.sh                 # Orquesta generación
│   ├── 09_test_postgis_metrics.sh               # Valida todo
│   └── apply_postgis_schema.sql                 # Schema SQL
└── services/
    ├── api-analytics/app.py                     # Endpoints de métricas
    └── api-gateway/app.py                       # Proxies con CORS
```

---

## 🔒 Privacidad y Seguridad

### Datos Sintéticos

- **NO hay PII**: Ningún dato personal real
- **NO hay direcciones reales**: Solo zonas generalizadas
- **NO hay incidentes reales**: Todo es fabricado

### Redacción en Capas

1. **Generación**: Datos sintéticos desde el inicio
2. **Normalización**: Alcaldías normalizadas (snake_case)
3. **Agregación**: Métricas por zona, no por individuo

### Cumplimiento Legal

- **LFPDPPP (México)**: No aplica, no hay datos personales
- **GDPR (EU)**: No aplica, no hay datos de ciudadanos EU
- **Ley General de Protección de Datos**: No aplica, datos sintéticos

---

## ⚠️ Limitaciones del MVP

### Técnicas

1. **Polígonos simplificados**: Cuadrados, no límites oficiales
2. **Distribución uniforme**: No refleja patrones reales
3. **Sin geocodificación real**: Coordenadas aleatorias dentro de polígonos
4. **Sin validación externa**: Métricas no comparadas con ground truth

### Operacionales

1. **No escalable**: 160 incidentes vs. miles en producción
2. **Sin histórico**: Solo snapshot, no series temporales
3. **Sin ML real**: Clasificación determinista, no modelos entrenados
4. **Sin integración C5**: No conectado a sistemas reales

### Legales

1. **No certificado**: No auditado por autoridades
2. **No homologado**: No cumple estándares oficiales de C5
3. **Solo educativo**: No apto para uso en producción

---

## 🎯 Próximos Pasos (Fuera de Scope del MVP)

### Para Producción

1. **Límites oficiales**: Obtener shapefiles de INEGI
2. **Geocodificación real**: Integrar API de Google Maps o similar
3. **Datos históricos**: Analizar incidentes reales (con consentimiento)
4. **ML real**: Entrenar modelos con datos etiquetados
5. **Validación externa**: Comparar con métricas de C5

### Para Hackathon

1. **Dashboard interactivo**: Visualizar métricas en Lovable
2. **Mapa de calor**: Mostrar distribución de incidentes
3. **Gráficas temporales**: Tendencias por hora/día
4. **Comparación antes/después**: Simular impacto de IA

---

## 📚 Referencias

### PostGIS

- [PostGIS Documentation](https://postgis.net/docs/)
- [ST_Contains](https://postgis.net/docs/ST_Contains.html)
- [Spatial Indexes](https://postgis.net/docs/using_postgis_dbmanagement.html#gist_indexes)

### Métricas

- [Gini Coefficient](https://en.wikipedia.org/wiki/Gini_coefficient)
- [Pearson Correlation](https://en.wikipedia.org/wiki/Pearson_correlation_coefficient)
- [Precision and Recall](https://en.wikipedia.org/wiki/Precision_and_recall)

### Estándares

- [OGC Simple Features](https://www.ogc.org/standards/sfa)
- [WGS84 (SRID 4326)](https://epsg.io/4326)
- [GeoJSON Specification](https://geojson.org/)

---

## 📞 Soporte

Para preguntas sobre este documento:

1. Revisar código en `tools/generate_judge_metrics_postgis.py`
2. Ejecutar `./scripts/09_test_postgis_metrics.sh` para diagnóstico
3. Consultar logs en `docker compose logs api-analytics`

---

**Versión:** 1.0.0  
**Fecha:** 2026-06-06  
**Autor:** 911 AI Flow Demo Team  
**Licencia:** Educational Use Only

---

**⚠️ DISCLAIMER FINAL:**

Este sistema es una **demostración educativa** de capacidades técnicas. NO debe usarse para emergencias reales. Todos los datos son sintéticos. Para sistemas de producción, se requiere:

- Certificación por autoridades competentes
- Auditoría de seguridad y privacidad
- Cumplimiento de estándares oficiales
- Integración con C5 y protocolos establecidos
- Validación con datos reales (con consentimiento)

**Made with Bob** 🤖