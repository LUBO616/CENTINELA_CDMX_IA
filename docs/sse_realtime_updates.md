# Server-Sent Events (SSE) - Real-time Updates

## Objetivo

Implementar actualizaciones en tiempo real para el dashboard predictivo usando PostgreSQL NOTIFY/LISTEN y Server-Sent Events (SSE).

## Arquitectura

```
PostgreSQL Database
    ↓ (INSERT/UPDATE/DELETE trigger)
NOTIFY 'predictive_updates'
    ↓ (LISTEN)
api-analytics SSE endpoint
    ↓ (EventSource)
Frontend Dashboard
    ↓ (refetch queries)
Updated UI
```

## Componentes

### 1. PostgreSQL Triggers

**Ubicación:** `database/init.sql`

**Función de notificación:**
```sql
CREATE OR REPLACE FUNCTION notify_predictive_change()
RETURNS TRIGGER AS $$
DECLARE
    payload JSON;
BEGIN
    IF TG_OP = 'DELETE' THEN
        payload = json_build_object(
            'operation', TG_OP,
            'table', TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME,
            'incident_id', OLD.incident_id,
            'created_at', OLD.created_at,
            'timestamp', NOW()
        );
    ELSE
        payload = json_build_object(
            'operation', TG_OP,
            'table', TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME,
            'incident_id', NEW.incident_id,
            'branch', NEW.branch,
            'risk_level', NEW.risk_level,
            'case_category', NEW.case_category,
            'created_at', NEW.created_at,
            'timestamp', NOW()
        );
    END IF;
    
    PERFORM pg_notify('predictive_updates', payload::text);
    
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;
```

**Triggers:**
```sql
CREATE TRIGGER notify_predictive_insert
    AFTER INSERT ON analytics.predictive_incidents
    FOR EACH ROW
    EXECUTE FUNCTION notify_predictive_change();

CREATE TRIGGER notify_predictive_update
    AFTER UPDATE ON analytics.predictive_incidents
    FOR EACH ROW
    EXECUTE FUNCTION notify_predictive_change();

CREATE TRIGGER notify_predictive_delete
    AFTER DELETE ON analytics.predictive_incidents
    FOR EACH ROW
    EXECUTE FUNCTION notify_predictive_change();
```

### 2. Backend SSE Endpoint

**Ubicación:** `services/api-analytics/app.py`

**Endpoint:** `GET /predictive/events`

**Implementación:**
```python
@app.get("/predictive/events")
async def predictive_events_sse():
    """Server-Sent Events endpoint for real-time predictive updates"""
    from fastapi.responses import StreamingResponse
    import asyncio
    import select
    
    async def event_generator():
        conn = None
        try:
            # Connect to database
            conn = get_db_connection()
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Listen to predictive_updates channel
            cursor.execute("LISTEN predictive_updates;")
            
            # Send initial connection event
            yield f"event: connected\ndata: {json.dumps({'status': 'connected'})}\n\n"
            
            while True:
                # Check for notifications with timeout
                if select.select([conn], [], [], 15.0) == ([], [], []):
                    # Timeout - send heartbeat
                    yield f"event: heartbeat\ndata: {json.dumps({'timestamp': datetime.utcnow().isoformat()})}\n\n"
                else:
                    # Process notifications
                    conn.poll()
                    while conn.notifies:
                        notify = conn.notifies.pop(0)
                        payload = json.loads(notify.payload)
                        
                        # Send event to client
                        yield f"event: predictive_update\ndata: {json.dumps(payload)}\n\n"
                
                await asyncio.sleep(0.1)
                
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        finally:
            if conn:
                cursor.execute("UNLISTEN predictive_updates;")
                cursor.close()
                conn.close()
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

### 3. Gateway Proxy

**Ubicación:** `services/api-gateway/app.py`

**Endpoint:** `GET /predictive/events`

**Implementación:**
```python
@app.get("/predictive/events")
async def predictive_events_sse():
    """Proxy SSE for predictive events"""
    from starlette.responses import StreamingResponse
    
    async def event_stream():
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", f"{ANALYTICS_BASE_URL}/predictive/events") as response:
                    async for chunk in response.aiter_bytes():
                        yield chunk
        except Exception as e:
            yield f"event: error\ndata: {{'error': '{str(e)}'}}\n\n".encode()
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

