import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import type { Lead, LeadStatus } from "./types";
import { ACTION_COLORS, SEGMENT_COLORS } from "./constants";

const LEAD_STATUS_LABELS: Record<LeadStatus, string> = {
  new: "Nuevo",
  contacted: "Contactado",
  showed_up: "Se presentó",
  closed: "Cerrado",
  lost: "Perdido",
};

const LEAD_STATUS_COLORS: Record<LeadStatus, string> = {
  new: "bg-gray-100 text-gray-600",
  contacted: "bg-blue-100 text-blue-700",
  showed_up: "bg-amber-100 text-amber-700",
  closed: "bg-green-100 text-green-700",
  lost: "bg-red-100 text-red-500",
};

function LeadStatusBadge({ status }: { status: LeadStatus }) {
  return (
    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${LEAD_STATUS_COLORS[status]}`}>
      {LEAD_STATUS_LABELS[status]}
    </span>
  );
}

function timeUntil(iso: string | null): string {
  if (!iso) return "";
  const diffMs = new Date(iso).getTime() - Date.now();
  if (diffMs <= 0) return "ya";
  const h = Math.round(diffMs / 36e5);
  if (h < 24) return `en ${h}h`;
  return `en ${Math.round(h / 24)}d`;
}

function ScoreBadge({ score, segment }: { score: number | null; segment: string | null }) {
  if (score == null) return <span className="text-xs text-gray-400">—</span>;
  const seg = segment ?? "cold";
  return (
    <div className="flex items-center gap-2">
      <div className={`px-2 py-0.5 rounded-full text-xs font-bold border ${SEGMENT_COLORS[seg]}`}>
        {score}
      </div>
      <span className="text-xs text-gray-400 capitalize">{seg}</span>
    </div>
  );
}

function SequenceProgress({ lead }: { lead: Lead }) {
  const status = lead.sequence_status;
  if (!status) return <span className="text-xs text-gray-400">—</span>;

  const total = status.email.total + status.whatsapp.total;
  const sent = status.email.sent + status.whatsapp.sent;
  if (total === 0) {
    return <span className="text-xs text-gray-400">Sin secuencia</span>;
  }

  const pct = Math.round((sent / total) * 100);
  const next = status.email.next_at || status.whatsapp.next_at;
  const nextOrder = status.email.next_order ?? status.whatsapp.next_order;

  return (
    <div className="space-y-1 min-w-[140px]">
      <div className="flex items-center justify-between text-xs">
        <span className="font-semibold text-gray-700">
          {sent}/{total}
        </span>
        {nextOrder ? (
          <span className="text-gray-400">→ #{nextOrder} {timeUntil(next)}</span>
        ) : (
          <span className="text-green-600 font-medium">✓ Completa</span>
        )}
      </div>
      <div className="h-1.5 rounded-full bg-gray-100 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-brand-500 to-violet-500 transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function LeadDetail({
  lead,
  onClose,
  onToggle,
  onPipelineUpdate,
}: {
  lead: Lead;
  onClose: () => void;
  onToggle: (done: boolean, note?: string) => Promise<void>;
  onPipelineUpdate: (leadId: string, status: LeadStatus, closedValue?: number | null) => Promise<void>;
}) {
  const action = lead.recommended_action;
  const status = lead.sequence_status;
  const done = !!lead.action_completed_at;
  const [note, setNote] = useState(lead.action_note ?? "");
  const [saving, setSaving] = useState(false);
  const [pipelineStatus, setPipelineStatus] = useState<LeadStatus>(lead.lead_status);
  const [closedValue, setClosedValue] = useState<string>(lead.closed_value != null ? String(lead.closed_value) : "");
  const [savingPipeline, setSavingPipeline] = useState(false);

  async function savePipeline() {
    setSavingPipeline(true);
    try {
      await onPipelineUpdate(lead.id, pipelineStatus, closedValue ? Number(closedValue) : null);
    } finally {
      setSavingPipeline(false);
    }
  }

  async function toggle() {
    setSaving(true);
    try {
      await onToggle(!done, note);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="bg-white/90 backdrop-blur-2xl rounded-2xl shadow-glass-lg w-full max-w-xl max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between p-5 border-b border-gray-100">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <ScoreBadge score={lead.score} segment={lead.segment} />
              <span className="text-xs text-gray-400">
                {new Date(lead.created_at).toLocaleString("es-ES", {
                  day: "2-digit",
                  month: "short",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
            <h2 className="font-bold text-gray-900 text-base truncate">{lead.email}</h2>
            {lead.nombre && <p className="text-xs text-gray-500 mt-0.5">{lead.nombre}</p>}
          </div>
          <button
            onClick={onClose}
            className="ml-3 shrink-0 w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100"
          >
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {/* Acción recomendada + toggle hecho */}
          {action && (
            <div
              className={`rounded-xl border p-4 ${
                done ? "bg-green-50 border-green-200 text-green-800" : ACTION_COLORS[action.color]
              }`}
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl">{done ? "✅" : action.icon}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-sm font-bold">
                      {done ? "Acción completada" : action.label}
                    </p>
                    {!done && (
                      <span className="text-[10px] font-medium uppercase tracking-wide opacity-70">
                        Prioridad {action.priority}
                      </span>
                    )}
                  </div>
                  <p className="text-xs opacity-80">{action.reason}</p>
                  {done && lead.action_completed_at && (
                    <p className="text-[11px] opacity-70 mt-1">
                      Hecho el{" "}
                      {new Date(lead.action_completed_at).toLocaleString("es-ES", {
                        day: "2-digit",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  )}
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-current/20 space-y-2">
                <input
                  type="text"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Nota opcional (resultado de la llamada, próximo paso…)"
                  className="w-full px-2.5 py-1.5 text-xs bg-white/70 border border-current/20 rounded-lg focus:outline-none focus:ring-1 focus:ring-current/40"
                />
                <button
                  onClick={toggle}
                  disabled={saving}
                  className={`w-full px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                    done
                      ? "bg-white text-green-700 hover:bg-green-100"
                      : "bg-current text-white hover:opacity-90"
                  }`}
                  style={done ? {} : { color: "white" }}
                >
                  {saving ? "Guardando…" : done ? "↩ Marcar como pendiente" : "✓ Marcar como hecho"}
                </button>
              </div>
            </div>
          )}

          {/* Datos del lead */}
          <div className="rounded-xl border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 border-b border-gray-200 px-4 py-2 text-xs font-semibold text-gray-500 uppercase">
              Datos
            </div>
            <div className="p-4 grid grid-cols-2 gap-3 text-xs">
              <Field label="Email" value={lead.email} />
              <Field label="Nombre" value={lead.nombre} />
              <Field label="Empresa" value={lead.empresa} />
              <Field label="Teléfono" value={lead.telefono} />
              <Field label="Empleados" value={lead.num_empleados} />
              {Object.entries(lead.extra_data || {}).map(([k, v]) => (
                <Field key={k} label={k.replace(/_/g, " ")} value={String(v ?? "")} />
              ))}
            </div>
          </div>

          {/* Scoring breakdown */}
          {lead.scoring_breakdown && Object.keys(lead.scoring_breakdown).length > 0 && (
            <div className="rounded-xl border border-gray-200 overflow-hidden">
              <div className="bg-gray-50 border-b border-gray-200 px-4 py-2 text-xs font-semibold text-gray-500 uppercase">
                Desglose del score
              </div>
              <div className="p-4 space-y-2">
                {Object.entries(lead.scoring_breakdown).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between text-xs">
                    <span className="text-gray-600 capitalize">{k.replace(/_/g, " ")}</span>
                    <span className="font-mono font-semibold text-gray-800">+{v}</span>
                  </div>
                ))}
                <div className="flex items-center justify-between text-xs pt-2 border-t border-gray-100">
                  <span className="font-semibold text-gray-700">Total</span>
                  <span className="font-bold text-brand-600">{lead.score}/100</span>
                </div>
              </div>
            </div>
          )}

          {/* Estado secuencia */}
          {status && (
            <div className="rounded-xl border border-gray-200 overflow-hidden">
              <div className="bg-gray-50 border-b border-gray-200 px-4 py-2 text-xs font-semibold text-gray-500 uppercase">
                Estado de la secuencia
              </div>
              <div className="p-4 space-y-3">
                <ChannelSummary label="Email" emoji="✉️" data={status.email} color="indigo" />
                <ChannelSummary label="WhatsApp" emoji="💬" data={status.whatsapp} color="emerald" />
              </div>
            </div>
          )}

          {/* Pipeline */}
          <div className="rounded-xl border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 border-b border-gray-200 px-4 py-2 text-xs font-semibold text-gray-500 uppercase">
              Pipeline
            </div>
            <div className="p-4 space-y-3">
              <div>
                <p className="text-[10px] text-gray-400 uppercase mb-1.5">Estado</p>
                <div className="flex flex-wrap gap-1.5">
                  {(["new", "contacted", "showed_up", "closed", "lost"] as LeadStatus[]).map((s) => (
                    <button
                      key={s}
                      onClick={() => setPipelineStatus(s)}
                      className={`px-2.5 py-1 rounded-full text-[10px] font-semibold border transition-colors ${
                        pipelineStatus === s
                          ? LEAD_STATUS_COLORS[s] + " border-current/30"
                          : "bg-white text-gray-400 border-gray-200 hover:border-gray-400"
                      }`}
                    >
                      {LEAD_STATUS_LABELS[s]}
                    </button>
                  ))}
                </div>
              </div>
              {(pipelineStatus === "closed" || lead.closed_value != null) && (
                <div>
                  <p className="text-[10px] text-gray-400 uppercase mb-1">Valor cerrado (€)</p>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={closedValue}
                    onChange={(e) => setClosedValue(e.target.value)}
                    placeholder="ej: 997"
                    className="w-40 px-2.5 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:border-brand-400"
                  />
                </div>
              )}
              <button
                onClick={savePipeline}
                disabled={savingPipeline}
                className="w-full px-3 py-2 text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white rounded-lg disabled:opacity-60"
              >
                {savingPipeline ? "Guardando…" : "Guardar pipeline"}
              </button>
            </div>
          </div>

          {/* Timeline eventos */}
          {lead.sequence_events.length > 0 && (
            <div className="rounded-xl border border-gray-200 overflow-hidden">
              <div className="bg-gray-50 border-b border-gray-200 px-4 py-2 text-xs font-semibold text-gray-500 uppercase">
                Historial
              </div>
              <div className="p-4 space-y-2">
                {lead.sequence_events.map((ev) => (
                  <div key={ev.id} className="flex items-start gap-2 text-xs">
                    <span className="mt-0.5">{ev.channel === "email" ? "✉️" : "💬"}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-gray-700">#{ev.order}</span>
                        <StatusPill status={ev.status} />
                        <span className="text-gray-400 text-[10px]">
                          {ev.sent_at
                            ? new Date(ev.sent_at).toLocaleString("es-ES", {
                                day: "2-digit",
                                month: "short",
                                hour: "2-digit",
                                minute: "2-digit",
                              })
                            : ev.scheduled_at
                            ? `Prog. ${new Date(ev.scheduled_at).toLocaleString("es-ES", {
                                day: "2-digit",
                                month: "short",
                                hour: "2-digit",
                              })}`
                            : ""}
                        </span>
                      </div>
                      {ev.subject && <p className="text-gray-600 truncate">{ev.subject}</p>}
                      {ev.preview && (
                        <p className="text-gray-400 text-[11px] line-clamp-2">{ev.preview}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string | null }) {
  return (
    <div>
      <p className="text-[10px] text-gray-400 uppercase tracking-wide">{label}</p>
      <p className="text-xs font-medium text-gray-800">{value || "—"}</p>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const styles: Record<string, string> = {
    sent: "bg-green-100 text-green-700",
    scheduled: "bg-blue-100 text-blue-700",
    failed: "bg-red-100 text-red-700",
    skipped: "bg-gray-100 text-gray-500",
  };
  const labels: Record<string, string> = {
    sent: "Enviado",
    scheduled: "Programado",
    failed: "Fallo",
    skipped: "Omitido",
  };
  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${styles[status] ?? ""}`}>
      {labels[status] ?? status}
    </span>
  );
}

