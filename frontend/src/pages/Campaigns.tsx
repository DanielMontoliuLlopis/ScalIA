import { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import { CampaignModal, type Campaign } from "../components/campaigns/CampaignModal";

interface OfferComparisonItem {
  plan_id: string;
  title: string;
  status: string;
  is_offer_test: boolean;
  offer_test_label: string | null;
  tipo_oferta: string | null;
  urgencia: string | null;
  garantia: string | null;
  transformacion: string | null;
  precio_base: number | null;
  total_leads: number;
  total_views: number;
  total_conversions: number;
  meta_campaign_id: string | null;
}

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

type View = "grid" | "table";

const VIEW_KEY = "campaigns_view";

function statusLabel(s: string) {
  const map: Record<string, string> = {
    executing: "En ejecución",
    pending_ads_approval: "Pendiente de ads",
    pending_copy_approval: "Pendiente de copies",
    done: "Completada",
  };
  return map[s] ?? s;
}

function statusDot(s: string) {
  if (s === "done") return "bg-green-500";
  if (s === "executing") return "bg-blue-500 animate-pulse";
  return "bg-yellow-400";
}

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

function CampaignCard({ campaign, onClick, onCompare }: { campaign: Campaign; onClick: () => void; onCompare: () => void }) {
  const heroImage = campaign.landings.find((l) => l.hero_image_url)?.hero_image_url;
  const primaryColor = campaign.landings[0]?.primary_color ?? "#6366f1";
  const convRate =
    campaign.total_views > 0
      ? ((campaign.total_conversions / campaign.total_views) * 100).toFixed(1) + "%"
      : "—";

  return (
    <button
      onClick={onClick}
      className="group bg-white/70 backdrop-blur-xl rounded-2xl border border-white/50 shadow-glass overflow-hidden hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 text-left w-full"
    >
      <div className="relative h-36 overflow-hidden">
        {heroImage ? (
          <img
            src={heroImage}
            alt={campaign.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div
            className="w-full h-full flex items-center justify-center"
            style={{ backgroundColor: primaryColor + "22" }}
          >
            <span className="text-5xl font-black opacity-20" style={{ color: primaryColor }}>
              G
            </span>
          </div>
        )}
        <div className="absolute top-2.5 right-2.5 flex items-center gap-1.5 bg-white/90 backdrop-blur-sm px-2.5 py-1 rounded-full shadow-sm">
          <span className={`w-1.5 h-1.5 rounded-full ${statusDot(campaign.status)}`} />
          <span className="text-xs font-medium text-gray-700">{statusLabel(campaign.status)}</span>
        </div>
        <div className="absolute top-2.5 left-2.5 flex gap-1 flex-wrap">
          {campaign.is_offer_test && (
            <span className="bg-amber-400/90 text-amber-900 text-[10px] font-bold px-2 py-0.5 rounded-full">
              {campaign.offer_test_label ?? "Test Oferta"}
            </span>
          )}
          {campaign.landings.map((l) => (
            <span
              key={l.id}
              className="w-5 h-5 rounded-full bg-black/40 text-white text-xs font-bold flex items-center justify-center"
            >
              {l.variant.toUpperCase()}
            </span>
          ))}
        </div>
      </div>

      <div className="p-4">
        <h3 className="font-semibold text-gray-900 text-sm line-clamp-2 mb-3">{campaign.title}</h3>

        <div className="grid grid-cols-3 gap-2 mb-3">
          {[
            { label: "Visitas", value: campaign.total_views.toLocaleString() },
            { label: "Leads", value: campaign.total_leads.toLocaleString() },
            { label: "Conv.", value: convRate },
          ].map((m) => (
            <div key={m.label} className="text-center">
              <p className="text-sm font-bold text-gray-900">{m.value}</p>
              <p className="text-xs text-gray-400">{m.label}</p>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">
            {new Date(campaign.created_at).toLocaleDateString("es-ES", {
              day: "2-digit",
              month: "short",
              year: "numeric",
            })}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={(e) => { e.stopPropagation(); onCompare(); }}
              className="text-xs text-amber-500 hover:text-amber-600 font-medium transition-colors"
            >
              Test oferta
            </button>
            <span className="text-xs font-medium text-brand-600 group-hover:text-brand-700 transition-colors">
              Ver detalles →
            </span>
          </div>
        </div>
      </div>
    </button>
  );
}

interface CampaignRow extends Campaign {
  insights: MetaInsights | null;
  insightsLoading: boolean;
  roas: number | null;
}

type SortKey = "title" | "spend" | "impressions" | "clicks" | "ctr" | "cpc" | "leads" | "views" | "roas";

function CampaignTable({
  rows,
  onSelect,
}: {
  rows: CampaignRow[];
  onSelect: (c: Campaign) => void;
}) {
  const [sort, setSort] = useState<{ key: SortKey; dir: "asc" | "desc" }>({
    key: "roas",
    dir: "desc",
  });

  const sorted = useMemo(() => {
    const arr = [...rows];
    arr.sort((a, b) => {
      const get = (r: CampaignRow): number | string => {
        switch (sort.key) {
          case "title":
            return r.title.toLowerCase();
          case "spend":
            return r.insights?.spend ?? -1;
          case "impressions":
            return r.insights?.impressions ?? -1;
          case "clicks":
            return r.insights?.clicks ?? -1;
          case "ctr":
            return r.insights?.ctr ?? -1;
          case "cpc":
            return r.insights?.cpc ?? -1;
          case "leads":
            return Math.max(r.total_leads ?? 0, r.insights?.leads ?? 0);
          case "views":
            return r.total_views ?? 0;
          case "roas":
            return r.roas ?? -1;
        }
      };
      const av = get(a);
      const bv = get(b);
      if (av < bv) return sort.dir === "asc" ? -1 : 1;
      if (av > bv) return sort.dir === "asc" ? 1 : -1;
      return 0;
    });
    return arr;
  }, [rows, sort]);

  const toggle = (key: SortKey) =>
    setSort((s) => (s.key === key ? { key, dir: s.dir === "asc" ? "desc" : "asc" } : { key, dir: "desc" }));

  const Th = ({ k, label, align = "right" }: { k: SortKey; label: string; align?: "left" | "right" }) => (
    <th
      onClick={() => toggle(k)}
      className={`px-4 py-3 font-medium cursor-pointer select-none hover:text-gray-700 ${
        align === "right" ? "text-right" : "text-left"
      }`}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        {sort.key === k && <span className="text-[10px]">{sort.dir === "asc" ? "▲" : "▼"}</span>}
      </span>
    </th>
  );

  return (
    <div className="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/50 shadow-glass overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[800px]">
          <thead>
            <tr className="border-b border-gray-100 text-xs text-gray-400 uppercase tracking-wide">
              <Th k="title" label="Campaña" align="left" />
              <Th k="spend" label="Gasto" />
              <Th k="impressions" label="Impr." />
              <Th k="clicks" label="Clics" />
              <Th k="ctr" label="CTR" />
              <Th k="cpc" label="CPC" />
              <Th k="views" label="Visitas" />
              <Th k="leads" label="Leads" />
              <Th k="roas" label="ROAS" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {sorted.map((r) => (
              <tr
                key={r.plan_id}
                onClick={() => onSelect(r)}
                className="hover:bg-gray-50/50 transition-colors cursor-pointer"
              >
                <td className="px-4 py-3.5">
                  <div className="flex items-center gap-2.5">
                    <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${statusDot(r.status)}`} />
                    <span className="font-medium text-gray-900 line-clamp-1">{r.title}</span>
                    {!r.meta_campaign_id && (
                      <span className="text-xs text-gray-300 italic">sin publicar</span>
                    )}
                  </div>
                </td>
                {r.insightsLoading ? (
                  <td colSpan={6} className="px-4 py-3.5 text-center">
                    <div className="flex justify-center">
                      <div className="w-3 h-3 border border-brand-300 border-t-transparent rounded-full animate-spin" />
                    </div>
                  </td>
                ) : r.insights ? (
                  <>
                    <td className="px-4 py-3.5 text-right text-gray-700">{fmtEur(r.insights.spend)}</td>
                    <td className="px-4 py-3.5 text-right text-gray-700">{fmt(r.insights.impressions)}</td>
                    <td className="px-4 py-3.5 text-right text-gray-700">{fmt(r.insights.clicks)}</td>
                    <td className="px-4 py-3.5 text-right text-gray-700">{fmtPct(r.insights.ctr)}</td>
                    <td className="px-4 py-3.5 text-right text-gray-700">{fmtEur(r.insights.cpc)}</td>
                  </>
                ) : (
                  <>
                    <td className="px-4 py-3.5 text-right text-gray-300">—</td>
                    <td className="px-4 py-3.5 text-right text-gray-300">—</td>
                    <td className="px-4 py-3.5 text-right text-gray-300">—</td>
                    <td className="px-4 py-3.5 text-right text-gray-300">—</td>
                    <td className="px-4 py-3.5 text-right text-gray-300">—</td>
                  </>
                )}
                <td className="px-4 py-3.5 text-right text-gray-700">{fmt(r.total_views)}</td>
                <td className="px-4 py-3.5 text-right font-semibold text-brand-600">
                  {fmt(Math.max(r.total_leads ?? 0, r.insights?.leads ?? 0))}
                </td>
                <td className={`px-4 py-3.5 text-right font-semibold ${r.roas != null ? (r.roas >= 2 ? "text-green-600" : "text-amber-600") : "text-gray-300"}`}>
                  {r.roas != null ? `${r.roas.toFixed(2)}x` : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function OfferComparisonPanel({ planId, onClose }: { planId: string; onClose: () => void }) {
  const [items, setItems] = useState<OfferComparisonItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    transformacion: "",
    tipo_oferta: "",
    urgencia: "",
    garantia: "",
    offer_test_label: "Oferta B",
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api
      .get<OfferComparisonItem[]>(`/plans/${planId}/offer-comparison`)
      .then((d) => { setItems(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [planId]);

  const handleCreate = async () => {
    if (!form.transformacion.trim()) return;
    setSubmitting(true);
    try {
      await api.post(`/plans/${planId}/offer-test`, {
        transformacion: form.transformacion,
        tipo_oferta: form.tipo_oferta || undefined,
        urgencia: form.urgencia || undefined,
        garantia: form.garantia || undefined,
        offer_test_label: form.offer_test_label || "Oferta B",
      });
      const updated = await api.get<OfferComparisonItem[]>(`/plans/${planId}/offer-comparison`);
      setItems(updated);
      setCreating(false);
    } finally {
      setSubmitting(false);
    }
  };

  const winner = items.length >= 2
    ? items.reduce((a, b) => {
        const rateA = a.total_views > 0 ? a.total_leads / a.total_views : 0;
        const rateB = b.total_views > 0 ? b.total_leads / b.total_views : 0;
        return rateA >= rateB ? a : b;
      })
    : null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white/90 backdrop-blur-2xl rounded-2xl shadow-glass-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-5 border-b border-gray-100">
          <h2 className="font-bold text-gray-900">Comparativa de Ofertas</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>

        <div className="p-5 space-y-4">
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="w-5 h-5 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <>
              {items.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {items.map((item) => {
                    const convRate = item.total_views > 0
                      ? ((item.total_leads / item.total_views) * 100).toFixed(1) + "%"
                      : "—";
                    const isWinner = winner?.plan_id === item.plan_id && items.length >= 2 && item.total_leads > 0;
                    return (
                      <div
                        key={item.plan_id}
                        className={`p-4 rounded-xl border-2 ${isWinner ? "border-green-400 bg-green-50" : "border-gray-200 bg-gray-50"}`}
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${item.is_offer_test ? "bg-amber-100 text-amber-700" : "bg-brand-100 text-brand-700"}`}>
                            {item.offer_test_label ?? "Oferta A"}
                          </span>
                          {isWinner && <span className="text-xs font-bold text-green-600">Ganadora</span>}
                        </div>
                        <p className="text-xs text-gray-500 mb-3 line-clamp-2">{item.transformacion ?? "—"}</p>
                        <div className="grid grid-cols-3 gap-2 text-center">
                          <div>
                            <p className="text-sm font-bold text-gray-900">{item.total_leads}</p>
                            <p className="text-xs text-gray-400">Leads</p>
                          </div>
                          <div>
                            <p className="text-sm font-bold text-gray-900">{item.total_views}</p>
                            <p className="text-xs text-gray-400">Visitas</p>
                          </div>
                          <div>
                            <p className="text-sm font-bold text-gray-900">{convRate}</p>
                            <p className="text-xs text-gray-400">Conv.</p>
                          </div>
                        </div>
                        <div className="mt-2 text-xs text-gray-400 space-y-0.5">
                          {item.tipo_oferta && <p>Tipo: {item.tipo_oferta}</p>}
                          {item.urgencia && item.urgencia !== "sin_urgencia" && <p>Urgencia: {item.urgencia}</p>}
                          {item.garantia && item.garantia !== "sin_garantia" && <p>Garantía: {item.garantia}</p>}
                        </div>
                        <div className="mt-2">
                          <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${item.status === "done" ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"}`}>
                            {statusLabel(item.status)}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {winner && items.length >= 2 && winner.total_leads >= 10 && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-xl text-sm text-green-800">
                  <strong>Recomendación:</strong> La <em>{winner.offer_test_label ?? "Oferta A"}</em> lleva ventaja
                  con {winner.total_leads} leads y una conversión de{" "}
                  {winner.total_views > 0 ? ((winner.total_leads / winner.total_views) * 100).toFixed(1) : 0}%.
                  Considera consolidar presupuesto en esa oferta.
                </div>
              )}

              {!creating ? (
                <button
                  onClick={() => setCreating(true)}
                  className="w-full py-2.5 rounded-xl border-2 border-dashed border-amber-300 text-amber-600 text-sm font-medium hover:bg-amber-50 transition-colors"
                >
                  + Testear oferta alternativa (10% del presupuesto)
                </button>
              ) : (
                <div className="p-4 border border-gray-200 rounded-xl space-y-3">
                  <p className="text-sm font-semibold text-gray-800">Nueva oferta de test</p>
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">Transformación (qué promete esta oferta)</label>
                    <textarea
                      rows={2}
                      value={form.transformacion}
                      onChange={(e) => setForm((f) => ({ ...f, transformacion: e.target.value }))}
                      placeholder="ej: Cerrar 3 clientes nuevos en 30 días"
                      className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-300"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs text-gray-500 block mb-1">Tipo de oferta</label>
                      <select
                        value={form.tipo_oferta}
                        onChange={(e) => setForm((f) => ({ ...f, tipo_oferta: e.target.value }))}
                        className="w-full border border-gray-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none"
                      >
                        <option value="">Sin cambio</option>
                        <option value="evergreen">Evergreen</option>
                        <option value="lanzamiento">Lanzamiento</option>
                        <option value="descuento_limitado">Descuento limitado</option>
                        <option value="prueba_gratuita">Prueba gratuita</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-gray-500 block mb-1">Urgencia</label>
                      <select
                        value={form.urgencia}
                        onChange={(e) => setForm((f) => ({ ...f, urgencia: e.target.value }))}
                        className="w-full border border-gray-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none"
                      >
                        <option value="">Sin cambio</option>
                        <option value="sin_urgencia">Sin urgencia</option>
                        <option value="fecha_limite">Fecha límite</option>
                        <option value="plazas_limitadas">Plazas limitadas</option>
                        <option value="bonus_temporal">Bonus temporal</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-gray-500 block mb-1">Garantía</label>
                      <select
                        value={form.garantia}
                        onChange={(e) => setForm((f) => ({ ...f, garantia: e.target.value }))}
                        className="w-full border border-gray-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none"
                      >
                        <option value="">Sin cambio</option>
                        <option value="sin_garantia">Sin garantía</option>
                        <option value="satisfaccion">Satisfacción</option>
                        <option value="resultados">Resultados</option>
                        <option value="devolucion_X_dias">Devolución X días</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-gray-500 block mb-1">Etiqueta</label>
                      <input
                        type="text"
                        value={form.offer_test_label}
                        onChange={(e) => setForm((f) => ({ ...f, offer_test_label: e.target.value }))}
                        placeholder="Oferta B"
                        className="w-full border border-gray-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none"
                      />
                    </div>
                  </div>
                  <div className="flex gap-2 pt-1">
                    <button
                      onClick={() => setCreating(false)}
                      className="flex-1 py-2 rounded-lg border border-gray-200 text-sm text-gray-500 hover:bg-gray-50"
                    >
                      Cancelar
                    </button>
                    <button
                      onClick={handleCreate}
                      disabled={submitting || !form.transformacion.trim()}
                      className="flex-1 py-2 rounded-lg bg-amber-500 text-white text-sm font-medium hover:bg-amber-600 disabled:opacity-50"
                    >
                      {submitting ? "Creando…" : "Crear test"}
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export function Campaigns() {
  const [rows, setRows] = useState<CampaignRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Campaign | null>(null);
  const [compareId, setCompareId] = useState<string | null>(null);
  const [view, setView] = useState<View>(() => {
    if (typeof window === "undefined") return "grid";
    return (localStorage.getItem(VIEW_KEY) as View) ?? "grid";
  });

  useEffect(() => {
    localStorage.setItem(VIEW_KEY, view);
  }, [view]);

  useEffect(() => {
    api
      .get<Campaign[]>("/campaigns")
      .then((campaigns) => {
        const initial: CampaignRow[] = campaigns.map((c) => ({
          ...c,
          insights: null,
          insightsLoading: !!c.meta_campaign_id,
          roas: null,
        }));
        setRows(initial);
        setLoading(false);

        campaigns.forEach((c) => {
          api
            .get<{ roas: number | null }>(`/campaigns/${c.plan_id}/metrics`)
            .then((m) => {
              setRows((prev) =>
                prev.map((r) => (r.plan_id === c.plan_id ? { ...r, roas: m.roas } : r))
              );
            })
            .catch(() => {});

          if (!c.meta_campaign_id) return;
          api
            .get<MetaInsights>(`/campaigns/${c.plan_id}/meta-insights`)
            .then((insights) => {
              setRows((prev) =>
                prev.map((r) =>
                  r.plan_id === c.plan_id ? { ...r, insights, insightsLoading: false } : r
                )
              );
            })
            .catch(() => {
              setRows((prev) =>
                prev.map((r) => (r.plan_id === c.plan_id ? { ...r, insightsLoading: false } : r))
              );
            });
        });
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6 gap-4 flex-wrap">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Mis Campañas</h1>
            <p className="text-sm text-gray-400 mt-0.5">
              {loading ? "Cargando…" : `${rows.length} campaña${rows.length !== 1 ? "s" : ""}`}
            </p>
          </div>

          {!loading && rows.length > 0 && (
            <div className="inline-flex items-center bg-white border border-gray-200 rounded-xl p-1">
              <button
                onClick={() => setView("grid")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  view === "grid"
                    ? "bg-brand-50 text-brand-700"
                    : "text-gray-500 hover:text-gray-700"
                }`}
                title="Vista cuadrícula"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="7" height="7" />
                  <rect x="14" y="3" width="7" height="7" />
                  <rect x="3" y="14" width="7" height="7" />
                  <rect x="14" y="14" width="7" height="7" />
                </svg>
                Cuadrícula
              </button>
              <button
                onClick={() => setView("table")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  view === "table"
                    ? "bg-brand-50 text-brand-700"
                    : "text-gray-500 hover:text-gray-700"
                }`}
                title="Vista tabla"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="3" y1="6" x2="21" y2="6" />
                  <line x1="3" y1="12" x2="21" y2="12" />
                  <line x1="3" y1="18" x2="21" y2="18" />
                </svg>
                Tabla
              </button>
            </div>
          )}
        </div>

        {loading && (
          <div className="flex justify-center py-20">
            <div className="w-6 h-6 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {!loading && rows.length === 0 && (
          <div className="text-center py-20">
            <p className="text-5xl mb-4">📣</p>
            <h2 className="text-lg font-semibold text-gray-700 mb-1">Sin campañas todavía</h2>
            <p className="text-sm text-gray-400 max-w-xs mx-auto">
              Cuando apruebes un plan desde el chat, la campaña aparecerá aquí con sus métricas en
              tiempo real.
            </p>
          </div>
        )}

        {!loading && rows.length > 0 && view === "grid" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {rows.map((c) => (
              <CampaignCard
                key={c.plan_id}
                campaign={c}
                onClick={() => setSelected(c)}
                onCompare={() => setCompareId(c.plan_id)}
              />
            ))}
          </div>
        )}

        {!loading && rows.length > 0 && view === "table" && (
          <CampaignTable rows={rows} onSelect={setSelected} />
        )}
      </div>

      {selected && <CampaignModal campaign={selected} onClose={() => setSelected(null)} />}
      {compareId && (
        <OfferComparisonPanel planId={compareId} onClose={() => setCompareId(null)} />
      )}
    </div>
  );
}