### 4. Frontend Client

**Ubicación:** `lovable-dashboard/src/lib/centinela-api.ts`

**Función de suscripción:**
```typescript
export function subscribePredictiveEvents(
  onEvent: (event: PredictiveEvent) => void,
  onError?: (error: Error) => void
): EventSource {
  const eventSource = new EventSource(`${PREDICTIVE_BASE_URL}/events`);

  eventSource.addEventListener("predictive_update", (e) => {
    try {
      const data = JSON.parse(e.data) as PredictiveEvent;
      onEvent(data);
    } catch (err) {
      console.error("Error parsing SSE event:", err);
      onError?.(err as Error);
    }
  });

  eventSource.addEventListener("connected", (e) => {
    console.log("SSE connected:", e.data);
  });

  eventSource.addEventListener("heartbeat", (e) => {
    console.debug("SSE heartbeat:", e.data);
  });

  eventSource.onerror = (err) => {
    console.error("SSE onerror:", err);
    onError?.(new Error("SSE connection failed"));
  };

  return eventSource;
}
```

**Uso en Dashboard:**
```typescript
useEffect(() => {
  let eventSource: EventSource | null = null;

  try {
    eventSource = subscribePredictiveEvents(
      (event) => {
        setLastEvent(event);
        setEventCount((prev) => prev + 1);
        
        // Invalidate queries on update
        if (event.operation === "INSERT" || event.operation === "UPDATE") {
          overviewQuery.refetch();
          hourlyQuery.refetch();
          categoriesQuery.refetch();
        }
      },
      (error) => {
        console.error("SSE error:", error);
        setIsLive(false);
      }
    );
  } catch (error) {
    console.error("Failed to connect SSE:", error);
  }

  return () => {
    if (eventSource) {
      eventSource.close();
    }
  };
}, []);
```

## Tipos de Eventos

### 1. connected
Enviado cuando el cliente se conecta exitosamente.

