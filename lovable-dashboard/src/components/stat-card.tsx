import type { ReactNode } from "react";

type Tone = "primary" | "low" | "mid" | "critical" | "analytics" | "muted";

const toneMap: Record<Tone, { ring: string; bg: string; text: string; dot: string }> = {
  primary: {
    ring: "ring-primary/30",
    bg: "bg-primary/10",
    text: "text-primary",
    dot: "bg-primary",
  },
  low: {
    ring: "ring-risk-low/40",
    bg: "bg-risk-low/10",
    text: "text-risk-low",
    dot: "bg-risk-low",
  },
  mid: {
    ring: "ring-risk-mid/40",
    bg: "bg-risk-mid/10",
    text: "text-risk-mid",
    dot: "bg-risk-mid",
  },
  critical: {
    ring: "ring-risk-critical/40",
    bg: "bg-risk-critical/10",
    text: "text-risk-critical",
    dot: "bg-risk-critical",
  },
  analytics: {
    ring: "ring-analytics/40",
    bg: "bg-analytics/10",
    text: "text-analytics",
    dot: "bg-analytics",
  },
  muted: {
    ring: "ring-border",
    bg: "bg-muted/40",
    text: "text-muted-foreground",
    dot: "bg-muted-foreground",
  },
};

interface Props {
  label: string;
  value: ReactNode;
  hint?: string;
  icon?: ReactNode;
  tone?: Tone;
}

export function StatCard({ label, value, hint, icon, tone = "primary" }: Props) {
  const t = toneMap[tone];
  return (
    <div
      className={[
        "relative overflow-hidden rounded-xl border border-border bg-card p-5 ring-1 transition-colors",
        t.ring,
      ].join(" ")}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            <span className={["h-1.5 w-1.5 rounded-full", t.dot].join(" ")} />
            {label}
          </div>
          <div className={["mt-3 font-mono text-3xl font-bold tabular-nums", t.text].join(" ")}>
            {value}
          </div>
          {hint && <div className="mt-1 text-xs text-muted-foreground">{hint}</div>}
        </div>
        {icon && (
          <div
            className={[
              "grid h-10 w-10 place-items-center rounded-lg",
              t.bg,
              t.text,
            ].join(" ")}
          >
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
