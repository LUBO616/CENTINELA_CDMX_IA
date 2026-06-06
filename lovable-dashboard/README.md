# CENTINELA CDMX IA

Demo educativa de hackathon — dashboard web para simular un flujo de atención de emergencias asistido por IA. **No usar para emergencias reales.** Todos los datos son sintéticos.

## Configuración de URLs

Crea un archivo `.env` en la raíz del proyecto (ya incluido por defecto):

```
VITE_N8N_WEBHOOK_URL=http://localhost:5678/webhook/911-call
VITE_ANALYTICS_SUMMARY_URL=http://localhost:8003/analytics/summary
VITE_ANALYTICS_PREDICTIONS_URL=http://localhost:8003/analytics/predictions
```

Si los endpoints de analytics no responden, el dashboard entra en **modo demo local** con datos mock.

## Pantallas

- **Dashboard** — totales por nivel de riesgo, casos que requieren humano, señales P0 y panel de predicción.
- **Simular llamada** — envía un transcript al webhook de n8n y muestra el resultado de clasificación.

## Stack

TanStack Start + React 19 + Tailwind v4 + shadcn/ui.