```json
{
  "status": "connected",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2. predictive_update
Enviado cuando hay INSERT, UPDATE o DELETE en la tabla.

**INSERT/UPDATE:**
```json
{
  "operation": "INSERT",
  "table": "analytics.predictive_incidents",
  "incident_id": "PRED-ABC123",
  "branch": "critical",
  "risk_level": 8,
  "case_category": "protection_civil",
  "created_at": "2024-01-15T10:30:00Z",
  "timestamp": "2024-01-15T10:30:01Z"
}
```

**DELETE:**
```json
{
  "operation": "DELETE",
  "table": "analytics.predictive_incidents",
  "incident_id": "PRED-XYZ789",
  "created_at": "2024-01-15T09:00:00Z",
  "timestamp": "2024-01-15T10:30:01Z"
}
```

### 3. heartbeat
Enviado cada 15 segundos para mantener la conexión viva.

```json
{
  "count": 42,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 4. error
Enviado cuando hay un error en el servidor.

```json
{
  "error": "Database connection lost"
}
```

## Formato SSE

Server-Sent Events usa formato de texto plano:

```
event: predictive_update
data: {"operation":"INSERT","incident_id":"PRED-123"}

event: heartbeat
data: {"timestamp":"2024-01-15T10:30:00Z"}

```

**Reglas:**
- Cada evento termina con doble salto de línea (`\n\n`)
- `event:` especifica el tipo de evento
- `data:` contiene el payload JSON
- Múltiples líneas `data:` se concatenan

## Ventajas de SSE

1. **Unidireccional:** Servidor → Cliente (suficiente para notificaciones)
2. **HTTP/1.1:** No requiere WebSocket
3. **Reconexión automática:** El navegador reconecta automáticamente
4. **Eventos tipados:** Permite múltiples tipos de eventos
5. **Texto plano:** Fácil de debuggear

## Limitaciones

1. **Solo servidor → cliente:** No bidireccional (usar WebSocket si se necesita)
2. **Límite de conexiones:** Navegadores limitan conexiones SSE por dominio (6-8)
3. **No binario:** Solo texto (JSON)
4. **Buffering:** Algunos proxies pueden bufferear (usar `X-Accel-Buffering: no`)

## Fallback

Si SSE no funciona o es complejo:

**Opción 1: Polling con React Query**
```typescript
const overviewQuery = useQuery({
  queryKey: ["predictive-overview"],
  queryFn: fetchPredictiveOverview,
  refetchInterval: 3000, // Poll every 3 seconds
});
```

**Opción 2: Conexión directa**
Frontend puede conectarse directamente a `http://localhost:8003/predictive/events` si el gateway tiene problemas con streaming.

## Testing

### Manual con curl

```bash
# Connect to SSE endpoint
curl -N http://localhost:8010/predictive/events

# In another terminal, insert data to trigger event
docker exec centinela-postgres psql -U centinela_user -d centinela_db -c \
  "INSERT INTO analytics.predictive_incidents (incident_id, branch, risk_level, case_category, human_required, alcaldia_norm, synthetic) 
   VALUES ('TEST-SSE-001', 'critical', 9, 'security', true, 'cuauhtemoc', true);"
```

### Browser DevTools

1. Abrir dashboard: `http://127.0.0.1:5173/predictivo`
2. Abrir DevTools → Network
3. Filtrar por `predictive/events`
4. Ver eventos en tiempo real
5. Insertar datos en DB para ver actualizaciones

### Logs

**Backend:**
```
SSE: Listening to predictive_updates channel
SSE: Received notification - INSERT on PRED-ABC123
```

**Frontend:**
```
SSE connected: {"status":"connected"}
SSE heartbeat: {"count":1}
Received event: INSERT PRED-ABC123
```

## Troubleshooting

### Problema: No se reciben eventos

**Solución:**
1. Verificar que triggers estén creados: `\d+ analytics.predictive_incidents`
2. Verificar que función existe: `\df notify_predictive_change`
3. Verificar logs de api-analytics
4. Probar inserción manual en DB

### Problema: Conexión se cierra

**Solución:**
1. Verificar heartbeat (debe enviarse cada 15s)
2. Verificar que no haya proxy buffering
3. Aumentar timeout en nginx/proxy si aplica
4. Verificar logs de errores

### Problema: Eventos duplicados

**Solución:**
1. Verificar que no haya múltiples triggers
2. Verificar que EventSource no se cree múltiples veces
3. Usar cleanup en useEffect

### Problema: CORS en SSE

**Solución:**
1. Verificar headers CORS en gateway
2. Agregar `Access-Control-Allow-Origin`
3. Verificar que OPTIONS preflight funcione

## Seguridad

### Consideraciones

1. **Autenticación:** Agregar token en query string o header
2. **Rate limiting:** Limitar conexiones por IP
3. **Validación:** Validar payload antes de enviar
4. **Sanitización:** No enviar PII en eventos
5. **Timeout:** Cerrar conexiones inactivas

### Ejemplo con Auth

```typescript
const eventSource = new EventSource(
  `${PREDICTIVE_BASE_URL}/events?token=${authToken}`
);
```

## Performance

### Optimizaciones

1. **Batch notifications:** Agrupar múltiples cambios
2. **Debounce:** No enviar eventos muy frecuentes
3. **Selective updates:** Solo enviar campos cambiados
4. **Connection pooling:** Reusar conexiones DB

### Métricas

- Conexiones SSE activas
- Eventos enviados por segundo
- Latencia de notificación
- Tasa de reconexión

## Referencias

- [MDN: Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [PostgreSQL NOTIFY/LISTEN](https://www.postgresql.org/docs/current/sql-notify.html)
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [EventSource API](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)

---

**Nota:** SSE es ideal para notificaciones unidireccionales. Para chat bidireccional, considerar WebSocket.