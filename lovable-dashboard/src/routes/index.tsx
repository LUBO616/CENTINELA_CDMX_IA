import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
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
} from "lucide-react";
import { StatCard } from "@/components/stat-card";
import { fetchSummary, fetchPredictions, fetchJudgeMetrics } from "@/lib/centinela-api";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Dashboard · CENTINELA CDMX IA" },
      { name: "description", content: "Resumen de incidentes simulados y predicción mock." },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  const summaryQ = useQuery({
    queryKey: ["summary"],
    queryFn: fetchSummary,
    refetchInterval: 15000,
  });
  const predQ = useQuery({
    queryKey: ["predictions"],
    queryFn: fetchPredictions,
    refetchInterval: 30000,
  });
  const judgeQ = useQuery({
    queryKey: ["judgeMetrics"],
    queryFn: fetchJudgeMetrics,
    refetchInterval: 60000,
    retry: false,
  });

  const s = summaryQ.data?.data;
  const p = predQ.data?.data;
  const j = judgeQ.data;
  const summaryMock = summaryQ.data?.isMock;
  const predMock = predQ.data?.isMock;

  return (
    <div className="space-y-8">
      <header>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">
              Panel de operaciones
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Estado consolidado de incidentes clasificados por IA determinista.
            </p>
          </div>
          {(summaryMock || predMock) && (
            <span className="inline-flex items-center gap-2 rounded-full border border-risk-mid/40 bg-risk-mid/10 px-3 py-1 text-xs text-risk-mid">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-risk-mid" />
              Modo demo local — analytics no disponible
            </span>
          )}
        </div>
      </header>

      <section>
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          Incidentes
        </h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
          <StatCard
            label="Total"
            value={s ? Number(s.total_incidents ?? 0).toLocaleString() : "—"}
            icon={<Activity className="h-5 w-5" />}
            tone="primary"
          />
          <StatCard
            label="Bajo"
            value={s ? Number(s.by_branch?.low ?? 0).toLocaleString() : "—"}
            icon={<ShieldCheck className="h-5 w-5" />}
            tone="low"
          />
          <StatCard
            label="Medio"
            value={s ? Number(s.by_branch?.mid ?? 0).toLocaleString() : "—"}
            icon={<AlertTriangle className="h-5 w-5" />}
            tone="mid"
          />
          <StatCard
            label="Crítico"
            value={s ? Number(s.by_branch?.critical ?? 0).toLocaleString() : "—"}
            icon={<Flame className="h-5 w-5" />}
            tone="critical"
          />
          <StatCard
            label="Requiere humano"
            value={s ? Number(s.human_required_count ?? 0).toLocaleString() : "—"}
            icon={<UserCog className="h-5 w-5" />}
            tone="analytics"
          />
          <StatCard
            label="Señales P0"
            value={s ? Number(s.p0_signals_count ?? 0).toLocaleString() : "—"}
            icon={<Siren className="h-5 w-5" />}
            tone="critical"
          />
        </div>
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Predicción
          </h2>
          <span className="text-[10px] uppercase tracking-wider text-analytics">
            Mock con datos sintéticos
          </span>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <div className="rounded-xl border border-analytics/30 bg-card p-5 ring-1 ring-analytics/20">
            <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
              Llamadas estimadas (24h)
            </div>
            <div className="mt-3 flex items-baseline gap-3">
              <div className="font-mono text-4xl font-bold text-analytics tabular-nums">
                {p?.estimated_calls ?? "—"}
              </div>
              <TrendBadge trend={p?.trend} />
            </div>
            <p className="mt-3 text-xs text-muted-foreground">
              Predicción mock con datos sintéticos. No representa flujo real.
            </p>
          </div>

          <div className="rounded-xl border border-border bg-card p-5">
            <div className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
              Distribución por categoría
            </div>
            <div className="space-y-2.5">
              {p
                ? Object.entries(p.category_distribution).map(([k, v]) => {
                    const max = Math.max(...Object.values(p.category_distribution));
                    const pct = max ? (v / max) * 100 : 0;
                    return (
                      <div key={k}>
                        <div className="mb-1 flex justify-between text-xs">
                          <span className="text-foreground">{k}</span>
                          <span className="font-mono text-muted-foreground">{v}</span>
                        </div>
                        <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                          <div
                            className="h-full rounded-full bg-analytics"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })
                : <Skeleton rows={5} />}
            </div>
          </div>

          <div className="rounded-xl border border-border bg-card p-5">
            <div className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
              Zonas de riesgo (normalizadas)
            </div>
            <ul className="space-y-2.5">
              {p
                ? p.risk_zones.map((z, idx) => (
                    <li key={idx} className="flex items-center gap-3">
                      <MapPin className="h-4 w-4 shrink-0 text-muted-foreground" />
                      <div className="flex-1">
                        <div className="flex justify-between text-xs">
                          <span>{z.zone}</span>
                          <span className="font-mono text-muted-foreground">
                            {Number(((z as any).risk_score ?? (z as any).score ?? 0)).toFixed(2)}
                          </span>
                        </div>
                        <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-muted">
                          <div
                            className={[
                              "h-full rounded-full",
                              Number(((z as any).risk_score ?? (z as any).score ?? 0)) >= 7
                                ? "bg-risk-critical"
                                : Number(((z as any).risk_score ?? (z as any).score ?? 0)) >= 4
                                  ? "bg-risk-mid"
                                  : "bg-risk-low",
                            ].join(" ")}
                            style={{ width: `${Math.min(100, Number(((z as any).risk_score ?? (z as any).score ?? 0)) * 10)}%` }}
                          />
                        </div>
                      </div>
                    </li>
                  ))
                : <Skeleton rows={5} />}
            </ul>
          </div>
        </div>
      </section>

      {/* Judge Metrics Section */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Métricas para jueces / Equidad territorial
          </h2>
        </div>
        <p className="mb-4 text-xs text-muted-foreground italic">
          Datos geoespaciales sintéticos para demo. No representan límites oficiales ni incidentes reales.
        </p>

        {j?.status === "not_generated" ? (
          <div className="rounded-xl border border-risk-mid/40 bg-risk-mid/10 p-5">
            <div className="flex items-center gap-2 text-risk-mid">
              <AlertTriangle className="h-5 w-5" />
              <h3 className="font-semibold">Métricas no generadas</h3>
            </div>
            <p className="mt-2 text-sm text-risk-mid/90">
              {j?.message || "Ejecuta ./scripts/08_setup_postgis_demo.sh para generar las métricas PostGIS."}
            </p>
          </div>
        ) : judgeQ.isError ? (
          <div className="rounded-xl border border-destructive/40 bg-destructive/10 p-5">
            <div className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              <h3 className="font-semibold">Error al cargar métricas</h3>
            </div>
            <p className="mt-2 text-sm text-destructive/90">
              No se pudieron cargar las métricas de jueces. Verifica que el backend esté activo.
            </p>
          </div>
        ) : j?.metrics ? (
          <>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <StatCard
                label="Gini territorial"
                value={j.metrics.gini_risk_norm.value.toFixed(2)}
                hint={`Umbral: ≤${j.metrics.gini_risk_norm.threshold}`}
                icon={<Scale className="h-5 w-5" />}
                tone={j.metrics.gini_risk_norm.pass ? "low" : "mid"}
              />
              <StatCard
                label="Recall P0"
                value={`${(j.metrics.recall_p0_detection_rate.value * 100).toFixed(1)}%`}
                hint={`Umbral: ≥${(j.metrics.recall_p0_detection_rate.threshold * 100).toFixed(0)}%`}
                icon={<Target className="h-5 w-5" />}
                tone={j.metrics.recall_p0_detection_rate.pass ? "low" : "critical"}
              />
              <StatCard
                label="Horas liberadas/día"
                value={j.metrics.operator_hours_freed_per_day.value.toFixed(1)}
                hint={`Umbral: ≥${j.metrics.operator_hours_freed_per_day.threshold}h`}
                icon={<Clock className="h-5 w-5" />}
                tone={j.metrics.operator_hours_freed_per_day.pass ? "analytics" : "mid"}
              />
              <StatCard
                label="Correlación acceso digital"
                value={Math.abs(j.metrics.coverage_bias_correlation_after.value).toFixed(2)}
                hint={`Umbral: ≤${j.metrics.coverage_bias_correlation_after.threshold}`}
                icon={<CorrelationIcon className="h-5 w-5" />}
                tone={j.metrics.coverage_bias_correlation_after.pass ? "low" : "mid"}
              />
            </div>

            {j.by_alcaldia && j.by_alcaldia.length > 0 && (
              <div className="mt-6 rounded-xl border border-border bg-card p-5">
                <h3 className="mb-4 text-sm font-semibold">Distribución por alcaldía</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-muted-foreground">
                        <th className="pb-2 pr-4">Alcaldía</th>
                        <th className="pb-2 pr-4 text-right">Incidentes</th>
                        <th className="pb-2 pr-4 text-right">Riesgo prom.</th>
                        <th className="pb-2 pr-4 text-right">P0</th>
                        <th className="pb-2 pr-4 text-right">Acceso digital</th>
                        <th className="pb-2 text-right">Percentil</th>
                      </tr>
                    </thead>
                    <tbody>
                      {j.by_alcaldia.map((item) => (
                        <tr key={item.alcaldia_norm} className="border-b border-border/50 last:border-0">
                          <td className="py-2 pr-4 font-medium">{item.alcaldia}</td>
                          <td className="py-2 pr-4 text-right font-mono">{item.incident_count}</td>
                          <td className="py-2 pr-4 text-right font-mono">{item.avg_risk.toFixed(1)}</td>
                          <td className="py-2 pr-4 text-right font-mono">{item.p0_count}</td>
                          <td className="py-2 pr-4 text-right font-mono">{item.digital_access_index.toFixed(2)}</td>
                          <td className="py-2 text-right font-mono text-muted-foreground">{item.percentile}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="grid h-32 place-items-center rounded-xl border border-dashed border-border bg-card/50">
            <p className="text-sm text-muted-foreground">Cargando métricas de jueces...</p>
          </div>
        )}
      </section>
    </div>
  );


}

function TrendBadge({ trend }: { trend?: string }) {
  if (!trend) return null;
  const map: Record<string, { icon: typeof TrendingUp; cls: string; label: string }> = {
    up: { icon: TrendingUp, cls: "text-risk-critical bg-risk-critical/10 border-risk-critical/30", label: "Al alza" },
    down: { icon: TrendingDown, cls: "text-risk-low bg-risk-low/10 border-risk-low/30", label: "A la baja" },
    stable: { icon: Minus, cls: "text-muted-foreground bg-muted/40 border-border", label: "Estable" },
  };
  const cfg = map[trend] ?? map.stable;
  const Icon = cfg.icon;
  return (
    <span
      className={["inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs", cfg.cls].join(" ")}
    >
      <Icon className="h-3 w-3" />
      {cfg.label}
    </span>
  );
}

function Skeleton({ rows }: { rows: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-3 animate-pulse rounded bg-muted/60" />
      ))}
    </div>
  );
}
