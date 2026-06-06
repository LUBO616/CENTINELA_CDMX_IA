import { Link, Outlet, useRouterState } from "@tanstack/react-router";
import { ShieldAlert, LayoutDashboard, PhoneCall, TrendingUp } from "lucide-react";

export default function AppShell() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const nav = [
    { to: "/", label: "Dashboard", icon: LayoutDashboard },
    { to: "/predictivo", label: "Predictivo", icon: TrendingUp },
    { to: "/simular", label: "Simular llamada", icon: PhoneCall },
  ];

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3 sm:px-6">
          <Link to="/" className="flex items-center gap-2">
            <div className="relative grid h-9 w-9 place-items-center rounded-md bg-primary/15 ring-1 ring-primary/40">
              <ShieldAlert className="h-5 w-5 text-primary" />
              <span className="absolute -right-0.5 -top-0.5 h-2 w-2 animate-pulse rounded-full bg-destructive" />
            </div>
            <div className="leading-tight">
              <div className="font-display text-sm font-bold tracking-wide">CENTINELA CDMX IA</div>
              <div className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                Centro de mando · demo
              </div>
            </div>
          </Link>

          <nav className="ml-6 hidden gap-1 md:flex">
            {nav.map((n) => {
              const active = pathname === n.to;
              const Icon = n.icon;
              return (
                <Link
                  key={n.to}
                  to={n.to}
                  className={[
                    "inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors",
                    active
                      ? "bg-primary/15 text-primary"
                      : "text-muted-foreground hover:bg-accent hover:text-foreground",
                  ].join(" ")}
                >
                  <Icon className="h-4 w-4" />
                  {n.label}
                </Link>
              );
            })}
          </nav>

          <div className="ml-auto hidden items-center gap-2 sm:flex">
            <span className="inline-flex h-2 w-2 animate-pulse rounded-full bg-risk-low" />
            <span className="text-xs text-muted-foreground">Sistema operativo</span>
          </div>
        </div>

        <div className="border-t border-destructive/40 bg-destructive/10">
          <div className="mx-auto max-w-7xl px-4 py-1.5 text-center text-[11px] font-medium uppercase tracking-wider text-destructive sm:px-6">
            ⚠ Demo educativa: no usar para emergencias reales
          </div>
        </div>

        {/* mobile nav */}
        <nav className="flex gap-1 border-t border-border px-2 py-2 md:hidden">
          {nav.map((n) => {
            const active = pathname === n.to;
            const Icon = n.icon;
            return (
              <Link
                key={n.to}
                to={n.to}
                className={[
                  "flex-1 inline-flex items-center justify-center gap-2 rounded-md px-3 py-2 text-xs",
                  active
                    ? "bg-primary/15 text-primary"
                    : "text-muted-foreground hover:bg-accent",
                ].join(" ")}
              >
                <Icon className="h-4 w-4" />
                {n.label}
              </Link>
            );
          })}
        </nav>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8">
        <Outlet />
      </main>

      <footer className="mx-auto max-w-7xl px-4 pb-8 pt-4 text-center text-xs text-muted-foreground sm:px-6">
        Datos sintéticos · CENTINELA CDMX IA — demo de hackathon
      </footer>
    </div>
  );
}
