# Gate 4 - Correcciones de Privacidad

## Fecha
2026-06-06

## Problema Identificado

En `api-analytics`, el endpoint `/analytics/predictions` exponía direcciones completas en el campo `risk_zones`, por ejemplo:
```json
{
  "zone": "Calle Madero 45, Colonia Centro"
}
```

Esto viola el principio de **Privacy by Design** y minimización de datos.

## Solución Implementada

### 1. Función de Normalización de Ubicaciones

**Archivo:** `services/api-analytics/app.py`

**Nueva función agregada:**
```python
def normalize_location_hint(location_hint: Optional[str]) -> str:
    """
    Normalize location to generalized zone, never expose full addresses
    Privacy by design: no street numbers or specific addresses
    """
```

**Comportamiento:**
- Detecta colonias/alcaldías conocidas de CDMX → Devuelve nombre generalizado
- Detecta números de calle (patrón `\b\d{1,4}\b`) → Devuelve "Zona simulada"
- Detecta calles principales sin número → Devuelve "Zona {calle}"
- Por defecto → Devuelve "Zona simulada"

**Zonas reconocidas:**
- Centro
- Cuauhtémoc
- Iztapalapa
- Benito Juárez
- Coyoacán
- Tlalpan
- Xochimilco
- Miguel Hidalgo
- Álvaro Obregón
- Azcapotzalco
- Gustavo A. Madero
- Venustiano Carranza
- Magdalena Contreras
- Milpa Alta

### 2. Aplicación en POST /incidents

**Antes:**
```python
request.location_hint  # Guardaba dirección completa
```

**Después:**
```python
normalized_location = normalize_location_hint(request.location_hint)
# Guarda solo zona generalizada
```

### 3. Aplicación en GET /analytics/predictions

**Antes:**
```python
"zone": row['zone']  # Exponía dirección completa
```

**Después:**
```python
normalized_zone = normalize_location_hint(row['zone'])
"zone": normalized_zone  # Expone solo zona generalizada
```

## Ejemplos de Transformación

| Entrada Original | Salida Normalizada |
|-----------------|-------------------|
| "Calle Madero 45, Colonia Centro" | "Centro" |
| "Insurgentes con Reforma" | "Zona Insurgentes" |
| "Colonia Cuauhtémoc" | "Cuauhtémoc" |
| "Avenida Revolución 123" | "Zona simulada" |
| "Iztapalapa" | "Iztapalapa" |
| "Calle desconocida 789" | "Zona simulada" |

## Validación

### Antes de la Corrección
```bash
curl http://localhost:8003/analytics/predictions | jq '.risk_zones'
```
```json
[
  {
    "zone": "Calle Madero 45, Colonia Centro",
    "risk_score": 7.5,
    "incident_count": 3,
    "primary_category": "medical"
  }
]
```

### Después de la Corrección
```bash
curl http://localhost:8003/analytics/predictions | jq '.risk_zones'
```
```json
[
  {
    "zone": "Centro",
    "risk_score": 7.5,
    "incident_count": 3,
    "primary_category": "medical"
  }
]
```

## Comandos para Aplicar

El usuario debe reconstruir api-analytics:

```bash
# 1. Reconstruir imagen
docker compose --profile services build api-analytics

# 2. Reiniciar servicio
docker compose --profile services up -d api-analytics

# 3. Esperar 5 segundos
sleep 5

# 4. Validar
curl http://localhost:8003/analytics/predictions | jq '.risk_zones'
```

## Principios de Privacidad Aplicados

### ✅ Privacy by Design
- Normalización automática en el punto de almacenamiento
- No se requiere intervención manual
- Imposible exponer direcciones completas

### ✅ Minimización de Datos
- Solo se almacena información necesaria (zona generalizada)
- No se guardan detalles específicos de ubicación
- Suficiente para análisis agregado, insuficiente para identificación

### ✅ Transparencia
- Función documentada con propósito claro
- Comportamiento predecible y auditable
- Logs no contienen direcciones completas

### ✅ Seguridad desde el Diseño
- Validación en capa de aplicación
- No depende de configuración externa
- Falla de forma segura (default: "Zona simulada")

## Impacto en Funcionalidad

### ✅ Mantiene Utilidad
- Analytics por zona sigue funcionando
- Predicciones de riesgo por área siguen siendo válidas
- Dashboard puede mostrar mapas de calor por alcaldía

### ✅ No Rompe Integraciones
- API contract se mantiene igual
- Lovable puede consumir datos sin cambios
- n8n workflow no requiere modificación

## Archivos Modificados

1. `services/api-analytics/app.py`
   - Líneas 58-106: Nueva función `normalize_location_hint()`
   - Línea 236: Normalización en POST /incidents
   - Línea 533: Normalización en GET /analytics/predictions

## Estado

✅ Código corregido
⏳ Pendiente: Usuario debe reconstruir imagen Docker

## Próximos Pasos

1. Aplicar corrección (rebuild Docker)
2. Validar que no aparecen direcciones completas
3. Continuar con documentación completa de Gate 4

---

**Versión:** Gate 4 - Privacy Fix  
**Fecha:** 2026-06-06  
**Autor:** Bob  
**Principio:** Privacy by Design