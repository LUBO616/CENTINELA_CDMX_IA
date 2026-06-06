# Patch para agregar sección "Actividad reciente" al dashboard principal

## Instrucciones

Aplicar los siguientes cambios a `lovable-dashboard/src/routes/index.tsx`:

### 1. Actualizar imports (líneas 1-22)

Agregar estos imports adicionales:

```typescript
import {
  Activity,
  AlertTriangle,
  Flame,
  ShieldCheck,
  UserCog,
  Siren,
  TrendingUp,
  TrendingDown,
  Minus,
  MapPin,
  Scale,
  Target,
  Clock,
  TrendingDown as CorrelationIcon,
  Printer,           // NUEVO
  Phone,             // NUEVO
  MessageSquare,     // NUEVO
  MapPinned,         // NUEVO
} from "lucide-react";
import { Button } from "@/components/ui/button";  // NUEVO
import { StatCard } from "@/components/stat-card";
import { Badge } from "@/components/ui/badge";     // NUEVO
import { fetchSummary, fetchPredictions, fetchJudgeMetrics, fetchRecentActivity } from "@/lib/centinela-api";  // Agregar fetchRecentActivity
```

### 2. Agregar query para actividad reciente (después de línea 46)

```typescript
  const activityQ = useQuery({
    queryKey: ["recentActivity"],
    queryFn: () => fetchRecentActivity(10),
    refetchInterval: 5000,
    retry: false,
  });
```

### 3. Agregar variable activity (después de línea 54)

```typescript
  const activity = activityQ.data;
```

### 4. Agregar botón "Exportar PDF" (después de línea 67, dentro del header)

```typescript
          <Button variant="outline" size="sm" onClick={() => window.print()} className="print:hidden">
            <Printer className="h-4 w-4 mr-2" />
            Exportar PDF
          </Button>
```

### 5. Agregar sección completa "Actividad reciente"

**UBICACIÓN**: Después de `</section>` de la sección "Predicción" (aproximadamente línea 225), ANTES de la sección "Métricas para jueces".

Insertar el siguiente código completo:

