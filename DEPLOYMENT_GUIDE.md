# 🚀 Guía de Despliegue - Entorno de Microservicios

## 📋 Resumen

Esta guía explica cómo desplegar las mejoras de IA y métricas económicas en el entorno real de producción con Docker y microservicios.

## ✅ Cambios Implementados

1. **IA de Sentimientos**: Análisis automático con pysentimiento en `api-triage`
2. **Script de Métricas**: Calculadora de impacto económico independiente
3. **Datos del Economista**: Archivos de población y acceso digital

## 🔧 Requisitos Previos

- Docker y Docker Compose instalados
- Acceso al repositorio Git
- Variables de entorno configuradas
- PostgreSQL corriendo (parte del stack)

## 📦 Paso 1: Obtener el Código

```bash
# Clonar o actualizar el repositorio
cd /ruta/a/tu/proyecto
git fetch origin

# Checkout de la rama demo
git checkout demo/economist-metrics-ia

# Verificar que estás en la rama correcta
git branch --show-current
```

## 🐳 Paso 2: Variables de Entorno

Crear o actualizar el archivo `.env` en la raíz del proyecto:

```bash
# .env
DATABASE_URL=postgresql://emergency_user:TU_PASSWORD_SEGURO@postgres:5432/emergency_demo
CORS_ORIGINS=http://localhost:3000,https://tu-dominio-produccion.com
SERVICE_PORT=8002
LOG_LEVEL=INFO

# Para producción, cambiar a WARNING o ERROR
# LOG_LEVEL=WARNING
```

## 🏗️ Paso 3: Reconstruir el Servicio api-triage

El servicio `api-triage` es el único que cambió. No necesitas reconstruir todo el stack.

```bash
# Opción 1: Reconstruir solo api-triage
docker-compose build api-triage

# Opción 2: Reconstruir sin caché (si hay problemas)
docker-compose build --no-cache api-triage
```

## 🚀 Paso 4: Desplegar

```bash
# Detener el servicio actual
docker-compose stop api-triage

# Iniciar el servicio actualizado
docker-compose up -d api-triage

# Verificar que está corriendo
docker-compose ps api-triage
```

## 📊 Paso 5: Verificar el Despliegue

### 5.1 Health Check

```bash
curl http://localhost:8002/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "service": "api-triage",
  "version": "1.0.0",
  "rules_loaded": 150,
  "timestamp": "2026-06-06T17:00:00Z"
}
```

### 5.2 Probar Análisis de Sentimientos

```bash
curl -X POST http://localhost:8002/triage \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "TEST-DEPLOY-001",
    "transcript": "¡Ayuda urgente! Hay un incendio en mi casa, estoy muy asustado",
    "consent": true
  }'
```

**Verifica que la respuesta incluya:**
```json
{
  "sentiment_analysis": {
    "emotion": "fear",
    "emotion_probs": {...},
    "sentiment": "NEG",
    "sentiment_probs": {...}
  },
  "risk_level": 8,
  "p0_signals": ["incendio"],
  ...
}
```

### 5.3 Ver Logs

```bash
# Ver logs en tiempo real
docker-compose logs -f api-triage

# Ver últimas 100 líneas
docker-compose logs --tail=100 api-triage
```

## 📈 Paso 6: Ejecutar Script de Métricas

El script de métricas es **independiente** y se ejecuta fuera de Docker:

### Opción A: Ejecución Local

```bash
# Instalar dependencias (solo primera vez)
pip install pandas numpy psycopg2-binary

# Configurar variable de entorno
export DATABASE_URL="postgresql://emergency_user:PASSWORD@localhost:5432/emergency_demo"

# Ejecutar script
cd Hackathon/CENTINELA_CDMX_IA
python tools/calculate_impact_metrics.py
```

### Opción B: Ejecución con Docker (Recomendado para Producción)

```bash
# Crear un contenedor temporal para ejecutar el script
docker run --rm \
  --network centinela_default \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/evidence:/app/evidence \
  -v $(pwd)/tools:/app/tools \
  -e DATABASE_URL="postgresql://emergency_user:PASSWORD@postgres:5432/emergency_demo" \
  python:3.11-slim \
  bash -c "pip install pandas numpy psycopg2-binary && python /app/tools/calculate_impact_metrics.py"
```

**Salida esperada:**
```
================================================================================
CENTINELA CDMX - Calculo de Metricas de Impacto
================================================================================

Cargando datos...
   - Poblacion: 16 alcaldias
   - Acceso digital: 16 alcaldias
   - Datos de triaje: 500 llamadas

Calculando metricas...
   - Horas liberadas
   - Recall P0
   - Equidad territorial (Gini)
   - Correlacion de sesgo digital

Generando reporte...
   - Reporte guardado: evidence/economist_metrics/impact_metrics_YYYYMMDD_HHMMSS.md
   - Metricas JSON: evidence/economist_metrics/impact_metrics_YYYYMMDD_HHMMSS.json

================================================================================
RESUMEN DE METRICAS
================================================================================
Horas liberadas: 7.25 hrs
Recall P0: 95.2% OK
Gini (equidad): 0.28 OK
Correlacion digital: 0.08 OK
================================================================================

Proceso completado exitosamente
```

## ⚠️ Consideraciones Importantes

### 1. Primera Ejecución (Descarga de Modelos)

