import { useState, useEffect, useCallback } from "react";
import { api } from "../../lib/api";

interface Recommendation {
  id: string;
  plan_id: string;
  type: string;
  reasoning: string;
  action_payload: Record<string, unknown>;
  status: "pending" | "approved" | "rejected";
  applied_at: string | null;
  created_at: string;
}

const TYPE_LABELS: Record<string, { label: string; icon: string; color: string }> = {
  budget_increase:   { label: "Aumentar presupuesto", icon: "📈", color: "bg-green-50 border-green-200" },
  budget_decrease:   { label: "Reducir presupuesto",  icon: "📉", color: "bg-amber-50 border-amber-200" },
  copy_refresh:      { label: "Renovar copies",        icon: "✍️", color: "bg-violet-50 border-violet-200" },
  audience_expand:   { label: "Ampliar audiencia",     icon: "🎯", color: "bg-sky-50 border-sky-200" },
  audience_narrow:   { label: "Afinar audiencia",      icon: "🔍", color: "bg-sky-50 border-sky-200" },
  bid_adjustment:    { label: "Ajustar puja",          icon: "⚖️", color: "bg-brand-50 border-brand-200" },
  pause_variant:     { label: "Pausar variante",       icon: "⏸", color: "bg-orange-50 border-orange-200" },
  pause_campaign:    { label: "Pausar campaña",        icon: "🛑", color: "bg-red-50 border-red-200" },
};

function PayloadDetail({ payload }: { payload: Record<string, unknown> }) {
  const entries = Object.entries(payload).filter(([, v]) => v !== null && v !== undefined);
  if (!entries.length) return null;
  return (
    <div className="mt-2 grid grid-cols-2 gap-1">
      {entries.map(([k, v]) => (
        <div key={k} className="bg-white/70 rounded px-2 py-1">
          <p className="text-[10px] text-gray-400 uppercase">{k.replace(/_/g, " ")}</p>
          <p className="text-xs font-mono text-gray-700">{String(v)}</p>
        </div>
      ))}
    </div>
  );
}

export function RecommendationCards({ planId }: { planId: string }) {
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchRecs = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.get<Recommendation[]>(`/recommendations/campaigns/${planId}`);
      setRecs(data);
    } catch {
      // silencioso — campaña puede no tener recomendaciones aún
    } finally {
      setLoading(false);
    }
  }, [planId]);

  useEffect(() => {
    fetchRecs();
  }, [fetchRecs]);

  async function triggerAnalysis() {
    setTriggering(true);
    try {
      await api.post(`/recommendations/campaigns/${planId}/trigger`, {});
      setTimeout(fetchRecs, 3000);
    } catch {
      // silencioso
    } finally {
      setTriggering(false);
    }
  }

  async function handleApprove(id: string) {
    setActionLoading(id);
    try {
      const updated = await api.post<Recommendation>(`/recommendations/${id}/approve`, {});
      setRecs((prev) => prev.map((r) => (r.id === id ? updated : r)));
    } finally {
      setActionLoading(null);
    }
  }

  async function handleReject(id: string) {
    setActionLoading(id);
    try {
      const updated = await api.post<Recommendation>(`/recommendations/${id}/reject`, {});
      setRecs((prev) => prev.map((r) => (r.id === id ? updated : r)));
    } finally {
      setActionLoading(null);
    }
  }

  const pending = recs.filter((r) => r.status === "pending");
  const done = recs.filter((r) => r.status !== "pending");

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-800">Recomendaciones de optimización</h3>
          <p className="text-xs text-gray-400 mt-0.5">Generadas por OptimizationAgent cada 24h</p>
        </div>
        <button
          onClick={triggerAnalysis}
          disabled={triggering || loading}
          className="px-3 py-1.5 text-xs font-medium rounded-lg bg-brand-600 hover:bg-brand-700 text-white disabled:opacity-60"
        >
          {triggering ? "Analizando…" : "Analizar ahora"}
        </button>
      </div>

      {loading && (
        <div className="text-center py-6 text-xs text-gray-400">Cargando recomendaciones…</div>
      )}

      {!loading && recs.length === 0 && (
        <div className="rounded-xl border border-dashed border-gray-200 p-6 text-center">
          <p className="text-2xl mb-2">🤖</p>
          <p className="text-sm font-medium text-gray-600">Sin recomendaciones aún</p>
          <p className="text-xs text-gray-400 mt-1">
            El agente analizará la campaña cada 24h automáticamente, o haz clic en "Analizar ahora".
          </p>
        </div>
      )}

      {pending.length > 0 && (
        <div className="space-y-2">
          {pending.map((rec) => {
            const meta = TYPE_LABELS[rec.type] ?? { label: rec.type, icon: "💡", color: "bg-gray-50 border-gray-200" };
            const busy = actionLoading === rec.id;
            return (
              <div key={rec.id} className={`rounded-xl border p-4 ${meta.color}`}>
                <div className="flex items-start gap-3">
                  <span className="text-xl shrink-0">{meta.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <span className="text-sm font-semibold text-gray-800">{meta.label}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 font-medium">
                        Pendiente
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 mt-1 leading-relaxed">{rec.reasoning}</p>
                    <PayloadDetail payload={rec.action_payload} />
                    <div className="flex gap-2 mt-3">
                      <button
                        disabled={busy}
                        onClick={() => handleApprove(rec.id)}
                        className="px-3 py-1.5 text-xs font-medium rounded-lg bg-green-600 hover:bg-green-700 text-white disabled:opacity-60"
                      >
                        {busy ? "…" : "✓ Aprobar"}
                      </button>
                      <button
                        disabled={busy}
                        onClick={() => handleReject(rec.id)}
                        className="px-3 py-1.5 text-xs font-medium rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 disabled:opacity-60"
                      >
                        Descartar
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {done.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">Historial</p>
          {done.map((rec) => {
            const meta = TYPE_LABELS[rec.type] ?? { label: rec.type, icon: "💡", color: "" };
            const isApproved = rec.status === "approved";
            return (
              <div key={rec.id} className="flex items-center gap-3 py-2 px-3 rounded-lg bg-gray-50 border border-gray-100">
                <span className="text-base">{meta.icon}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-gray-700 truncate">{meta.label}</p>
                  <p className="text-[10px] text-gray-400 truncate">{rec.reasoning.slice(0, 80)}…</p>
                </div>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-medium shrink-0 ${
                    isApproved
                      ? "bg-green-100 text-green-700"
                      : "bg-gray-200 text-gray-500"
                  }`}
                >
                  {isApproved ? "Aprobado" : "Descartado"}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
