import { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";

interface TimeseriesPoint {
  date: string;
  impressions: number;
  clicks: number;
  reach: number;
  leads: number;
  conversions: number;
  spend: number;
  revenue: number;
  ctr: number | null;
  cpc: number | null;
  cpm: number | null;
  cpl: number | null;
}

interface BreakdownRow {
  value: string;
  impressions: number;
  clicks: number;
  leads: number;
  spend: number;
  revenue: number;
  ctr: number | null;
  cpl: number | null;
  roas: number | null;
}

interface DashboardCampaignRow {
  plan_id: string;
  title: string;
  status: string;
  meta_campaign_id: string | null;
  impressions: number;
  clicks: number;
  reach: number;
  spend: number;
  revenue: number;
  leads: number;
  meta_leads: number;
  ctr: number | null;
  cpl: number | null;
  roas: number | null;
}

interface AlertRow {
  id: string;
  plan_id: string;
  plan_title: string | null;
  type: string;
  severity: string;
  title: string;
  message: string;
  metric_key: string;
  current_value: number | null;
  baseline_value: number | null;
  status: string;
  snapshot_date: string;
  created_at: string;
}

interface DashboardData {
  days: number;
  totals: {
    impressions: number;
    clicks: number;
    reach: number;
    spend: number;
    revenue: number;
    leads: number;
    meta_leads: number;
    ctr: number | null;
    cpc: number | null;
    cpm: number | null;
    cpl: number | null;
    roas: number | null;
    published_campaigns: number;
    total_campaigns: number;
  };
  timeseries: TimeseriesPoint[];
  by_campaign: DashboardCampaignRow[];
  by_placement: BreakdownRow[];
  by_device: BreakdownRow[];
  alerts: AlertRow[];
}

const PALETTE = ["#6366f1", "#10b981", "#f59e0b", "#f43f5e", "#06b6d4", "#8b5cf6", "#f97316", "#14b8a6"];

const PLACEMENT_LABELS: Record<string, string> = {
  facebook: "Facebook",
  instagram: "Instagram",
  audience_network: "Audience Network",
  messenger: "Messenger",
};
const DEVICE_LABELS: Record<string, string> = {
  mobile_app: "App móvil",
  mobile_web: "Web móvil",
  desktop: "Escritorio",
  unknown: "Desconocido",
};

function fmt(n: number | null | undefined, decimals = 0) {
  if (n == null) return "—";
  return n.toLocaleString("es-ES", { maximumFractionDigits: decimals });
}
function fmtEur(n: number | null | undefined) {
  if (n == null) return "—";
  return `€${n.toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}
function fmtPct(n: number | null | undefined) {
  if (n == null) return "—";
  return `${n.toFixed(2)}%`;
}

// ── Métricas disponibles en la serie temporal ────────────────────────────────
type MetricKey = "spend" | "leads" | "clicks" | "impressions" | "ctr" | "cpl" | "revenue";
const METRICS: { key: MetricKey; label: string; color: string; fmt: (n: number | null) => string }[] = [
  { key: "spend", label: "Gasto", color: "#6366f1", fmt: fmtEur },
  { key: "leads", label: "Leads", color: "#10b981", fmt: (n) => fmt(n) },
  { key: "clicks", label: "Clics", color: "#f59e0b", fmt: (n) => fmt(n) },
  { key: "impressions", label: "Impresiones", color: "#06b6d4", fmt: (n) => fmt(n) },
  { key: "ctr", label: "CTR", color: "#8b5cf6", fmt: fmtPct },
  { key: "cpl", label: "CPL", color: "#f43f5e", fmt: fmtEur },
  { key: "revenue", label: "Revenue", color: "#f97316", fmt: fmtEur },
];

function HeroKPI({ label, value, sub, accent, icon }: {
  label: string; value: string; sub?: string; accent: string; icon: string;
}) {
  return (
    <div className="relative bg-white/70 backdrop-blur-xl rounded-2xl border border-white/50 shadow-glass p-5 overflow-hidden">
      <div className="absolute -top-8 -right-8 w-24 h-24 rounded-full opacity-10" style={{ backgroundColor: accent }} />
      <div className="relative">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center text-base"
            style={{ backgroundColor: accent + "1a", color: accent }}>{icon}</div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{label}</p>
        </div>
        <p className="text-3xl font-bold text-gray-900 leading-none">{value}</p>
        {sub && <p className="text-xs text-gray-400 mt-2">{sub}</p>}
      </div>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white/70 backdrop-blur-xl rounded-xl border border-white/50 shadow-glass p-4">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">{label}</p>
      <p className="text-xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

// ── Serie temporal (line + area) ──────────────────────────────────────────────
function LineChart({ data }: { data: TimeseriesPoint[] }) {
  const [metric, setMetric] = useState<MetricKey>("spend");
  const meta = METRICS.find((m) => m.key === metric)!;

  const points = data.map((d) => ({ date: d.date, value: (d[metric] ?? 0) as number }));
  const W = 760, H = 220, padX = 8, padY = 16;
  const max = Math.max(...points.map((p) => p.value), 0.0001);
  const stepX = points.length > 1 ? (W - padX * 2) / (points.length - 1) : 0;

  const coords = points.map((p, i) => {
    const x = padX + i * stepX;
    const y = H - padY - (p.value / max) * (H - padY * 2);
    return { x, y, ...p };
  });
  const linePath = coords.map((c, i) => `${i === 0 ? "M" : "L"}${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(" ");
  const areaPath = coords.length
    ? `${linePath} L${coords[coords.length - 1].x.toFixed(1)},${H - padY} L${coords[0].x.toFixed(1)},${H - padY} Z`
    : "";

  const first = points[0]?.value ?? 0;
  const last = points[points.length - 1]?.value ?? 0;
  const delta = first > 0 ? ((last - first) / first) * 100 : null;

  return (
    <div className="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/50 shadow-glass p-5">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div>
          <h3 className="text-sm font-semibold text-gray-700">Evolución temporal</h3>
          {delta != null && (
            <p className={`text-xs mt-0.5 ${delta >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
              {delta >= 0 ? "▲" : "▼"} {Math.abs(delta).toFixed(1)}% vs inicio del periodo
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-1">
          {METRICS.map((m) => (
            <button key={m.key} onClick={() => setMetric(m.key)}
              className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
                metric === m.key ? "text-white border-transparent" : "bg-white text-gray-500 border-gray-200 hover:border-gray-300"
              }`}
              style={metric === m.key ? { backgroundColor: m.color } : undefined}>
              {m.label}
            </button>
          ))}
        </div>
      </div>
      {points.length === 0 ? (
        <p className="text-xs text-gray-400 py-12 text-center">Sin datos en este periodo todavía</p>
      ) : (
        <>
          <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: H }}>
            <defs>
              <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={meta.color} stopOpacity="0.25" />
                <stop offset="100%" stopColor={meta.color} stopOpacity="0" />
              </linearGradient>
            </defs>
            {areaPath && <path d={areaPath} fill="url(#areaGrad)" />}
            {linePath && <path d={linePath} fill="none" stroke={meta.color} strokeWidth={2} strokeLinejoin="round" />}
            {coords.map((c, i) => (
              <circle key={i} cx={c.x} cy={c.y} r={2.5} fill={meta.color}>
                <title>{`${c.date}: ${meta.fmt(c.value)}`}</title>
              </circle>
            ))}
          </svg>
          <div className="flex justify-between mt-1 text-[10px] text-gray-400">
            <span>{points[0]?.date}</span>
            <span>{points[points.length - 1]?.date}</span>
          </div>
        </>
      )}
    </div>
  );
}