```typescript
      {/* Recent Activity Section */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Actividad reciente: llamadas y mensajes
          </h2>
          <span className="text-[10px] uppercase tracking-wider text-analytics">
            Actualización cada 5 segundos
          </span>
        </div>

        {/* Summary Cards */}
        <div className="mb-4 grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-6">
          <StatCard
            label="Total 24h"
            value={activity?.summary?.total_recent?.toLocaleString() ?? "—"}
            icon={<Activity className="h-5 w-5" />}
            tone="primary"
          />
          <StatCard
            label="Llamadas 24h"
            value={activity?.summary?.calls_24h?.toLocaleString() ?? "—"}
            icon={<Phone className="h-5 w-5" />}
            tone="analytics"
          />
          <StatCard
            label="Mensajes 24h"
            value={activity?.summary?.messages_24h?.toLocaleString() ?? "—"}
            icon={<MessageSquare className="h-5 w-5" />}
            tone="analytics"
          />
          <StatCard
            label="Críticos 24h"
            value={activity?.summary?.critical_recent?.toLocaleString() ?? "—"}
            icon={<Flame className="h-5 w-5" />}
            tone="critical"
          />
          <StatCard
            label="Requieren humano"
            value={activity?.summary?.human_required_recent?.toLocaleString() ?? "—"}
            icon={<UserCog className="h-5 w-5" />}
            tone="mid"
          />
          <StatCard
            label="Señales P0"
            value={activity?.summary?.p0_recent?.toLocaleString() ?? "—"}
            icon={<Siren className="h-5 w-5" />}
            tone="critical"
          />
        </div>

        {/* Two columns: Calls and Messages */}
        <div className="grid gap-4 lg:grid-cols-2">
          {/* Recent 911 Calls */}
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <Phone className="h-4 w-4" />
                Llamadas 911 recientes
              </h3>
              <span className="text-xs text-muted-foreground">
                {activity?.calls?.length ?? 0} registros
              </span>
            </div>
            
            {activity?.calls && activity.calls.length > 0 ? (
              <div className="space-y-3">
                {activity.calls.slice(0, 5).map((call, idx) => (
                  <div key={call.call_id || idx} className="rounded-lg border border-border/50 bg-muted/30 p-3">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex-1">
                        <div className="text-xs text-muted-foreground mb-1">
                          {call.timestamp ? new Date(call.timestamp).toLocaleString("es-MX", {
                            month: "short",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit"
                          }) : "—"}
                        </div>
                        <div className="text-sm line-clamp-2">
                          {call.transcript || "Sin transcripción"}
                        </div>
                      </div>
                      <div className="flex flex-col gap-1">
                        {call.branch && (
                          <Badge variant={
                            call.branch === "critical" ? "destructive" :
                            call.branch === "mid" ? "default" : "secondary"
                          } className="text-[10px]">
                            {call.branch}
                          </Badge>
                        )}
                        {call.human_required && (
                          <Badge variant="outline" className="text-[10px]">
                            <UserCog className="h-3 w-3 mr-1" />
                            Humano
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2 text-xs">
                      {call.category && (
                        <span className="text-muted-foreground">
                          📋 {call.category}
                        </span>
                      )}
                      {call.risk_level && (
                        <span className="text-muted-foreground">
                          ⚠️ Riesgo: {call.risk_level}
                        </span>
                      )}
                      {call.p0_signals && call.p0_signals.length > 0 && (
                        <span className="text-risk-critical font-semibold">
                          🚨 P0: {call.p0_signals.join(", ")}
                        </span>
                      )}
                      {call.location_hint && (
                        <span className="text-muted-foreground">
                          📍 {call.location_hint}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-8 text-center text-sm text-muted-foreground">
                No hay llamadas recientes
              </div>
            )}
          </div>

          {/* Recent WhatsApp Messages */}
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                Mensajes WhatsApp Lab recientes
              </h3>
              <span className="text-xs text-muted-foreground">
                {activity?.messages?.length ?? 0} registros
              </span>
            </div>
            
            {activity?.messages && activity.messages.length > 0 ? (
              <div className="space-y-3">
                {activity.messages.slice(0, 5).map((msg, idx) => (
                  <div key={msg.message_id || idx} className="rounded-lg border border-border/50 bg-muted/30 p-3">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                          <span>
                            {msg.incident_time ? new Date(msg.incident_time).toLocaleString("es-MX", {
                              month: "short",
                              day: "numeric",
                              hour: "2-digit",
                              minute: "2-digit"
                            }) : "—"}
                          </span>
                          {msg.from_number_redacted && (
                            <span className="font-mono">
                              📱 {msg.from_number_redacted}
                            </span>
                          )}
                        </div>
                        <div className="text-sm line-clamp-2">
                          {msg.message_text}
                        </div>
                      </div>
                      <div className="flex flex-col gap-1">
                        {msg.branch && (
                          <Badge variant={
                            msg.branch === "critical" ? "destructive" :
                            msg.branch === "mid" ? "default" : "secondary"
                          } className="text-[10px]">
                            {msg.branch}
                          </Badge>
                        )}
                        {msg.human_required && (
                          <Badge variant="outline" className="text-[10px]">
                            <UserCog className="h-3 w-3 mr-1" />
                            Humano
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2 text-xs">
                      {msg.location_hint && (
                        <span className="flex items-center gap-1">
                          <MapPinned className="h-3 w-3" />
                          {msg.location_hint}
                          {msg.location_source && (
                            <Badge variant="outline" className="text-[9px] ml-1">
                              {msg.location_source === "user_text" ? "Reportada" : "Geoloc 911"}
                            </Badge>
                          )}
                        </span>
                      )}
                      {msg.alcaldia_norm && (
                        <span className="text-muted-foreground">
                          🏛️ {msg.alcaldia_norm.replace(/_/g, " ")}
                        </span>
                      )}
                      {msg.category && (
                        <span className="text-muted-foreground">
                          📋 {msg.category}
                        </span>
                      )}
                      {msg.risk_level && (
                        <span className="text-muted-foreground">
                          ⚠️ Riesgo: {msg.risk_level}
                        </span>
                      )}
                      {msg.p0_signals && msg.p0_signals.length > 0 && (
                        <span className="text-risk-critical font-semibold">
                          🚨 P0: {msg.p0_signals.join(", ")}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-8 text-center text-sm text-muted-foreground">
                No hay mensajes recientes
              </div>
            )}
          </div>
        </div>
      </section>
```

## Verificación

Después de aplicar los cambios:

1. `npm run build` debe pasar sin errores
2. El dashboard principal debe mostrar la nueva sección "Actividad reciente"
3. La sección debe actualizarse cada 5 segundos
4. Debe mostrar llamadas 911 y mensajes WhatsApp Lab recientes
5. El botón "Exportar PDF" debe funcionar

## Archivos ya completados

✅ `services/api-analytics/app.py` - Endpoint `/activity/recent` creado
✅ `services/api-gateway/app.py` - Proxy agregado
✅ `lovable-dashboard/src/lib/centinela-api.ts` - Tipos y función `fetchRecentActivity()` agregados