function ChannelSummary({
  label,
  emoji,
  data,
  color,
}: {
  label: string;
  emoji: string;
  data: { total: number; sent: number; failed: number; skipped: number; next_order: number | null; next_at: string | null; next_subject: string | null };
  color: "indigo" | "emerald";
}) {
  if (data.total === 0) {
    return (
      <div className="flex items-center gap-2 text-xs text-gray-400">
        <span>{emoji}</span>
        <span>{label}: sin programar</span>
      </div>
    );
  }
  const pct = Math.round((data.sent / data.total) * 100);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5">
          <span>{emoji}</span>
          <span className="font-semibold text-gray-700">{label}</span>
          <span className="text-gray-400">
            {data.sent}/{data.total} enviados
          </span>
        </div>
        {data.failed > 0 && (
          <span className="text-red-600 text-[10px] font-medium">{data.failed} fallos</span>
        )}
      </div>
      <div className="h-1.5 rounded-full bg-gray-100 overflow-hidden">
        <div
          className={`h-full ${color === "indigo" ? "bg-brand-500" : "bg-emerald-500"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {data.next_order && (
        <p className="text-[11px] text-gray-500">
          Siguiente: #{data.next_order}
          {data.next_subject ? ` — ${data.next_subject}` : ""}
          {data.next_at && (
            <span className="text-gray-400"> ({timeUntil(data.next_at)})</span>
          )}
        </p>
      )}
    </div>
  );
}

export function TabLeads({ planId }: { planId: string }) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "hot" | "warm" | "cold" | "pending" | "done">("pending");
  const [selected, setSelected] = useState<Lead | null>(null);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  async function updatePipeline(leadId: string, status: LeadStatus, closedValue?: number | null) {
    const updated = await api.patch<Lead>(`/leads/${leadId}`, {
      lead_status: status,
      closed_value: closedValue ?? null,
    });
    setLeads((prev) => prev.map((l) => (l.id === leadId ? updated : l)));
    if (selected?.id === leadId) setSelected(updated);
  }

  useEffect(() => {
    api
      .get<Lead[]>(`/campaigns/${planId}/leads`)
      .then(setLeads)
      .finally(() => setLoading(false));
  }, [planId]);

  async function toggleLead(lead: Lead, done: boolean, note?: string) {
    setTogglingId(lead.id);
    try {
      const updated = await api.patch<Lead>(
        `/campaigns/${planId}/leads/${lead.id}/action`,
        { completed: done, note: note ?? null },
      );
      setLeads((prev) => {
        const next = prev.map((l) => (l.id === lead.id ? updated : l));
        // Re-aplicar mismo orden que el backend: pendientes primero, score desc
        return next.sort((a, b) => {
          const aDone = a.action_completed_at ? 1 : 0;
          const bDone = b.action_completed_at ? 1 : 0;
          if (aDone !== bDone) return aDone - bDone;
          return (b.score ?? 0) - (a.score ?? 0);
        });
      });
      if (selected?.id === lead.id) setSelected(updated);
    } finally {
      setTogglingId(null);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-10">
        <div className="w-5 h-5 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (leads.length === 0) {
    return (
      <div className="text-center py-10 text-gray-400">
        <p className="text-3xl mb-2">📭</p>
        <p className="text-sm">Todavía no hay leads para esta campaña.</p>
        <p className="text-xs mt-1">Los leads aparecen cuando alguien rellena el formulario de la landing.</p>
      </div>
    );
  }

  const counts = {
    all: leads.length,
    pending: leads.filter((l) => !l.action_completed_at).length,
    done: leads.filter((l) => l.action_completed_at).length,
    hot: leads.filter((l) => l.segment === "hot").length,
    warm: leads.filter((l) => l.segment === "warm").length,
    cold: leads.filter((l) => l.segment === "cold").length,
  };

  function applyFilter(l: Lead): boolean {
    if (filter === "all") return true;
    if (filter === "pending") return !l.action_completed_at;
    if (filter === "done") return !!l.action_completed_at;
    return l.segment === filter;
  }

  const filtered = leads.filter(applyFilter);
  const avgScore =
    leads.reduce((acc, l) => acc + (l.score ?? 0), 0) / leads.length;

  return (
    <div className="space-y-4">
      {/* KPIs */}
      <div className="grid grid-cols-4 gap-2">
        {[
          { label: "Total", value: leads.length, color: "bg-gray-50 text-gray-700" },
          { label: "🔥 Hot", value: counts.hot, color: "bg-red-50 text-red-700" },
          { label: "🌤 Warm", value: counts.warm, color: "bg-amber-50 text-amber-700" },
          { label: "🧊 Cold", value: counts.cold, color: "bg-gray-50 text-gray-500" },
        ].map((k) => (
          <div key={k.label} className={`rounded-xl p-3 text-center ${k.color}`}>
            <p className="text-lg font-bold">{k.value}</p>
            <p className="text-xs opacity-70">{k.label}</p>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between flex-wrap gap-2">
        <p className="text-xs text-gray-400">
          Score medio: <span className="font-semibold text-gray-700">{avgScore.toFixed(0)}/100</span>
          {" · "}
          <span className="text-amber-600 font-medium">{counts.pending} pendientes</span>
          {" · "}
          <span className="text-green-600 font-medium">{counts.done} hechos</span>
        </p>
        <div className="flex bg-gray-100 rounded-lg p-1 gap-1 flex-wrap">
          {(
            [
              { id: "pending", label: "⏳ Pendientes" },
              { id: "done", label: "✓ Hechos" },
              { id: "all", label: "Todos" },
              { id: "hot", label: "🔥 Hot" },
              { id: "warm", label: "🌤 Warm" },
              { id: "cold", label: "🧊 Cold" },
            ] as const
          ).map((f) => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors whitespace-nowrap ${
                filter === f.id ? "bg-white text-gray-800 shadow-sm" : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tabla */}
      <div className="overflow-x-auto rounded-xl border border-gray-200">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="w-8 px-2 py-2.5"></th>
              <th className="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Lead</th>
              <th className="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Score</th>
              <th className="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Acción recomendada</th>
              <th className="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Pipeline</th>
              <th className="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Secuencia</th>
              <th className="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Fecha</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.map((lead) => {
              const done = !!lead.action_completed_at;
              const loading = togglingId === lead.id;
              return (
                <tr
                  key={lead.id}
                  className={`transition-colors ${
                    done
                      ? "bg-gray-50/40 opacity-60 hover:opacity-100"
                      : "hover:bg-brand-50/40"
                  }`}
                >
                  {/* Toggle hecho */}
                  <td className="px-2 py-3 text-center">
                    <button
                      disabled={loading}
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleLead(lead, !done);
                      }}
                      title={done ? "Marcar pendiente" : "Marcar hecho"}
                      className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                        done
                          ? "bg-green-500 border-green-500 text-white hover:bg-green-600"
                          : "border-gray-300 hover:border-brand-500 hover:bg-brand-50"
                      } ${loading ? "opacity-50 cursor-wait" : ""}`}
                    >
                      {done && <span className="text-xs leading-none">✓</span>}
                    </button>
                  </td>

                  <td
                    onClick={() => setSelected(lead)}
                    className="px-3 py-3 max-w-[180px] cursor-pointer"
                  >
                    <p
                      className={`font-medium truncate ${
                        done ? "text-gray-400 line-through" : "text-gray-800"
                      }`}
                    >
                      {lead.email}
                    </p>
                    <p className="text-xs text-gray-400 truncate">
                      {lead.nombre ?? ""}
                      {lead.empresa ? ` · ${lead.empresa}` : ""}
                    </p>
                    {done && lead.action_note && (
                      <p className="text-[11px] text-green-700 truncate mt-0.5">
                        💬 {lead.action_note}
                      </p>
                    )}
                  </td>
                  <td
                    onClick={() => setSelected(lead)}
                    className="px-3 py-3 cursor-pointer"
                  >
                    <ScoreBadge score={lead.score} segment={lead.segment} />
                  </td>
                  <td
                    onClick={() => setSelected(lead)}
                    className="px-3 py-3 max-w-[200px] cursor-pointer"
                  >
                    {done ? (
                      <span className="inline-flex items-center gap-1 text-xs text-green-700 font-medium">
                        ✅ Completada
                      </span>
                    ) : lead.recommended_action ? (
                      <div className="flex items-center gap-1.5">
                        <span>{lead.recommended_action.icon}</span>
                        <span className="text-xs font-medium text-gray-700 truncate">
                          {lead.recommended_action.label}
                        </span>
                      </div>
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                  <td
                    onClick={() => setSelected(lead)}
                    className="px-3 py-3 cursor-pointer"
                  >
                    <LeadStatusBadge status={lead.lead_status} />
                    {lead.closed_value != null && (
                      <p className="text-[10px] text-green-600 font-semibold mt-0.5">€{lead.closed_value}</p>
                    )}
                  </td>
                  <td
                    onClick={() => setSelected(lead)}
                    className="px-3 py-3 min-w-[160px] cursor-pointer"
                  >
                    <SequenceProgress lead={lead} />
                  </td>
                  <td
                    onClick={() => setSelected(lead)}
                    className="px-3 py-3 text-xs text-gray-400 whitespace-nowrap cursor-pointer"
                  >
                    {new Date(lead.created_at).toLocaleDateString("es-ES", {
                      day: "2-digit",
                      month: "short",
                    })}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {filtered.length === 0 && filter !== "all" && (
        <p className="text-center text-xs text-gray-400 py-4">
          No hay leads en este filtro.
        </p>
      )}

      {selected && (
        <LeadDetail
          lead={selected}
          onClose={() => setSelected(null)}
          onToggle={(done, note) => toggleLead(selected, done, note)}
          onPipelineUpdate={updatePipeline}
        />
      )}
    </div>
  );
}