function BarChart({ title, data, formatter }: {
  title: string; data: { label: string; value: number; color: string }[]; formatter: (n: number) => string;
}) {
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <div className="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/50 shadow-glass p-5">
      <h3 className="text-sm font-semibold text-gray-700 mb-4">{title}</h3>
      {data.length === 0 ? (
        <p className="text-xs text-gray-400 py-8 text-center">Sin datos todavía</p>
      ) : (
        <div className="space-y-3">
          {data.map((d, i) => (
            <div key={i}>
              <div className="flex items-baseline justify-between mb-1">
                <span className="text-xs text-gray-600 line-clamp-1 max-w-[70%]">{d.label}</span>
                <span className="text-xs font-semibold text-gray-900">{formatter(d.value)}</span>
              </div>
              <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${(d.value / max) * 100}%`, backgroundColor: d.color }} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function FunnelChart({ impressions, clicks, leads }: { impressions: number; clicks: number; leads: number }) {
  const max = Math.max(impressions, 1);
  const steps = [
    { label: "Impresiones", value: impressions, color: "#6366f1" },
    { label: "Clics", value: clicks, color: "#8b5cf6" },
    { label: "Leads", value: leads, color: "#10b981" },
  ];
  return (
    <div className="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/50 shadow-glass p-5">
      <h3 className="text-sm font-semibold text-gray-700 mb-4">Embudo de conversión</h3>
      <div className="space-y-2">
        {steps.map((s, i) => {
          const widthPct = (s.value / max) * 100;
          const prev = i > 0 ? steps[i - 1].value : null;
          const rate = prev && prev > 0 ? ((s.value / prev) * 100).toFixed(2) : null;
          return (
            <div key={s.label}>
              <div className="flex items-baseline justify-between mb-1.5">
                <span className="text-xs font-medium text-gray-700">{s.label}</span>
                <div className="flex items-baseline gap-2">
                  {rate && <span className="text-xs text-gray-400">{rate}%</span>}
                  <span className="text-sm font-bold text-gray-900">{fmt(s.value)}</span>
                </div>
              </div>
              <div className="w-full bg-gray-100 rounded-lg overflow-hidden h-8 flex items-center">
                <div className="h-full rounded-lg transition-all duration-700"
                  style={{ width: `${Math.max(widthPct, 4)}%`, backgroundColor: s.color }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const SEVERITY_STYLES: Record<string, { box: string; icon: string }> = {
  critical: { box: "bg-rose-50 border-rose-200 text-rose-800", icon: "🔴" },
  warning: { box: "bg-amber-50 border-amber-200 text-amber-800", icon: "🟠" },
  info: { box: "bg-sky-50 border-sky-200 text-sky-800", icon: "🔵" },
};

function AlertsPanel({ alerts, onDismiss }: { alerts: AlertRow[]; onDismiss: (id: string) => void }) {
  if (alerts.length === 0) return null;
  return (
    <div className="space-y-2">
      {alerts.map((a) => {
        const s = SEVERITY_STYLES[a.severity] ?? SEVERITY_STYLES.warning;
        return (
          <div key={a.id} className={`rounded-xl border px-4 py-3 flex items-start gap-3 ${s.box}`}>
            <span className="text-base leading-none mt-0.5">{s.icon}</span>
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-2 flex-wrap">
                <p className="text-sm font-semibold">{a.title}</p>
                {a.plan_title && <span className="text-[11px] opacity-70">· {a.plan_title}</span>}
              </div>
              <p className="text-xs mt-0.5 opacity-90 leading-relaxed">{a.message}</p>
            </div>
            <button onClick={() => onDismiss(a.id)}
              className="text-xs font-medium opacity-60 hover:opacity-100 shrink-0"
              title="Descartar alerta">✕</button>
          </div>
        );
      })}
    </div>
  );
}

const RANGES = [
  { days: 7, label: "7 días" },
  { days: 30, label: "30 días" },
  { days: 90, label: "90 días" },
];

export function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  useEffect(() => {
    setLoading(true);
    api.get<DashboardData>(`/analytics/dashboard?days=${days}`)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [days]);

  async function dismissAlert(id: string) {
    setData((prev) => prev ? { ...prev, alerts: prev.alerts.filter((a) => a.id !== id) } : prev);
    try {
      await api.post(`/analytics/alerts/${id}/dismiss`, {});
    } catch {
      /* optimista: si falla, reaparecerá en la próxima carga */
    }
  }

  const spendData = useMemo(() =>
    (data?.by_campaign ?? [])
      .filter((c) => c.spend > 0).slice(0, 6)
      .map((c, i) => ({ label: c.title, value: c.spend, color: PALETTE[i % PALETTE.length] })),
    [data]);

  const leadsData = useMemo(() =>
    (data?.by_campaign ?? [])
      .filter((c) => c.leads > 0 || c.meta_leads > 0)
      .map((c, i) => ({ label: c.title, value: Math.max(c.leads, c.meta_leads), color: PALETTE[i % PALETTE.length] }))
      .sort((a, b) => b.value - a.value).slice(0, 6),
    [data]);

  const placementData = useMemo(() =>
    (data?.by_placement ?? []).slice(0, 6)
      .map((b, i) => ({ label: PLACEMENT_LABELS[b.value] ?? b.value, value: b.spend, color: PALETTE[i % PALETTE.length] })),
    [data]);

  const deviceData = useMemo(() =>
    (data?.by_device ?? []).slice(0, 6)
      .map((b, i) => ({ label: DEVICE_LABELS[b.value] ?? b.value, value: b.spend, color: PALETTE[i % PALETTE.length] })),
    [data]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!data || data.totals.total_campaigns === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400">
        <div className="text-center">
          <p className="text-4xl mb-2">📊</p>
          <p className="text-lg font-medium text-gray-700">Sin campañas todavía</p>
          <p className="text-sm mt-1">Crea una campaña desde "Nueva campaña" para ver métricas aquí.</p>
        </div>
      </div>
    );
  }

  const t = data.totals;
  const hasSnapshots = t.impressions > 0 || data.timeseries.length > 0;

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-sm text-gray-400 mt-0.5">
              Visión global · {t.published_campaigns} campaña{t.published_campaigns !== 1 ? "s" : ""} publicada
              {t.published_campaigns !== 1 ? "s" : ""} de {t.total_campaigns} · últimos {data.days} días
            </p>
          </div>
          <div className="flex gap-1 bg-white/60 rounded-lg border border-white/50 p-1">
            {RANGES.map((r) => (
              <button key={r.days} onClick={() => setDays(r.days)}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                  days === r.days ? "bg-brand-600 text-white" : "text-gray-500 hover:bg-gray-100"
                }`}>
                {r.label}
              </button>
            ))}
          </div>
        </div>

        {/* Alertas automáticas */}
        <AlertsPanel alerts={data.alerts ?? []} onDismiss={dismissAlert} />

        {!hasSnapshots && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800">
            ℹ️ Aún no hay snapshots de métricas en este periodo. Se recogen automáticamente cada hora
            tras publicar una campaña en Meta.
          </div>
        )}

        {/* Hero KPIs */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <HeroKPI label="Gasto total" value={fmtEur(t.spend)} sub={t.cpl != null ? `CPL ${fmtEur(t.cpl)}` : undefined} accent="#6366f1" icon="💰" />
          <HeroKPI label="Leads" value={fmt(Math.max(t.leads, t.meta_leads))} sub={t.meta_leads > 0 ? `${t.meta_leads} en Meta` : undefined} accent="#10b981" icon="🎯" />
          <HeroKPI label="ROAS" value={t.roas != null ? `${t.roas.toFixed(2)}x` : "—"} sub={t.revenue > 0 ? `${fmtEur(t.revenue)} revenue` : undefined} accent="#14b8a6" icon="📈" />
          <HeroKPI label="Alcance" value={fmt(t.reach)} sub={t.ctr != null ? `CTR ${fmtPct(t.ctr)}` : undefined} accent="#f43f5e" icon="📡" />
        </div>

        {/* Mini stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <MiniStat label="Impresiones" value={fmt(t.impressions)} />
          <MiniStat label="Clics" value={fmt(t.clicks)} />
          <MiniStat label="CTR medio" value={fmtPct(t.ctr)} />
          <MiniStat label="CPC medio" value={fmtEur(t.cpc)} />
        </div>

        {/* Serie temporal */}
        <LineChart data={data.timeseries} />

        {/* Funnel */}
        <FunnelChart impressions={t.impressions} clicks={t.clicks} leads={Math.max(t.leads, t.meta_leads)} />

        {/* Campañas */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <BarChart title="Top campañas por gasto" data={spendData} formatter={fmtEur} />
          <BarChart title="Top campañas por leads" data={leadsData} formatter={(n) => fmt(n)} />
        </div>

        {/* Breakdowns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <BarChart title="Gasto por plataforma" data={placementData} formatter={fmtEur} />
          <BarChart title="Gasto por dispositivo" data={deviceData} formatter={fmtEur} />
        </div>
      </div>
    </div>
  );
}
