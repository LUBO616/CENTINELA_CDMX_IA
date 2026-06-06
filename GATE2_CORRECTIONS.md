# Gate 2 - Correcciones Finales

## Fecha
2026-06-06

## Problemas Identificados y Corregidos

### 1. ✅ Script de Test con call_ids Fijos
**Problema:** `scripts/04_test_environment.sh all` usaba call_ids hardcodeados que no existían en la base de datos, causando errores 422.

**Solución:** Reescrito completamente para encadenar datos reales:
- POST a `/raw-conversations` → extrae `call_id` y `trace_id` con jq
- POST a `/triage` usando el `call_id` real → extrae `risk_level`, `branch`, `case_category`, etc.
- POST a `/incidents` usando datos reales del triage
- Validación de `/analytics/summary` y `/analytics/predictions`

**Archivo:** `scripts/04_test_environment.sh`

### 2. ✅ Script de Seed sin Modo Direct
**Problema:** `scripts/05_seed_demo_data.sh` solo funcionaba con n8n webhook, no había modo para usar APIs directamente.

**Solución:** Agregado modo `direct` (default) que:
- Llama directamente a las 3 APIs en secuencia
- No depende de n8n para funcionar
- Preserva el modo `n8n` para Gate 3
- Uso: `./scripts/05_seed_demo_data.sh direct` o `./scripts/05_seed_demo_data.sh n8n`

**Archivo:** `scripts/05_seed_demo_data.sh`

### 3. ✅ Trazabilidad de trace_id
**Problema:** `api-triage` generaba un nuevo `trace_id` en lugar de preservar el de `api-ingest`, rompiendo la trazabilidad.

**Solución:**
- Agregado campo opcional `trace_id` al modelo `TriageRequest`
- Si viene en el request, se usa; si no, se genera uno nuevo
- Actualizado script de seed para pasar `trace_id` de ingest a triage
- Actualizado script de test para pasar `trace_id` de ingest a triage

**Archivos:**
- `services/api-triage/app.py` (líneas 293-298, 361)
- `scripts/05_seed_demo_data.sh` (línea 56)
- `scripts/04_test_environment.sh` (línea 217)

### 4. ✅ Warning de Pydantic en api-analytics
**Problema:** Campo `model_version` en `PredictionsResponse` causaba warning porque es palabra reservada de Pydantic.

**Solución:** Renombrado a `ai_model_version` para evitar conflicto.

**Archivo:** `services/api-analytics/app.py` (línea 135)

## Validación

### Comandos de Prueba

```bash
# 1. Levantar infraestructura
./scripts/01_start.sh infra

# 2. Esperar 10 segundos
sleep 10

# 3. Levantar servicios
./scripts/01_start.sh all

# 4. Esperar 5 segundos
sleep 5

# 5. Test completo (debe pasar todos)
./scripts/04_test_environment.sh all

# 6. Seed con modo direct (debe insertar 6 casos)
./scripts/05_seed_demo_data.sh direct

# 7. Verificar analytics
curl http://localhost:8003/analytics/summary | jq
curl http://localhost:8003/analytics/predictions | jq
```

### Resultados Esperados

**Test Environment:**
- ✅ Todos los tests de infraestructura pasan
- ✅ Todos los health endpoints responden
- ✅ Flow completo ingest→triage→analytics funciona
- ✅ GET endpoints devuelven datos
- ✅ Analytics summary y predictions responden

**Seed Demo Data:**
- ✅ 6 escenarios insertados correctamente
- ✅ Contadores en DB incrementan
- ✅ Distribución de riesgo correcta
- ✅ Categorías clasificadas correctamente
- ✅ P0 signals detectados en casos críticos

## Trazabilidad Completa

Ahora el flujo preserva el `trace_id` a través de todos los servicios:

```
api-ingest (genera trace_id)
    ↓ trace_id
api-triage (preserva trace_id)
    ↓ trace_id
api-analytics (almacena trace_id)
```

Esto permite:
- Seguimiento end-to-end de cada llamada
- Auditoría completa del flujo
- Debugging más fácil
- Cumplimiento con requisitos de trazabilidad

## Estado de Gate 2

✅ **COMPLETADO**

Todos los servicios funcionan correctamente:
- api-ingest: Redacción PII + almacenamiento raw
- api-triage: Clasificación determinista + detección P0
- api-analytics: Métricas + predicciones mock

Scripts operacionales:
- ✅ 00_precheck.sh
- ✅ 01_start.sh (infra/all)
- ✅ 02_stop.sh
- ✅ 03_logs.sh
- ✅ 04_test_environment.sh (infra/all) - CORREGIDO
- ✅ 05_seed_demo_data.sh (direct/n8n) - CORREGIDO

## Próximos Pasos (Gate 3)

1. Crear workflow n8n JSON
2. Documentar importación de workflow
3. Validar webhook end-to-end
4. Crear documentación técnica (architecture.md, etc.)
5. Crear README completo

## Notas Técnicas

- Los errores de basedpyright son normales (imports no resueltos en IDE, pero funcionan en Docker)
- PostgreSQL usa schemas separados (raw, core, analytics) para organización lógica
- Todos los endpoints JSON responden correctamente
- No se exponen secretos en el repo
- PII se redacta antes de almacenar
- P0 signals SIEMPRE elevan risk_level >= 6

---
**Autor:** Bob  
**Fecha:** 2026-06-06  
**Versión:** Gate 2 Final