La primera vez que se ejecuta el servicio, pysentimiento descarga los modelos de IA:
- **Tiempo**: 2-5 minutos
- **Tamaño**: ~500 MB
- **Ubicación**: Se cachean en el contenedor

**Para pre-descargar modelos (opcional):**

Modificar `services/api-triage/Dockerfile`:

```dockerfile
# Agregar después de instalar requirements
RUN python -c "from pysentimiento import create_analyzer; \
    create_analyzer(task='emotion', lang='es'); \
    create_analyzer(task='sentiment', lang='es')"
```

### 2. Recursos del Contenedor

El servicio api-triage con IA requiere más recursos:
- **RAM**: Mínimo 2 GB (recomendado 4 GB)
- **CPU**: 2 cores recomendados
- **Disco**: +1 GB para modelos

**Configurar límites en docker-compose.yml:**

```yaml
services:
  api-triage:
    # ... configuración existente ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### 3. Variables de Entorno Críticas

```bash
# Producción
DATABASE_URL=postgresql://user:pass@postgres:5432/db
CORS_ORIGINS=https://dashboard.centinela.cdmx.gob.mx
LOG_LEVEL=WARNING  # Reducir logs en producción

# Desarrollo
DATABASE_URL=postgresql://user:pass@localhost:5432/db
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=DEBUG
```

## 🔄 Rollback (Si algo falla)

```bash
# 1. Detener el servicio
docker-compose stop api-triage

# 2. Volver a la rama anterior
git checkout main  # o la rama que estabas usando

# 3. Reconstruir
docker-compose build api-triage

# 4. Reiniciar
docker-compose up -d api-triage

# 5. Verificar
docker-compose logs -f api-triage
```

## 🔍 Troubleshooting

### Problema: "Connection refused" al conectar a PostgreSQL

**Solución:**
```bash
# Verificar que PostgreSQL está corriendo
docker-compose ps postgres

# Verificar la red
docker network ls
docker network inspect centinela_default

# Verificar la variable DATABASE_URL
docker-compose exec api-triage env | grep DATABASE_URL
```

### Problema: "ModuleNotFoundError: No module named 'pysentimiento'"

**Solución:**
```bash
# Reconstruir sin caché
docker-compose build --no-cache api-triage
docker-compose up -d api-triage
```

### Problema: Servicio muy lento en primera ejecución

**Causa:** Descarga de modelos de IA

**Solución:**
- Esperar 2-5 minutos en la primera ejecución
- Pre-descargar modelos en el Dockerfile (ver sección anterior)
- Verificar logs: `docker-compose logs -f api-triage`

### Problema: Error de memoria (OOM)

**Solución:**
```bash
# Aumentar límites de memoria
# Editar docker-compose.yml y agregar:
deploy:
  resources:
    limits:
      memory: 4G

# Reiniciar
docker-compose up -d api-triage
```

## 📊 Monitoreo

### Ver Uso de Recursos

```bash
# Recursos en tiempo real
docker stats centinela-api-triage

# Información del contenedor
docker inspect centinela-api-triage
```

### Logs Estructurados

```bash
# Logs con timestamp
docker-compose logs -f --timestamps api-triage

# Filtrar por nivel
docker-compose logs api-triage | grep ERROR
docker-compose logs api-triage | grep WARNING
```

## 🎯 Checklist de Despliegue

- [ ] Código actualizado desde `demo/economist-metrics-ia`
- [ ] Variables de entorno configuradas en `.env`
- [ ] Servicio api-triage reconstruido
- [ ] Health check exitoso
- [ ] Análisis de sentimientos funcionando
- [ ] Logs sin errores críticos
- [ ] Script de métricas ejecutado
- [ ] Reportes generados en `evidence/economist_metrics/`
- [ ] Documentación revisada
- [ ] Equipo notificado del despliegue

## 📚 Archivos Importantes

```
CENTINELA_CDMX_IA/
├── services/
│   └── api-triage/
│       ├── app.py                    # Servicio con IA integrada
│       ├── requirements.txt          # Incluye pysentimiento
│       └── Dockerfile                # Configuración del contenedor
├── scripts/
│   └── sentiment_analyzer.py        # Módulo de análisis de sentimientos
├── tools/
│   └── calculate_impact_metrics.py  # Script de métricas económicas
├── data/
│   └── economia/
│       ├── ITER_09CSV20.csv         # Datos de población INEGI
│       ├── digital_access_alcaldia.csv
│       └── economia_constants.json
├── evidence/
│   └── economist_metrics/           # Reportes generados
├── docker-compose.yml               # Orquestación de servicios
├── .env                             # Variables de entorno
├── IMPLEMENTATION_SUMMARY.md        # Resumen técnico
└── DEPLOYMENT_GUIDE.md             # Esta guía
```

## 🆘 Soporte

Si encuentras problemas:

1. **Revisar logs**: `docker-compose logs -f api-triage`
2. **Verificar health check**: `curl http://localhost:8002/health`
3. **Consultar documentación**: `IMPLEMENTATION_SUMMARY.md`
4. **Rollback si es necesario**: Ver sección de Rollback

## 📝 Notas Finales

- **No afecta otras ramas**: Esta implementación está en `demo/economist-metrics-ia`
- **Independiente**: El script de métricas no afecta los servicios
- **Reversible**: Puedes hacer rollback en cualquier momento
- **Probado**: Todos los componentes han sido validados

---

**Última actualización**: 2026-06-06  
**Versión**: 1.0  
**Rama**: demo/economist-metrics-ia