import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  fetchPredictiveOverview,
  fetchPredictiveHourly,
  fetchPredictiveCategories,
  fetchPredictiveAlcaldias,
  fetchPredictiveForecast,
  subscribePredictiveEvents,
  type PredictiveEvent,
} from "@/lib/centinela-api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { Activity, TrendingUp, TrendingDown, Minus, AlertTriangle, Users, Clock } from "lucide-react";

export const Route = createFileRoute("/predictivo")({
  component: PredictivoDashboard,
});

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8", "#82CA9D"];

function PredictivoDashboard() {
  const [lastEvent, setLastEvent] = useState<PredictiveEvent | null>(null);
  const [isLive, setIsLive] = useState(false);
  const [eventCount, setEventCount] = useState(0);

  const overviewQuery = useQuery({
    queryKey: ["predictive-overview"],
    queryFn: fetchPredictiveOverview,
    refetchInterval: 30000,
  });

  const hourlyQuery = useQuery({
    queryKey: ["predictive-hourly"],
    queryFn: fetchPredictiveHourly,
    refetchInterval: 60000,
  });

  const categoriesQuery = useQuery({
    queryKey: ["predictive-categories"],
    queryFn: fetchPredictiveCategories,
    refetchInterval: 60000,
  });

  const alcaldiasQuery = useQuery({
    queryKey: ["predictive-alcaldias"],
    queryFn: fetchPredictiveAlcaldias,
    refetchInterval: 60000,
  });

  const forecastQuery = useQuery({
    queryKey: ["predictive-forecast"],
    queryFn: fetchPredictiveForecast,
    refetchInterval: 60000,
  });

  useEffect(() => {
    let eventSource: EventSource | null = null;
    try {
      eventSource = subscribePredictiveEvents(
        (event) => {
          setLastEvent(event);
          setEventCount((prev) => prev + 1);
          setIsLive(true);
          if (event.operation === "INSERT" || event.operation === "UPDATE") {
            overviewQuery.refetch();
            hourlyQuery.refetch();
            categoriesQuery.refetch();
            alcaldiasQuery.refetch();
            forecastQuery.refetch();
          }
        },
        (error) => {
          console.error("SSE error:", error);
          setIsLive(false);
        }
      );
      setIsLive(true);
    } catch (error) {
      console.error("Failed to connect SSE:", error);
      setIsLive(false);
    }
    return () => {
      if (eventSource) {
        eventSource.close();
        setIsLive(false);
      }
    };
  }, []);

  const overview = overviewQuery.data;
  const hourly = hourlyQuery.data;
  const categories = categoriesQuery.data;
  const alcaldias = alcaldiasQuery.data;
  const forecast = forecastQuery.data;

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard Predictivo</h1>
          <p className="text-muted-foreground mt-1">
            Predicción operativa basada en datos sintéticos y patrones históricos
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={isLive ? "default" : "secondary"} className="gap-1">
            <Activity className={`h-3 w-3 \${isLive ? "animate-pulse" : ""}`} />
            {isLive ? "En vivo" : "Desconectado"}
          </Badge>
          {eventCount > 0 && <Badge variant="outline">{eventCount} eventos</Badge>}
        </div>
      </div>

      {lastEvent && (
        <Alert>
          <Activity className="h-4 w-4" />
          <AlertDescription>
            Último evento: {lastEvent.operation} en {lastEvent.incident_id} - {new Date(lastEvent.timestamp).toLocaleTimeString("es-MX")}
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Incidentes</CardTitle>
          </CardHeader>
          <CardContent>
            {overviewQuery.isLoading ? <Skeleton className="h-8 w-24" /> : <div className="text-2xl font-bold">{overview?.total_incidents.toLocaleString()}</div>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Últimas 24h</CardTitle>
          </CardHeader>
          <CardContent>
            {overviewQuery.isLoading ? <Skeleton className="h-8 w-24" /> : <div className="text-2xl font-bold">{overview?.last_24h.toLocaleString()}</div>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Críticos</CardTitle>
          </CardHeader>
          <CardContent>
            {overviewQuery.isLoading ? <Skeleton className="h-8 w-24" /> : <div className="text-2xl font-bold text-red-600">{overview?.critical_count.toLocaleString()}</div>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Requieren Humano</CardTitle>
          </CardHeader>
          <CardContent>
            {overviewQuery.isLoading ? <Skeleton className="h-8 w-24" /> : <div className="text-2xl font-bold">{overview?.human_required_count.toLocaleString()}</div>}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Predicción Próximas 24 Horas
          </CardTitle>
          <CardDescription>Estimación basada en patrones históricos</CardDescription>
        </CardHeader>
        <CardContent>
          {forecastQuery.isLoading ? <Skeleton className="h-32 w-full" /> : forecast ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <div className="text-sm text-muted-foreground mb-1">Próxima hora</div>
                <div className="text-3xl font-bold">{forecast.next_hour_expected_calls}</div>
                <div className="text-sm text-muted-foreground mt-1">llamadas esperadas</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground mb-1">Próximas 24h</div>
                <div className="text-3xl font-bold">{forecast.next_24h_expected_calls}</div>
                <div className="flex items-center gap-1 mt-1">
                  {forecast.trend === "increasing" && <TrendingUp className="h-4 w-4 text-red-500" />}
                  {forecast.trend === "decreasing" && <TrendingDown className="h-4 w-4 text-green-500" />}
                  {forecast.trend === "stable" && <Minus className="h-4 w-4 text-gray-500" />}
                  <span className="text-sm text-muted-foreground capitalize">{forecast.trend}</span>
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground mb-1">Nivel de staffing</div>
                <Badge variant={forecast.recommended_staffing_level === "high" ? "destructive" : forecast.recommended_staffing_level === "medium" ? "default" : "secondary"} className="text-lg px-3 py-1">
                  {forecast.recommended_staffing_level === "high" && "Alto"}
                  {forecast.recommended_staffing_level === "medium" && "Medio"}
                  {forecast.recommended_staffing_level === "low" && "Bajo"}
                </Badge>
                <div className="text-sm text-muted-foreground mt-1">Confianza: {(forecast.confidence * 100).toFixed(0)}%</div>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Distribución por Hora</CardTitle>
            <CardDescription>Incidentes por hora del día</CardDescription>
          </CardHeader>
          <CardContent>
            {hourlyQuery.isLoading ? <Skeleton className="h-64 w-full" /> : hourly ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={hourly.hourly_distribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" label={{ value: "Hora", position: "insideBottom", offset: -5 }} />
                  <YAxis label={{ value: "Incidentes", angle: -90, position: "insideLeft" }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="incident_count" fill="#8884d8" name="Incidentes" />
                </BarChart>
              </ResponsiveContainer>
            ) : null}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Distribución por Categoría</CardTitle>
            <CardDescription>Top categorías de incidentes</CardDescription>
          </CardHeader>
          <CardContent>
            {categoriesQuery.isLoading ? <Skeleton className="h-64 w-full" /> : categories ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={categories.categories.slice(0, 6)} dataKey="incident_count" nameKey="category" cx="50%" cy="50%" outerRadius={100} label>
                    {categories.categories.slice(0, 6).map((_, index) => (
                      <Cell key={`cell-\${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Top Alcaldías por Riesgo
          </CardTitle>
          <CardDescription>Alcaldías con mayor actividad de incidentes</CardDescription>
        </CardHeader>
        <CardContent>
          {alcaldiasQuery.isLoading ? <Skeleton className="h-64 w-full" /> : alcaldias ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Alcaldía</th>
                    <th className="text-right p-2">Incidentes</th>
                    <th className="text-right p-2">Riesgo Promedio</th>
                    <th className="text-right p-2">Críticos</th>
                    <th className="text-right p-2">P0</th>
                  </tr>
                </thead>
                <tbody>
                  {alcaldias.alcaldias.map((alc, idx) => (
                    <tr key={idx} className="border-b hover:bg-muted/50">
                      <td className="p-2 font-medium">{alc.alcaldia}</td>
                      <td className="text-right p-2">{alc.incident_count.toLocaleString()}</td>
                      <td className="text-right p-2">
                        <Badge variant={alc.avg_risk >= 7 ? "destructive" : alc.avg_risk >= 4 ? "default" : "secondary"}>{alc.avg_risk.toFixed(1)}</Badge>
                      </td>
                      <td className="text-right p-2">{alc.critical_count}</td>
                      <td className="text-right p-2">{alc.p0_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </CardContent>
      </Card>

      {forecast?.risk_hotspots && forecast.risk_hotspots.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Hotspots de Riesgo (Últimas 24h)
            </CardTitle>
            <CardDescription>Zonas con mayor riesgo promedio</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {forecast.risk_hotspots.map((hotspot, idx) => (
                <Card key={idx}>
                  <CardContent className="pt-6">
                    <div className="text-lg font-semibold">{hotspot.alcaldia}</div>
                    <div className="text-2xl font-bold text-red-600 mt-2">{hotspot.avg_risk.toFixed(1)}</div>
                    <div className="text-sm text-muted-foreground mt-1">{hotspot.incident_count} incidentes</div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="text-center text-sm text-muted-foreground">
        <p>Dashboard predictivo basado en {overview?.total_incidents.toLocaleString()} incidentes sintéticos</p>
        <p className="mt-1">Última actualización: {overview?.generated_at ? new Date(overview.generated_at).toLocaleString("es-MX") : "N/A"}</p>
      </div>
    </div>
  );
}
