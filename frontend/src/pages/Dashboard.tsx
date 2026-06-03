import { useEffect, useState } from "react";
import { api } from "../lib/api";

interface MetaInsights {
  impressions: number;
  clicks: number;
  spend: number;
  reach: number;
  cpc: number | null;
  ctr: number | null;
  cpp: number | null;
  leads: number;
}

interface CampaignRow {
  plan_id: string;
  title: string;
  status: string;
  meta_campaign_id: string | null;
  total_leads: number;
  total_views: number;
  total_conversions: number;
  insights: MetaInsights | null;
  loading: boolean;
}

const PALETTE = ["#6366f1", "#10b981", "#f59e0b", "#f43f5e", "#06b6d4", "#8b5cf6", "#f97316", "#14b8a6"];

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

function HeroKPI({
  label,
  value,
  sub,
  accent,
  icon,
}: {
  label: string;
  value: string;
  sub?: string;
  accent: string;
  icon: string;
}) {
  return (
    <div className="relative bg-white/70 backdrop-blur-xl rounded-2xl border border-white/50 shadow-glass p-5 overflow-hidden">
      <div
        className="absolute -top-8 -right-8 w-24 h-24 rounded-full opacity-10"
        style={{ backgroundColor: accent }}
      />
      <div className="relative">
        <div className="flex items-center gap-2 mb-3">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center text-base"
            style={{ backgroundColor: accent + "1a", color: accent }}
          >
            {icon}
          </div>
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

function BarChart({
  title,
  data,
  formatter,
}: {
  title: string;
  data: { label: string; value: number; color: string }[];
  formatter: (n: number) => string;
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
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${(d.value / max) * 100}%`,
                    backgroundColor: d.color,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function DonutChart({
  title,
  data,
  total,
  totalLabel,
}: {
  title: string;
  data: { label: string; value: number; color: string }[];
  total: number;
  totalLabel: string;
}) {
  const size = 180;
  const stroke = 24;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const sum = data.reduce((s, d) => s + d.value, 0);

  let offset = 0;
  const segments = data.map((d) => {
    const portion = sum > 0 ? d.value / sum : 0;
    const length = portion * circumference;
    const seg = {
      ...d,
      dashArray: `${length} ${circumference - length}`,
      dashOffset: -offset,
    };
    offset += length;
    return seg;
  });

  return (
    <div className="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/50 shadow-glass p-5">
      <h3 className="text-sm font-semibold text-gray-700 mb-4">{title}</h3>
      {sum === 0 ? (
        <p className="text-xs text-gray-400 py-8 text-center">Sin datos todavía</p>
      ) : (
        <div className="flex items-center gap-5">
          <div className="relative" style={{ width: size, height: size }}>
            <svg width={size} height={size} className="-rotate-90">
              <circle
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke="#f3f4f6"
                strokeWidth={stroke}
              />
              {segments.map((s, i) => (
                <circle
                  key={i}
                  cx={size / 2}
                  cy={size / 2}
                  r={radius}
                  fill="none"
                  stroke={s.color}
                  strokeWidth={stroke}
                  strokeDasharray={s.dashArray}
                  strokeDashoffset={s.dashOffset}
                  strokeLinecap="butt"
                />
              ))}
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <p className="text-2xl font-bold text-gray-900">{fmt(total)}</p>
              <p className="text-xs text-gray-400">{totalLabel}</p>
            </div>
          </div>
          <div className="flex-1 space-y-2 min-w-0">
            {segments.map((s, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span
                  className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
                  style={{ backgroundColor: s.color }}
                />
                <span className="text-gray-600 line-clamp-1 flex-1">{s.label}</span>
                <span className="font-semibold text-gray-900">{fmt(s.value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function FunnelChart({
  impressions,
  clicks,
  leads,
}: {
  impressions: number;
  clicks: number;
  leads: number;
}) {
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
                <div
                  className="h-full rounded-lg transition-all duration-700 flex items-center justify-end pr-2"
                  style={{
                    width: `${Math.max(widthPct, 4)}%`,
                    backgroundColor: s.color,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function Dashboard() {
  const [rows, setRows] = useState<CampaignRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<
        {
          plan_id: string;
          title: string;
          status: string;
          meta_campaign_id: string | null;
          total_leads: number;
          total_views: number;
          total_conversions: number;
        }[]
      >("/campaigns")
      .then((campaigns) => {
        const initial: CampaignRow[] = campaigns.map((c) => ({
          ...c,
          insights: null,
          loading: !!c.meta_campaign_id,
        }));
        setRows(initial);
        setLoading(false);

        campaigns.forEach((c) => {
          if (!c.meta_campaign_id) return;
          api
            .get<MetaInsights>(`/campaigns/${c.plan_id}/meta-insights`)
            .then((insights) => {
              setRows((prev) =>
                prev.map((r) => (r.plan_id === c.plan_id ? { ...r, insights, loading: false } : r))
              );
            })
            .catch(() => {
              setRows((prev) =>
                prev.map((r) => (r.plan_id === c.plan_id ? { ...r, loading: false } : r))
              );
            });
        });
      })
      .catch(() => setLoading(false));
  }, []);

  const published = rows.filter((r) => r.meta_campaign_id);
  const totalSpend = published.reduce((s, r) => s + (r.insights?.spend ?? 0), 0);
  const totalImpressions = published.reduce((s, r) => s + (r.insights?.impressions ?? 0), 0);
  const totalClicks = published.reduce((s, r) => s + (r.insights?.clicks ?? 0), 0);
  const totalMetaLeads = published.reduce((s, r) => s + (r.insights?.leads ?? 0), 0);
  const totalLeadsDb = rows.reduce((s, r) => s + (r.total_leads ?? 0), 0);
  const totalReach = published.reduce((s, r) => s + (r.insights?.reach ?? 0), 0);
  const totalViews = rows.reduce((s, r) => s + (r.total_views ?? 0), 0);
  const avgCtr = totalImpressions > 0 ? (totalClicks / totalImpressions) * 100 : null;
  const avgCpc = totalClicks > 0 ? totalSpend / totalClicks : null;
  const cpl = totalMetaLeads > 0 ? totalSpend / totalMetaLeads : null;
  const convRate = totalViews > 0 ? (totalLeadsDb / totalViews) * 100 : null;

  const spendData = published
    .filter((r) => (r.insights?.spend ?? 0) > 0)
    .sort((a, b) => (b.insights?.spend ?? 0) - (a.insights?.spend ?? 0))
    .slice(0, 6)
    .map((r, i) => ({
      label: r.title,
      value: r.insights?.spend ?? 0,
      color: PALETTE[i % PALETTE.length],
    }));

  const leadsData = rows
    .filter((r) => (r.total_leads ?? 0) > 0 || (r.insights?.leads ?? 0) > 0)
    .map((r, i) => ({
      label: r.title,
      value: Math.max(r.total_leads ?? 0, r.insights?.leads ?? 0),
      color: PALETTE[i % PALETTE.length],
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 6);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (rows.length === 0) {
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

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            Visión global · {published.length} campaña{published.length !== 1 ? "s" : ""} publicada
            {published.length !== 1 ? "s" : ""} de {rows.length}
          </p>
        </div>

        {/* Hero KPIs */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <HeroKPI
            label="Gasto total"
            value={fmtEur(totalSpend)}
            sub={cpl != null ? `CPL ${fmtEur(cpl)}` : undefined}
            accent="#6366f1"
            icon="💰"
          />
          <HeroKPI
            label="Leads"
            value={fmt(Math.max(totalLeadsDb, totalMetaLeads))}
            sub={totalLeadsDb > 0 && totalMetaLeads > 0 ? `${totalMetaLeads} en Meta` : undefined}
            accent="#10b981"
            icon="🎯"
          />
          <HeroKPI
            label="Clics"
            value={fmt(totalClicks)}
            sub={avgCpc != null ? `CPC ${fmtEur(avgCpc)}` : undefined}
            accent="#f59e0b"
            icon="🖱️"
          />
          <HeroKPI
            label="Alcance"
            value={fmt(totalReach)}
            sub={avgCtr != null ? `CTR ${fmtPct(avgCtr)}` : undefined}
            accent="#f43f5e"
            icon="📡"
          />
        </div>

        {/* Mini stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <MiniStat label="Impresiones" value={fmt(totalImpressions)} />
          <MiniStat label="Visitas landing" value={fmt(totalViews)} />
          <MiniStat label="CTR medio" value={fmtPct(avgCtr)} />
          <MiniStat label="Conversión" value={fmtPct(convRate)} />
        </div>

        {/* Funnel */}
        <FunnelChart
          impressions={totalImpressions}
          clicks={totalClicks}
          leads={Math.max(totalLeadsDb, totalMetaLeads)}
        />

        {/* Charts grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <BarChart title="Top campañas por gasto" data={spendData} formatter={fmtEur} />
          <DonutChart
            title="Distribución de leads"
            data={leadsData}
            total={leadsData.reduce((s, d) => s + d.value, 0)}
            totalLabel="leads"
          />
        </div>
      </div>
    </div>
  );
}
