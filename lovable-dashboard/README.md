# CENTINELA_CDMX_IA — Dashboard del Operador

Panel en tiempo real para operadores del sistema 911 CDMX.  
El operador humano tiene la decisión final en todo momento — la IA asiste y sugiere, nunca reemplaza.

> **Datos sintéticos** en modo prototipo. Para producción, conectar al stack Docker del repositorio principal.

## Configuración de URLs

Crea un archivo `.env` en la raíz de este directorio:

```env
# Via api-gateway (recomendado — evita exponer credenciales de n8n)
VITE_N8N_WEBHOOK_URL=http://localhost:8010/911-call
VITE_ANALYTICS_SUMMARY_URL=http://localhost:8010/analytics/summary
VITE_ANALYTICS_PREDICTIONS_URL=http://localhost:8010/analytics/predictions

# Gate SOLID — OFF por defecto (Privacy by Design, LFPDPPP Art. 8)
VITE_SOLID_CONSENT_DEFAULT=false

# Directo a n8n (alternativa sin gateway)
# VITE_N8N_WEBHOOK_URL=http://localhost:5678/webhook/911-call
```

Si los endpoints no responden, el dashboard entra en **modo mock local** con datos de demostración.

## Pantallas

- **Panel principal** — nivel de riesgo en tiempo real, señales P0 detectadas, grupos de protección activados, sugerencia de autoridad competente, toggle SOLID.
- **Mapa de calor** — hotspots geoespaciales por alcaldía CDMX (normalizados por población INEGI 2020).
- **Simular llamada** — envía un transcript al webhook de n8n y muestra el resultado completo de clasificación A4 Triador.
- **Métricas** — totales por nivel de riesgo, rama, categoría, casos con intervención humana requerida.

## Restricciones de UX implementadas

- Toggle SOLID desactivado por defecto — el operador debe activarlo explícitamente
- Nivel de riesgo siempre etiquetado como **SUGERENCIA** — nunca como DECISIÓN
- Alertas P0 no tienen botón de descartar
- Footer permanente: *"Operador: tú tienes la decisión final"*

## Stack

TanStack Start + React 19 + Tailwind v4 + shadcn/ui.

## Levantar el backend

```bash
# Desde la raíz del repositorio
./scripts/01_start.sh all
# Dashboard disponible en: http://localhost:3000
```

Ver [`docs/lovable_integration.md`](../docs/lovable_integration.md) para la integración completa.
