# Integración con Lovable - 911 AI Flow Demo

## Descripción General

Este documento explica cómo integrar el dashboard de Lovable con el backend 911 AI Flow Demo. Incluye configuración de variables de entorno, ejemplos de payloads, sugerencias de componentes UI, y consideraciones de CORS.

**⚠️ Importante:** Este es un MVP educativo. No usar para emergencias reales.

---

## Tabla de Contenidos

1. [Arquitectura de Integración](#arquitectura-de-integración)
2. [Variables de Entorno](#variables-de-entorno)
3. [Endpoints Disponibles](#endpoints-disponibles)
4. [Ejemplos de Integración](#ejemplos-de-integración)
5. [Componentes UI Sugeridos](#componentes-ui-sugeridos)
6. [Manejo de Errores](#manejo-de-errores)
7. [CORS y Seguridad](#cors-y-seguridad)
8. [Modo Demo](#modo-demo)

---

## Arquitectura de Integración

### Opción 1: Con API Gateway (Recomendado para Lovable)

```
┌─────────────────────────────────────────────────────────────┐
│                    Lovable Dashboard                        │
│  (React/TypeScript - Puerto 5173 o similar)                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/JSON (sin CORS issues)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Gateway (Puerto 8010)                 │
│              http://localhost:8010/911-call                 │
│              http://localhost:8010/analytics/*              │
│                    (CORS habilitado, sin auth)              │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  n8n webhook │   │ api-analytics│   │  api-ingest  │
│   :5678      │   │   :8003      │   │   :8001      │
└──────────────┘   └──────────────┘   └──────────────┘
        │                                       │
        └───────────────┬───────────────────────┘
                        ▼
                ┌──────────────┐
                │  api-triage  │
                │   :8002      │
                └──────────────┘
```

**Ventajas del Gateway:**
- ✅ **Sin problemas de CORS:** CORS habilitado para todos los orígenes
- ✅ **Sin autenticación:** No necesitas Basic Auth desde Lovable
- ✅ **URLs simplificadas:** Un solo punto de entrada
- ✅ **Timeout configurado:** 15 segundos por request
- ✅ **Logs sin PII:** No registra transcripts

### Opción 2: Directo a n8n (Alternativa)

```
┌─────────────────────────────────────────────────────────────┐
│                    Lovable Dashboard                        │
│  (React/TypeScript - Puerto 5173 o similar)                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/JSON + Basic Auth
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   n8n Webhook (Orquestador)                 │
│              http://localhost:5678/webhook/911-call         │
│                    (Basic Auth: admin/changeme)             │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  api-ingest  │   │  api-triage  │   │ api-analytics│
│   :8001      │   │   :8002      │   │   :8003      │
└──────────────┘   └──────────────┘   └──────────────┘
```

**Desventajas:**
- ❌ Requiere manejar Basic Auth en frontend
- ❌ Posibles problemas de CORS
- ❌ Más complejo para Lovable

**Flujo Recomendado (con Gateway):**

1. **Dashboard → API Gateway:** Enviar llamada simulada a `/911-call`
2. **Gateway → n8n Webhook:** Reenvío con autenticación interna
3. **n8n → Microservicios:** Orquestación automática
4. **n8n → Gateway → Dashboard:** Respuesta consolidada
5. **Dashboard → Gateway:** Consultar métricas en `/analytics/summary` y `/analytics/predictions`

---

## Variables de Entorno

### Archivo `.env` en Lovable

Crear archivo `.env` en la raíz del proyecto Lovable:

```bash
# API Gateway URLs (Recomendado - Sin CORS issues)
VITE_N8N_WEBHOOK_URL=http://localhost:8010/911-call
VITE_ANALYTICS_SUMMARY_URL=http://localhost:8010/analytics/summary
VITE_ANALYTICS_PREDICTIONS_URL=http://localhost:8010/analytics/predictions

# Modo demo
VITE_DEMO_MODE=true
VITE_SHOW_PRIVACY_WARNINGS=true

# ============================================================================
# Alternativa: URLs directas (requiere manejar CORS y Basic Auth)
# ============================================================================
# VITE_N8N_WEBHOOK_URL=http://localhost:5678/webhook/911-call
# VITE_N8N_USERNAME=admin
# VITE_N8N_PASSWORD=changeme
# VITE_ANALYTICS_API_URL=http://localhost:8003
```

### Uso en Código TypeScript

```typescript
// src/config/api.ts
export const API_CONFIG = {
  // Opción 1: Con API Gateway (Recomendado)
  gateway: {
    webhookUrl: import.meta.env.VITE_N8N_WEBHOOK_URL || 'http://localhost:8010/911-call',
    summaryUrl: import.meta.env.VITE_ANALYTICS_SUMMARY_URL || 'http://localhost:8010/analytics/summary',
    predictionsUrl: import.meta.env.VITE_ANALYTICS_PREDICTIONS_URL || 'http://localhost:8010/analytics/predictions',
  },
  
  // Opción 2: Directo a n8n (Alternativa)
  n8nWebhook: {
    url: import.meta.env.VITE_N8N_WEBHOOK_URL || 'http://localhost:5678/webhook/911-call',
    username: import.meta.env.VITE_N8N_USERNAME || 'admin',
    password: import.meta.env.VITE_N8N_PASSWORD || 'changeme',
  },
  
  analytics: {
    url: import.meta.env.VITE_ANALYTICS_API_URL || 'http://localhost:8003',
  },
  
  demoMode: import.meta.env.VITE_DEMO_MODE === 'true',
  showPrivacyWarnings: import.meta.env.VITE_SHOW_PRIVACY_WARNINGS === 'true',
};
```

---

## Endpoints Disponibles

### 1. API Gateway (Recomendado para Lovable)

**Endpoint Principal:**
```
POST http://localhost:8010/911-call
```

**Ventajas:**
- ✅ **Sin CORS issues:** Configurado con `allow_origins=["*"]`
- ✅ **Sin autenticación:** No necesitas Basic Auth desde frontend
- ✅ **Orquestación automática:** Reenvía a n8n internamente
- ✅ **Respuesta consolidada:** Un solo request
- ✅ **Timeout configurado:** 15 segundos
- ✅ **Logs sin PII:** No registra transcripts

**Endpoints de Analytics:**
```
GET http://localhost:8010/analytics/summary
GET http://localhost:8010/analytics/predictions
```

**Ventajas:**
- ✅ Sin CORS issues
- ✅ Sin autenticación
- ✅ Proxy directo a api-analytics
- ✅ Respuesta rápida

---

### 2. n8n Webhook Directo (Alternativa)

**Endpoint Principal:**
```
POST http://localhost:5678/webhook/911-call
```

**Ventajas:**
- ✅ Orquestación automática de los 3 microservicios
- ✅ Respuesta consolidada en un solo request
- ✅ Manejo de errores centralizado
- ✅ Retry automático en caso de fallo

**Desventajas:**
- ❌ Requiere autenticación Basic Auth
- ❌ Posibles problemas de CORS
- ❌ Más complejo para Lovable

---

### 3. API Analytics Directo (Alternativa)

**Endpoints de Solo Lectura:**
```
GET http://localhost:8003/analytics/summary
GET http://localhost:8003/analytics/predictions
GET http://localhost:8003/incidents?limit=10&offset=0
```

**Ventajas:**
- ✅ No requiere autenticación
- ✅ Respuesta rápida
- ✅ Ideal para dashboards en tiempo real

**Desventajas:**
- ❌ Posibles problemas de CORS dependiendo del navegador

**Uso:**
- Métricas agregadas
- Predicciones mock
- Historial de incidentes

---

## Ejemplos de Integración

### 1. Enviar Llamada Simulada (TypeScript) - Con API Gateway

```typescript
// src/services/emergencyService.ts
import { API_CONFIG } from '../config/api';

interface EmergencyCallPayload {
  transcript: string;
  location_hint?: string;
  solid_consent?: boolean;
  metadata?: {
    source: string;
    timestamp: string;
  };
}

interface EmergencyCallResponse {
  success: boolean;
  call_id: string;
  trace_id: string;
  risk_level: number;
  branch: 'low' | 'mid' | 'critical';
  case_category: string;
  human_required: boolean;
  p0_signals: string[];
  primary_authority: string;
  support_authorities: string[];
  public_stage_phrase: string;
  rationale_public: string;
  incident_id: string;
  processed_at: string;
}

export async function submitEmergencyCall(
  payload: EmergencyCallPayload
): Promise<EmergencyCallResponse> {
  // Usar API Gateway (sin autenticación, sin CORS issues)
  const url = API_CONFIG.gateway.webhookUrl;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      ...payload,
      metadata: {
        source: 'lovable_dashboard',
        timestamp: new Date().toISOString(),
        ...payload.metadata,
      },
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to submit emergency call');
  }

  return response.json();
}
```

**Alternativa: Con n8n Directo (requiere Basic Auth)**

```typescript
export async function submitEmergencyCallDirect(
  payload: EmergencyCallPayload
): Promise<EmergencyCallResponse> {
  const { url, username, password } = API_CONFIG.n8nWebhook;

  // Crear Basic Auth header
  const authHeader = 'Basic ' + btoa(`${username}:${password}`);

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': authHeader,
    },
    body: JSON.stringify({
      ...payload,
      metadata: {
        source: 'lovable_dashboard',
        timestamp: new Date().toISOString(),
        ...payload.metadata,
      },
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to submit emergency call');
  }

  return response.json();
}
```

**Ejemplo de Uso:**
```typescript
// src/components/EmergencyForm.tsx
import { submitEmergencyCall } from '../services/emergencyService';

async function handleSubmit(transcript: string, location: string) {
  try {
    const result = await submitEmergencyCall({
      transcript,
      location_hint: location,
      solid_consent: true,
    });

    console.log('Call processed:', result);
    
    // Mostrar resultado al usuario
    if (result.human_required) {
      alert(`⚠️ Atención humana requerida\nRiesgo: ${result.risk_level}/10\nAutoridad: ${result.primary_authority}`);
    } else {
      alert(`✅ Llamada procesada\nCategoría: ${result.case_category}\nRiesgo: ${result.risk_level}/10`);
    }
  } catch (error) {
    console.error('Error submitting call:', error);
    alert('Error al procesar la llamada. Intente nuevamente.');
  }
}
```

---

### 2. Obtener Métricas (TypeScript) - Con API Gateway

```typescript
// src/services/analyticsService.ts
import { API_CONFIG } from '../config/api';

interface AnalyticsSummary {
  total_incidents: number;
  by_risk_level: Record<string, number>;
  by_branch: {
    low: number;
    mid: number;
    critical: number;
  };
  by_category: Record<string, number>;
  human_required_count: number;
  p0_signals_count: number;
  nna_involved_count: number;
  last_updated: string;
}

export async function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  // Usar API Gateway (sin CORS issues)
  const response = await fetch(API_CONFIG.gateway.summaryUrl);
  
  if (!response.ok) {
    throw new Error('Failed to fetch analytics summary');
  }
  
  return response.json();
}

export async function getAnalyticsPredictions() {
  // Usar API Gateway (sin CORS issues)
  const response = await fetch(API_CONFIG.gateway.predictionsUrl);
  
  if (!response.ok) {
    throw new Error('Failed to fetch predictions');
  }
  
  return response.json();
}
```

**Alternativa: Directo a api-analytics**

```typescript
export async function getAnalyticsSummaryDirect(): Promise<AnalyticsSummary> {
  const response = await fetch(`${API_CONFIG.analytics.url}/analytics/summary`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch analytics summary');
  }
  
  return response.json();
}
```

**Ejemplo de Uso:**
```typescript
// src/components/Dashboard.tsx
import { useEffect, useState } from 'react';
import { getAnalyticsSummary } from '../services/analyticsService';

export function Dashboard() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await getAnalyticsSummary();
        setSummary(data);
      } catch (error) {
        console.error('Error loading analytics:', error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
    
    // Actualizar cada 30 segundos
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div>Cargando métricas...</div>;
  if (!summary) return <div>Error al cargar datos</div>;

  return (
    <div className="dashboard">
      <h1>Dashboard 911 AI Flow</h1>
      
      <div className="metrics-grid">
        <MetricCard
          title="Total de Incidentes"
          value={summary.total_incidents}
          icon="📊"
        />
        <MetricCard
          title="Atención Humana Requerida"
          value={summary.human_required_count}
          icon="👤"
          variant="warning"
        />
        <MetricCard
          title="Señales P0 Detectadas"
          value={summary.p0_signals_count}
          icon="🚨"
          variant="danger"
        />
        <MetricCard
          title="NNA Involucrados"
          value={summary.nna_involved_count}
          icon="👶"
          variant="info"
        />
      </div>

      <div className="charts">
        <RiskLevelChart data={summary.by_risk_level} />
        <BranchDistribution data={summary.by_branch} />
        <CategoryBreakdown data={summary.by_category} />
      </div>
    </div>
  );
}
```

---

### 3. Polling en Tiempo Real

```typescript
// src/hooks/useRealtimeAnalytics.ts
import { useEffect, useState } from 'react';
import { getAnalyticsSummary } from '../services/analyticsService';

export function useRealtimeAnalytics(intervalMs: number = 10000) {
  const [data, setData] = useState<AnalyticsSummary | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const summary = await getAnalyticsSummary();
        setData(summary);
        setError(null);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
    const interval = setInterval(fetchData, intervalMs);

    return () => clearInterval(interval);
  }, [intervalMs]);

  return { data, error, loading };
}
```

**Uso:**
```typescript
// src/components/LiveDashboard.tsx
import { useRealtimeAnalytics } from '../hooks/useRealtimeAnalytics';

export function LiveDashboard() {
  const { data, error, loading } = useRealtimeAnalytics(10000); // 10 segundos

  if (loading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;
  if (!data) return null;

  return (
    <div>
      <h2>Dashboard en Tiempo Real</h2>
      <p>Última actualización: {new Date(data.last_updated).toLocaleString()}</p>
      {/* Renderizar métricas */}
    </div>
  );
}
```

---

## Componentes UI Sugeridos

### 1. Formulario de Llamada Simulada

```typescript
// src/components/EmergencyCallForm.tsx
import { useState } from 'react';
import { submitEmergencyCall } from '../services/emergencyService';

export function EmergencyCallForm() {
  const [transcript, setTranscript] = useState('');
  const [location, setLocation] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const response = await submitEmergencyCall({
        transcript,
        location_hint: location,
        solid_consent: true,
      });
      setResult(response);
    } catch (error) {
      console.error(error);
      alert('Error al procesar la llamada');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="emergency-form">
      <h2>Simular Llamada 911</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="transcript">Transcripción de la llamada:</label>
          <textarea
            id="transcript"
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Ej: Hay un incendio en mi edificio..."
            rows={5}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="location">Ubicación aproximada:</label>
          <input
            id="location"
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Ej: Colonia Centro"
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Procesando...' : 'Enviar Llamada'}
        </button>
      </form>

      {result && (
        <div className={`result ${result.branch}`}>
          <h3>Resultado del Análisis</h3>
          <div className="result-grid">
            <div>
              <strong>Nivel de Riesgo:</strong> {result.risk_level}/10
            </div>
            <div>
              <strong>Rama:</strong> {result.branch}
            </div>
            <div>
              <strong>Categoría:</strong> {result.case_category}
            </div>
            <div>
              <strong>Atención Humana:</strong> {result.human_required ? '✅ Sí' : '❌ No'}
            </div>
            {result.p0_signals.length > 0 && (
              <div>
                <strong>Señales P0:</strong> {result.p0_signals.join(', ')}
              </div>
            )}
            <div>
              <strong>Autoridad Primaria:</strong> {result.primary_authority}
            </div>
          </div>
          <div className="public-message">
            <p><strong>Mensaje Público:</strong></p>
            <p>{result.public_stage_phrase}</p>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

### 2. Tarjetas de Métricas

```typescript
// src/components/MetricCard.tsx
interface MetricCardProps {
  title: string;
  value: number;
  icon: string;
  variant?: 'default' | 'warning' | 'danger' | 'info';
}

export function MetricCard({ title, value, icon, variant = 'default' }: MetricCardProps) {
  return (
    <div className={`metric-card ${variant}`}>
      <div className="metric-icon">{icon}</div>
      <div className="metric-content">
        <h3>{title}</h3>
        <p className="metric-value">{value.toLocaleString()}</p>
      </div>
    </div>
  );
}
```

---

### 3. Gráfico de Distribución de Riesgo

```typescript
// src/components/RiskLevelChart.tsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

interface RiskLevelChartProps {
  data: Record<string, number>;
}

export function RiskLevelChart({ data }: RiskLevelChartProps) {
  const chartData = Object.entries(data).map(([level, count]) => ({
    level: `Nivel ${level}`,
    count,
  }));

  return (
    <div className="chart-container">
      <h3>Distribución por Nivel de Riesgo</h3>
      <BarChart width={600} height={300} data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="level" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="count" fill="#8884d8" />
      </BarChart>
    </div>
  );
}
```

---

### 4. Tabla de Incidentes Recientes

```typescript
// src/components/RecentIncidents.tsx
import { useEffect, useState } from 'react';

interface Incident {
  incident_id: string;
  call_id: string;
  risk_level: number;
  branch: string;
  case_category: string;
  human_required: boolean;
  timestamp: string;
}

export function RecentIncidents() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadIncidents() {
      try {
        const response = await fetch('http://localhost:8003/incidents?limit=10');
        const data = await response.json();
        setIncidents(data.items);
      } catch (error) {
        console.error('Error loading incidents:', error);
      } finally {
        setLoading(false);
      }
    }

    loadIncidents();
  }, []);

  if (loading) return <div>Cargando incidentes...</div>;

  return (
    <div className="recent-incidents">
      <h3>Incidentes Recientes</h3>
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Riesgo</th>
            <th>Rama</th>
            <th>Categoría</th>
            <th>Atención Humana</th>
          </tr>
        </thead>
        <tbody>
          {incidents.map((incident) => (
            <tr key={incident.incident_id}>
              <td>{new Date(incident.timestamp).toLocaleString()}</td>
              <td className={`risk-${incident.branch}`}>{incident.risk_level}/10</td>
              <td>{incident.branch}</td>
              <td>{incident.case_category}</td>
              <td>{incident.human_required ? '✅' : '❌'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## Manejo de Errores

### 1. Errores de Red

```typescript
// src/utils/errorHandler.ts
export class NetworkError extends Error {
  constructor(message: string, public statusCode?: number) {
    super(message);
    this.name = 'NetworkError';
  }
}

export async function handleApiError(response: Response) {
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new NetworkError(
      error.message || `HTTP ${response.status}: ${response.statusText}`,
      response.status
    );
  }
  return response;
}
```

**Uso:**
```typescript
try {
  const response = await fetch(url);
  await handleApiError(response);
  const data = await response.json();
  // ...
} catch (error) {
  if (error instanceof NetworkError) {
    if (error.statusCode === 401) {
      alert('Credenciales incorrectas');
    } else if (error.statusCode === 500) {
      alert('Error del servidor. Intente más tarde.');
    }
  }
}
```

---

### 2. Timeout

```typescript
// src/utils/fetchWithTimeout.ts
export async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeoutMs: number = 10000
): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timeout);
  }
}
```

---

## CORS y Seguridad

### Configuración CORS en FastAPI

Los servicios ya incluyen CORS habilitado para `localhost`:

```python
# services/api-analytics/app.py (ejemplo)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Consideraciones de Seguridad

**✅ Buenas Prácticas:**
- Usar variables de entorno para URLs y credenciales
- No hardcodear contraseñas en el código
- Validar inputs del usuario antes de enviar
- Mostrar advertencias de privacidad

**❌ Evitar:**
- Exponer credenciales en el frontend
- Enviar PII real en modo demo
- Hacer requests sin timeout
- Ignorar errores de red

---

## Modo Demo

### Advertencia de Privacidad

```typescript
// src/components/PrivacyWarning.tsx
import { API_CONFIG } from '../config/api';

export function PrivacyWarning() {
  if (!API_CONFIG.showPrivacyWarnings) return null;

  return (
    <div className="privacy-warning">
      <h3>⚠️ Advertencia de Privacidad</h3>
      <ul>
        <li>Este es un sistema de <strong>demostración educativa</strong></li>
        <li><strong>NO enviar datos personales reales</strong></li>
        <li><strong>NO usar para emergencias reales</strong></li>
        <li>Todos los datos son sintéticos y con fines educativos</li>
        <li>El sistema redacta automáticamente PII, pero es mejor no enviarlo</li>
      </ul>
    </div>
  );
}
```

---

### Datos de Prueba Predefinidos

```typescript
// src/data/testCases.ts
export const TEST_CASES = [
  {
    id: 'low-risk',
    name: 'Bajo Riesgo - Bache',
    transcript: 'Hay un bache grande en la calle principal de mi colonia',
    location: 'Colonia Centro',
    expectedRisk: 3,
  },
  {
    id: 'mid-risk',
    name: 'Riesgo Medio - Accidente de Tránsito',
    transcript: 'Hubo un choque entre dos autos, hay tráfico pero nadie herido',
    location: 'Avenida Insurgentes',
    expectedRisk: 5,
  },
  {
    id: 'critical-p0',
    name: 'Crítico P0 - Incendio',
    transcript: 'Hay un incendio en mi edificio, necesito ayuda urgente',
    location: 'Colonia Roma',
    expectedRisk: 8,
  },
];
```

**Uso:**
```typescript
// src/components/QuickTestButtons.tsx
import { TEST_CASES } from '../data/testCases';
import { submitEmergencyCall } from '../services/emergencyService';

export function QuickTestButtons() {
  const handleTest = async (testCase: typeof TEST_CASES[0]) => {
    const result = await submitEmergencyCall({
      transcript: testCase.transcript,
      location_hint: testCase.location,
      solid_consent: true,
    });
    console.log('Test result:', result);
  };

  return (
    <div className="quick-tests">
      <h3>Pruebas Rápidas</h3>
      {TEST_CASES.map((testCase) => (
        <button key={testCase.id} onClick={() => handleTest(testCase)}>
          {testCase.name}
        </button>
      ))}
    </div>
  );
}
```

---

## Checklist de Integración

### Antes de Empezar

- [ ] Backend corriendo (`docker compose up -d`)
- [ ] Todos los servicios healthy (`./scripts/04_test_environment.sh`)
- [ ] n8n accesible en `localhost:5678`
- [ ] Workflow importado en n8n

### Configuración

- [ ] Archivo `.env` creado con variables correctas
- [ ] CORS habilitado en servicios
- [ ] Credenciales Basic Auth configuradas

### Desarrollo

- [ ] Servicio de API creado (`emergencyService.ts`, `analyticsService.ts`)
- [ ] Componentes UI implementados
- [ ] Manejo de errores implementado
- [ ] Advertencias de privacidad visibles

### Pruebas

- [ ] Formulario envía llamadas correctamente
- [ ] Dashboard muestra métricas en tiempo real
- [ ] Errores se manejan apropiadamente
- [ ] Casos de prueba funcionan (bajo, medio, crítico)

---

## Recursos Adicionales

### Documentación Relacionada

- `docs/api_contract.md` - Especificación completa de APIs
- `docs/architecture.md` - Arquitectura del sistema
- `README.md` - Guía de instalación y uso

### Ejemplos de Código

Ver carpeta `scripts/` para ejemplos de curl:
- `scripts/04_test_environment.sh` - Pruebas de endpoints
- `scripts/06_test_n8n_webhook.sh` - Pruebas de webhook

---

**Versión:** 1.0.0  
**Fecha:** 2026-06-06  
**Autor:** Bob  
**Propósito:** Demo educativa - Hackathon