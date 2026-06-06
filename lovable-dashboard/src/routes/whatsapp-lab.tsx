import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  Activity,
  AlertTriangle,
  Bot,
  Clock,
  MapPin,
  MessageSquare,
  Phone,
  Printer,
  Send,
  ShieldAlert,
  User,
} from "lucide-react";

export const Route = createFileRoute("/whatsapp-lab")({
  component: WhatsAppLabDashboard,
});

type WhatsAppLabMessage = {
  message_id: string;
  from_hash?: string;
  from_number_redacted?: string;
  profile_name?: string;
  message_text?: string;
  message_text_redacted?: string;
  location_hint?: string;
  location_source?: string;
  incident_time?: string;
  alcaldia_norm?: string;
  latitude?: number;
  longitude?: number;
  category?: string;
  branch?: string;
  risk_level?: number;
  human_required?: boolean;
  p0_signals?: string[];
  bot_reply?: string;
  source?: string;
  created_at?: string;
  processed_at?: string;
};

type WhatsAppLabSummary = {
  total_messages?: number;
  last_24h?: number;
  by_branch?: Record<string, number>;
  by_category?: Record<string, number>;
  human_required_count?: number;
  p0_count?: number;
  generated_at?: string;
};

const API_BASE = "http://localhost:8010";

const EXAMPLES = [
  "Hay un incendio en colonia Centro, Cuauhtémoc",
  "Hay una persona herida inconsciente",
  "Hay un bache enorme en Reforma",
  "Me están robando con un arma en Iztapalapa",
  "Escucho violencia familiar en el departamento de al lado",
];

function normalizeRecentPayload(payload: any): WhatsAppLabMessage[] {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.messages)) return payload.messages;
  if (Array.isArray(payload?.data)) return payload.data;
  return [];
}

function branchLabel(branch?: string) {
  if (branch === "critical") return "Crítica";
  if (branch === "mid") return "Media";
  if (branch === "low") return "Baja";
  return "Sin clasificar";
}

function branchClass(branch?: string) {
  if (branch === "critical") return "border-red-500/40 bg-red-500/10 text-red-300";
  if (branch === "mid") return "border-yellow-500/40 bg-yellow-500/10 text-yellow-300";
  if (branch === "low") return "border-green-500/40 bg-green-500/10 text-green-300";
  return "border-slate-500/40 bg-slate-500/10 text-slate-300";
}

function categoryLabel(category?: string) {
  const map: Record<string, string> = {
    protection_civil: "Protección Civil",
    public_services: "Servicios Públicos",
    medical: "Médico",
    security: "Seguridad",
    victim_attention: "Atención a Víctimas",
    social_support: "Apoyo Social",
    unknown: "General",
  };
  return map[category || ""] || category || "General";
}

function locationSourceLabel(source?: string) {
  if (source === "user_text") return "Reportada por usuario";
  if (source === "synthetic_911_geolocation") return "Simulada por geolocalización 911";
  return "Sin fuente";
}

function fmtDate(value?: string) {
  if (!value) return "Sin horario";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString("es-MX", {
    dateStyle: "short",
    timeStyle: "medium",
  });
}

function WhatsAppLabDashboard() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<WhatsAppLabMessage[]>([]);
  const [summary, setSummary] = useState<WhatsAppLabSummary>({});
  const [loading, setLoading] = useState(false);
  const [live, setLive] = useState(false);
  const [lastEvent, setLastEvent] = useState<string>("Sin eventos todavía");
  const [error, setError] = useState<string | null>(null);

  async function loadRecent() {
    const res = await fetch(`${API_BASE}/whatsapp-lab/messages/recent`);
    if (!res.ok) throw new Error(`recent HTTP ${res.status}`);
    const payload = await res.json();
    setMessages(normalizeRecentPayload(payload));
  }

  async function loadSummary() {
    const res = await fetch(`${API_BASE}/whatsapp-lab/summary`);
    if (!res.ok) throw new Error(`summary HTTP ${res.status}`);
    const payload = await res.json();
    setSummary(payload);
  }

  async function refreshAll() {
    try {
      setError(null);
      await Promise.all([loadRecent(), loadSummary()]);
    } catch (e: any) {
      setError(e?.message || "Error cargando datos");
    }
  }

  useEffect(() => {
    refreshAll();

    const es = new EventSource(`${API_BASE}/whatsapp-lab/events`);

    es.onopen = () => {
      setLive(true);
      setLastEvent("Conectado a eventos en vivo");
    };

    es.onerror = () => {
      setLive(false);
      setLastEvent("SSE desconectado o reconectando");
    };

    es.addEventListener("connected", (ev) => {
      setLive(true);
      setLastEvent(`Conectado: ${ev.data}`);
    });

    es.addEventListener("heartbeat", () => {
      setLive(true);
    });

    es.addEventListener("whatsapp_lab_update", (ev) => {
      setLive(true);
      setLastEvent(ev.data);
      refreshAll();
    });

    return () => es.close();
  }, []);

  async function sendMessage(text?: string) {
    const content = (text ?? message).trim();
    if (!content) return;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/whatsapp-lab/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: content }),
      });

      const payload = await res.json();

      if (!res.ok) {
        throw new Error(payload?.detail || `HTTP ${res.status}`);
      }

      setMessage("");
      setMessages((prev) => [payload, ...prev].slice(0, 50));
      await loadSummary();
    } catch (e: any) {
      setError(e?.message || "Error enviando mensaje");
    } finally {
      setLoading(false);
    }
  }

  const categoryRows = useMemo(() => {
    return Object.entries(summary.by_category || {}).sort((a, b) => b[1] - a[1]);
  }, [summary]);

  const latest = messages[0];

  return (
    <main className="mx-auto max-w-7xl px-6 py-10 text-slate-100">
      <section className="mb-8 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2 text-sm uppercase tracking-[0.25em] text-cyan-300">
            <MessageSquare className="h-4 w-4" />
            WhatsApp Lab
          </div>
          <h1 className="text-4xl font-bold">Centro de mensajes ciudadanos</h1>
          <p className="mt-2 max-w-3xl text-slate-400">
            Simulación local tipo WhatsApp: el ciudadano solo escribe el incidente y CENTINELA
            enriquece automáticamente teléfono demo, horario, ubicación, alcaldía, coordenadas,
            clasificación y prioridad.
          </p>
        </div>

        <div className="flex flex-wrap gap-2 no-print">
          <span
            className={`rounded-full border px-3 py-1 text-sm ${
              live
                ? "border-cyan-400/40 bg-cyan-400/10 text-cyan-200"
                : "border-slate-500/40 bg-slate-500/10 text-slate-300"
            }`}
          >
            {live ? "● En vivo" : "○ Reconectando"}
          </span>
          <button
            onClick={() => window.print()}
            className="inline-flex items-center gap-2 rounded-lg border border-cyan-500/40 bg-cyan-500/10 px-4 py-2 text-sm text-cyan-100 hover:bg-cyan-500/20"
          >
            <Printer className="h-4 w-4" />
            Exportar PDF
          </button>
        </div>
      </section>

      {error && (
        <section className="mb-6 rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-red-200">
          <div className="flex items-center gap-2 font-semibold">
            <AlertTriangle className="h-4 w-4" />
            Error
          </div>
          <p className="mt-1 text-sm">{error}</p>
        </section>
      )}

      <section className="mb-6 grid gap-4 md:grid-cols-4">
        <SummaryCard label="Mensajes totales" value={summary.total_messages ?? messages.length} />
        <SummaryCard label="Últimas 24h" value={summary.last_24h ?? 0} />
        <SummaryCard label="Requieren humano" value={summary.human_required_count ?? 0} />
        <SummaryCard label="Señales P0" value={summary.p0_count ?? 0} danger />
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="rounded-2xl border border-slate-700/80 bg-slate-900/70 p-5 shadow-xl">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold">Chat ciudadano</h2>
              <p className="text-sm text-slate-400">
                Escribe solo el incidente. La ubicación se detecta del texto o se simula por geoloc 911.
              </p>
            </div>
            <Activity className="h-5 w-5 text-cyan-300" />
          </div>

          <div className="mb-4 rounded-xl border border-slate-700 bg-slate-950/70 p-4">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) sendMessage();
              }}
              placeholder="Ej. Hay una persona herida inconsciente"
              className="min-h-28 w-full resize-none rounded-xl border border-slate-700 bg-slate-950 p-4 text-slate-100 outline-none focus:border-cyan-500"
            />

            <div className="mt-3 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <p className="text-xs text-slate-500">Ctrl + Enter para enviar</p>
              <button
                onClick={() => sendMessage()}
                disabled={loading || !message.trim()}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-cyan-500 px-4 py-2 font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Send className="h-4 w-4" />
                {loading ? "Enviando..." : "Enviar mensaje"}
              </button>
            </div>
          </div>

          <div className="mb-4">
            <p className="mb-2 text-xs uppercase tracking-[0.2em] text-slate-500">Ejemplos rápidos</p>
            <div className="flex flex-wrap gap-2 no-print">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  onClick={() => sendMessage(ex)}
                  className="rounded-full border border-slate-700 bg-slate-800/80 px-3 py-1 text-xs text-slate-300 hover:border-cyan-500 hover:text-cyan-200"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            {messages.length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-700 p-8 text-center text-slate-400">
                No hay mensajes todavía.
              </div>
            ) : (
              messages.slice(0, 8).map((m) => <MessageBubble key={m.message_id} msg={m} />)
            )}
          </div>
        </div>

        <aside className="space-y-6">
          <div className="rounded-2xl border border-slate-700/80 bg-slate-900/70 p-5">
            <h2 className="mb-3 text-xl font-semibold">Último evento enriquecido</h2>

            {latest ? (
              <EventDetails msg={latest} />
            ) : (
              <p className="text-sm text-slate-400">Aún no hay mensajes para mostrar.</p>
            )}
          </div>

          <div className="rounded-2xl border border-slate-700/80 bg-slate-900/70 p-5">
            <h2 className="mb-3 text-xl font-semibold">Distribución por categoría</h2>

            {categoryRows.length === 0 ? (
              <p className="text-sm text-slate-400">Sin datos todavía.</p>
            ) : (
              <div className="space-y-3">
                {categoryRows.map(([cat, count]) => (
                  <div key={cat}>
                    <div className="mb-1 flex justify-between text-sm">
                      <span>{categoryLabel(cat)}</span>
                      <span className="font-mono text-cyan-300">{count}</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                      <div
                        className="h-full rounded-full bg-cyan-400"
                        style={{
                          width: `${Math.min(
                            100,
                            ((count || 0) / Math.max(1, summary.total_messages || 1)) * 100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="rounded-2xl border border-slate-700/80 bg-slate-900/70 p-5 text-xs text-slate-400">
            <p className="font-semibold text-slate-300">SSE status</p>
            <p className="mt-2 break-all">{lastEvent}</p>
          </div>
        </aside>
      </section>

      <section className="mt-6 rounded-2xl border border-slate-700/80 bg-slate-900/70 p-5">
        <h2 className="mb-4 text-xl font-semibold">Mensajes recientes</h2>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="border-b border-slate-700 text-xs uppercase tracking-[0.15em] text-slate-500">
              <tr>
                <th className="py-3">Hora</th>
                <th className="py-3">Teléfono</th>
                <th className="py-3">Lugar</th>
                <th className="py-3">Incidente</th>
                <th className="py-3">Categoría</th>
                <th className="py-3">Prioridad</th>
                <th className="py-3">P0</th>
              </tr>
            </thead>
            <tbody>
              {messages.map((m) => (
                <tr key={m.message_id} className="border-b border-slate-800">
                  <td className="py-3 text-slate-300">{fmtDate(m.incident_time || m.created_at)}</td>
                  <td className="py-3 font-mono text-slate-300">{m.from_number_redacted || "***5678"}</td>
                  <td className="py-3">
                    <div className="max-w-[220px]">
                      <p className="truncate text-slate-200">{m.location_hint || "Ubicación no disponible"}</p>
                      <p className="text-xs text-slate-500">{locationSourceLabel(m.location_source)}</p>
                    </div>
                  </td>
                  <td className="py-3">
                    <p className="max-w-[260px] truncate">{m.message_text || m.message_text_redacted || "Sin texto"}</p>
                  </td>
                  <td className="py-3">{categoryLabel(m.category)}</td>
                  <td className="py-3">
                    <span className={`rounded-full border px-2 py-1 text-xs ${branchClass(m.branch)}`}>
                      {branchLabel(m.branch)}
                    </span>
                  </td>
                  <td className="py-3">
                    {(m.p0_signals || []).length > 0 ? (
                      <span className="text-red-300">{m.p0_signals?.join(", ")}</span>
                    ) : (
                      <span className="text-slate-500">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

function SummaryCard({ label, value, danger = false }: { label: string; value: number; danger?: boolean }) {
  return (
    <div className="rounded-2xl border border-slate-700/80 bg-slate-900/70 p-5">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className={`mt-3 text-3xl font-bold ${danger ? "text-red-400" : "text-cyan-300"}`}>
        {value}
      </p>
    </div>
  );
}

function MessageBubble({ msg }: { msg: WhatsAppLabMessage }) {
  const p0 = msg.p0_signals || [];

  return (
    <div className="space-y-3">
      <div className="ml-auto max-w-[86%] rounded-2xl rounded-br-sm border border-cyan-500/30 bg-cyan-500/10 p-4">
        <div className="mb-2 flex items-center gap-2 text-xs text-cyan-200">
          <User className="h-4 w-4" />
          Ciudadano · {msg.from_number_redacted || "***5678"}
        </div>
        <p className="text-slate-100">{msg.message_text || msg.message_text_redacted || "Sin texto"}</p>
      </div>

      <div className="max-w-[92%] rounded-2xl rounded-bl-sm border border-slate-700 bg-slate-800/70 p-4">
        <div className="mb-3 flex items-center gap-2 text-xs text-slate-300">
          <Bot className="h-4 w-4 text-cyan-300" />
          CENTINELA IA
        </div>

        <p className="mb-3 text-slate-100">{msg.bot_reply || "Reporte procesado."}</p>

        <div className="flex flex-wrap gap-2 text-xs">
          <span className="rounded-full border border-cyan-500/40 bg-cyan-500/10 px-2 py-1 text-cyan-200">
            {categoryLabel(msg.category)}
          </span>
          <span className={`rounded-full border px-2 py-1 ${branchClass(msg.branch)}`}>
            {branchLabel(msg.branch)}
          </span>
          <span className="rounded-full border border-slate-600 bg-slate-900 px-2 py-1 text-slate-300">
            Riesgo {msg.risk_level ?? "N/A"}
          </span>
          {msg.human_required && (
            <span className="rounded-full border border-orange-500/40 bg-orange-500/10 px-2 py-1 text-orange-200">
              Requiere humano
            </span>
          )}
          {p0.length > 0 && (
            <span className="rounded-full border border-red-500/40 bg-red-500/10 px-2 py-1 text-red-200">
              P0: {p0.join(", ")}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function EventDetails({ msg }: { msg: WhatsAppLabMessage }) {
  return (
    <div className="space-y-4 text-sm">
      <InfoRow icon={<Phone className="h-4 w-4" />} label="Teléfono" value={msg.from_number_redacted || "***5678"} />
      <InfoRow icon={<Clock className="h-4 w-4" />} label="Horario" value={fmtDate(msg.incident_time || msg.created_at)} />
      <InfoRow icon={<MapPin className="h-4 w-4" />} label="Lugar" value={msg.location_hint || "Ubicación no disponible"} />
      <InfoRow icon={<Activity className="h-4 w-4" />} label="Fuente" value={locationSourceLabel(msg.location_source)} />
      <InfoRow icon={<MapPin className="h-4 w-4" />} label="Alcaldía" value={msg.alcaldia_norm || "N/D"} />
      <InfoRow
        icon={<ShieldAlert className="h-4 w-4" />}
        label="Clasificación"
        value={`${categoryLabel(msg.category)} / ${branchLabel(msg.branch)} / Riesgo ${msg.risk_level ?? "N/A"}`}
      />
      <InfoRow
        icon={<AlertTriangle className="h-4 w-4" />}
        label="P0"
        value={(msg.p0_signals || []).length ? (msg.p0_signals || []).join(", ") : "Sin señales P0"}
      />
      <div className="rounded-xl border border-slate-700 bg-slate-950/70 p-3">
        <p className="mb-1 text-xs uppercase tracking-[0.18em] text-slate-500">Coordenadas sintéticas</p>
        <p className="font-mono text-cyan-200">
          {msg.latitude ?? "N/D"}, {msg.longitude ?? "N/D"}
        </p>
      </div>
    </div>
  );
}

function InfoRow({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="flex gap-3 rounded-xl border border-slate-700 bg-slate-950/60 p-3">
      <div className="mt-0.5 text-cyan-300">{icon}</div>
      <div>
        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{label}</p>
        <p className="mt-1 text-slate-200">{value}</p>
      </div>
    </div>
  );
}
