import { useEffect, useState } from "react";
import type { AgentTask } from "../../store/tasksStore";
import { useTasksStore } from "../../store/tasksStore";
import { api } from "../../lib/api";

const STATUS_ICON: Record<AgentTask["status"], string> = {
  pending: "⏳",
  running: "⚙️",
  completed: "✅",
  failed: "❌",
};

const STATUS_LABEL: Record<AgentTask["status"], string> = {
  pending: "Pendiente",
  running: "Ejecutando...",
  completed: "Completado",
  failed: "Error",
};

function OutputModal({ task, onClose }: { task: AgentTask; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-white/90 backdrop-blur-2xl rounded-2xl shadow-glass-lg w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <div>
            <h3 className="font-semibold text-gray-900">{task.agent_name}</h3>
            <p className="text-xs text-gray-400">{task.tool_name}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>
        <div className="overflow-y-auto p-4 flex-1">
          <OutputRenderer output={task.output} />
        </div>
      </div>
    </div>
  );
}

function OutputRenderer({ output }: { output: Record<string, unknown> | null }) {
  if (!output) return <p className="text-gray-400 text-sm">Sin output</p>;

  if (output.copies && Array.isArray(output.copies)) {
    return (
      <div className="space-y-4">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Copies generados</p>
        {(output.copies as Array<{ hook: string; body: string; cta: string; score: number; angle?: string; image_url?: string }>).map((copy, i) => (
          <div key={i} className="border border-gray-200 rounded-xl overflow-hidden">
            {copy.image_url && (
              <img
                src={copy.image_url}
                alt={`Creativo variante ${i + 1}`}
                className="w-full aspect-square object-cover"
              />
            )}
            <div className="p-3 space-y-1">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-gray-400">Variante {i + 1}</span>
                  {copy.angle && (
                    <span className="text-xs bg-brand-50 text-brand-600 px-1.5 py-0.5 rounded-full">{copy.angle}</span>
                  )}
                </div>
                <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">
                  Score: {copy.score}/10
                </span>
              </div>
              <p className="font-semibold text-gray-900 text-sm">{copy.hook}</p>
              <p className="text-gray-600 text-sm">{copy.body}</p>
              <p className="text-brand-600 text-sm font-medium">→ {copy.cta}</p>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (output.emails && Array.isArray(output.emails)) {
    return (
      <div className="space-y-4">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Secuencia de emails</p>
        {(output.emails as Array<{ subject: string; preview: string; body: string; send_delay_days: number }>).map((email, i) => (
          <div key={i} className="border border-gray-200 rounded-xl p-3 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">Email {i + 1}</span>
              <span className="text-xs text-gray-400">Día {email.send_delay_days}</span>
            </div>
            <p className="font-semibold text-gray-900 text-sm">{email.subject}</p>
            <p className="text-gray-400 text-xs italic">{email.preview}</p>
            <p className="text-gray-600 text-sm whitespace-pre-line">{email.body}</p>
          </div>
        ))}
      </div>
    );
  }

  if (output.headline) {
    const lp = output as { headline: string; subheadline: string; benefits: string[]; cta: string; social_proof: string };
    return (
      <div className="space-y-3">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Copy de landing page</p>
        <div className="space-y-2">
          <p className="text-xl font-bold text-gray-900">{lp.headline}</p>
          <p className="text-gray-600">{lp.subheadline}</p>
          <ul className="space-y-1">
            {lp.benefits?.map((b, i) => <li key={i} className="text-sm text-gray-700">✓ {b}</li>)}
          </ul>
          <p className="text-brand-600 font-medium">{lp.cta}</p>
          <p className="text-gray-400 text-sm italic">{lp.social_proof}</p>
        </div>
      </div>
    );
  }

  if (output.pain_points && Array.isArray(output.pain_points)) {
    const r = output as {
      pain_points: Array<{ phrase: string; frequency: string; insight: string }>;
      competitors: Array<{ name: string; value_prop: string; weakness: string }>;
      audience_language: string[];
      icp: {
        demographics: string;
        psychographics: string;
        behaviors: string[];
        objections: string[];
        trigger_events: string[];
      } | null;
      copy_angles: Array<{ angle: string; rationale: string; hook_example: string }>;
      key_insight: string;
    };

    const ANGLE_COLORS: Record<string, string> = {
      dolor: "bg-red-50 border-red-200 text-red-800",
      aspiracion: "bg-emerald-50 border-emerald-200 text-emerald-800",
      miedo_urgencia: "bg-orange-50 border-orange-200 text-orange-800",
      social_proof: "bg-blue-50 border-blue-200 text-blue-800",
      curiosidad: "bg-violet-50 border-violet-200 text-violet-800",
      credibilidad: "bg-slate-50 border-slate-200 text-slate-800",
    };

    return (
      <div className="space-y-5">
        {r.key_insight && (
          <div className="bg-brand-50 border border-brand-200 rounded-xl p-3">
            <p className="text-xs font-semibold text-brand-600 mb-1">KEY INSIGHT</p>
            <p className="text-sm text-brand-900">{r.key_insight}</p>
          </div>
        )}

        {r.icp && (
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">ICP — Cliente Ideal</p>
            <div className="border border-gray-200 rounded-xl overflow-hidden divide-y divide-gray-100">
              <div className="p-2.5">
                <p className="text-xs font-medium text-gray-500 mb-0.5">Demografía</p>
                <p className="text-sm text-gray-800">{r.icp.demographics}</p>
              </div>
              <div className="p-2.5">
                <p className="text-xs font-medium text-gray-500 mb-0.5">Psicografía</p>
                <p className="text-sm text-gray-800">{r.icp.psychographics}</p>
              </div>
              {r.icp.behaviors?.length > 0 && (
                <div className="p-2.5">
                  <p className="text-xs font-medium text-gray-500 mb-1">Comportamientos</p>
                  <ul className="space-y-0.5">
                    {r.icp.behaviors.map((b, i) => (
                      <li key={i} className="text-xs text-gray-700">→ {b}</li>
                    ))}
                  </ul>
                </div>
              )}
              {r.icp.objections?.length > 0 && (
                <div className="p-2.5">
                  <p className="text-xs font-medium text-gray-500 mb-1">Objeciones principales</p>
                  <ul className="space-y-0.5">
                    {r.icp.objections.map((o, i) => (
                      <li key={i} className="text-xs text-red-600">✗ {o}</li>
                    ))}
                  </ul>
                </div>
              )}
              {r.icp.trigger_events?.length > 0 && (
                <div className="p-2.5">
                  <p className="text-xs font-medium text-gray-500 mb-1">Trigger events</p>
                  <ul className="space-y-0.5">
                    {r.icp.trigger_events.map((t, i) => (
                      <li key={i} className="text-xs text-gray-700">⚡ {t}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Pain points reales</p>
          <div className="space-y-2">
            {r.pain_points?.map((pp, i) => (
              <div key={i} className="border border-gray-200 rounded-lg p-2.5">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-gray-800">"{pp.phrase}"</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded-full ${pp.frequency === "alta" ? "bg-red-100 text-red-700" : pp.frequency === "media" ? "bg-yellow-100 text-yellow-700" : "bg-gray-100 text-gray-600"}`}>
                    {pp.frequency}
                  </span>
                </div>
                <p className="text-xs text-gray-500">{pp.insight}</p>
              </div>
            ))}
          </div>
        </div>

        {r.competitors?.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Competidores</p>
            <div className="space-y-2">
              {r.competitors.map((c, i) => (
                <div key={i} className="border border-gray-200 rounded-lg p-2.5">
                  <p className="text-sm font-semibold text-gray-800">{c.name}</p>
                  <p className="text-xs text-gray-600">✓ {c.value_prop}</p>
                  <p className="text-xs text-red-500">✗ {c.weakness}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {r.copy_angles?.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Ángulos de copy</p>
            <div className="space-y-2">
              {r.copy_angles.map((a, i) => {
                const colorClass = ANGLE_COLORS[a.angle] ?? "bg-gray-50 border-gray-200 text-gray-800";
                return (
                  <div key={i} className={`border rounded-lg p-2.5 ${colorClass}`}>
                    <p className="text-xs font-bold uppercase tracking-wide mb-0.5">{a.angle.replace("_", " ")}</p>
                    <p className="text-xs opacity-75 mb-1">{a.rationale}</p>
                    <p className="text-xs font-medium italic">"{a.hook_example}"</p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {r.audience_language?.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Lenguaje de la audiencia</p>
            <div className="flex flex-wrap gap-1.5">
              {r.audience_language.map((phrase, i) => (
                <span key={i} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-lg">"{phrase}"</span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  if (output.status === "ready_to_publish" && output.campaign_json) {
    const campaign = output.campaign_json as Record<string, unknown>;
    const budget = output.budget as { monthly_eur: number; daily_eur: number; summary: string };
    const interests = (output.interests_mapped as Array<{ name: string; id: string; relevance: string }>) ?? [];
    const ads = (campaign.ads as Array<{ variant: string; copy_score: number; copy_angle: string; landing_url: string }>) ?? [];

    return (
      <div className="space-y-5">
        <div className="bg-green-50 border border-green-200 rounded-xl p-3">
          <p className="text-xs font-semibold text-green-700 mb-1">CAMPAÑA LISTA PARA PUBLICAR</p>
          <p className="text-sm text-green-900">{output.note as string}</p>
        </div>

        {/* Presupuesto */}
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Presupuesto</p>
          <div className="bg-gray-50 rounded-xl p-3 flex gap-6">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">€{budget?.monthly_eur}</p>
              <p className="text-xs text-gray-400">/ mes</p>
            </div>
            <div className="flex items-center text-gray-300 text-xl">÷</div>
            <div className="text-center">
              <p className="text-2xl font-bold text-brand-600">€{budget?.daily_eur?.toFixed(2)}</p>
              <p className="text-xs text-gray-400">/ día</p>
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-1">{budget?.summary}</p>
        </div>

        {/* Ads A/B */}
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Split test A/B</p>
          <div className="grid grid-cols-2 gap-2">
            {ads.map((ad) => (
              <div key={ad.variant} className="border border-gray-200 rounded-xl p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-bold text-gray-800">Variante {ad.variant}</span>
                  <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full">Score {ad.copy_score}/10</span>
                </div>
                <p className="text-xs text-brand-600 mb-1">{ad.copy_angle}</p>
                <p className="text-xs text-gray-400 truncate">{ad.landing_url}</p>
              </div>
            ))}
          </div>
        </div>

        {interests.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Intereses de targeting ({interests.length})</p>
            <div className="flex flex-wrap gap-1.5">
              {interests.map((interest, idx) => (
                <span key={idx} className={`text-xs px-2 py-1 rounded-full ${interest.relevance === "alta" ? "bg-brand-100 text-brand-700" : "bg-gray-100 text-gray-600"}`}>
                  {interest.name}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* JSON completo */}
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">JSON de campaña completo</p>
          <pre className="text-xs text-gray-700 bg-gray-50 rounded-xl p-3 overflow-x-auto max-h-64 whitespace-pre-wrap">
            {JSON.stringify(campaign, null, 2)}
          </pre>
        </div>

        {!!output.requires_meta_keys && (
          <p className="text-xs text-amber-600 bg-amber-50 rounded-xl p-3">
            ⚠️ Configura tus Meta API keys en Ajustes para publicar esta campaña.
          </p>
        )}
      </div>
    );
  }

  if (output.landing_ids || output.variant_a) {
    return <LandingOutputRenderer output={output} />;
  }

  if (output.title && output.sections && Array.isArray(output.sections)) {
    const lm = output as {
      title: string;
      subtitle?: string;
      sections: Array<{ heading: string; body: string }>;
      pdf_url?: string;
      pdf_size_kb?: number;
      estimated_reading_minutes?: number;
    };
    return (
      <div className="space-y-3">
        <div className="bg-brand-50 border border-brand-200 rounded-xl p-3">
          <p className="text-xs font-bold text-brand-700 uppercase tracking-wide">Lead Magnet PDF</p>
          <p className="text-lg font-bold text-gray-900 mt-1">{lm.title}</p>
          {lm.subtitle && <p className="text-sm text-gray-600">{lm.subtitle}</p>}
          {lm.pdf_url && (
            <a
              href={lm.pdf_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block mt-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-3 py-1.5 rounded-lg"
            >
              📄 Descargar PDF ({lm.pdf_size_kb} KB)
            </a>
          )}
        </div>
        <div className="space-y-2">
          {lm.sections.map((s, i) => (
            <details key={i} className="border border-gray-200 rounded-lg p-2.5">
              <summary className="text-sm font-semibold text-gray-800 cursor-pointer">
                {i + 1}. {s.heading}
              </summary>
              <p className="text-xs text-gray-600 mt-2 whitespace-pre-line">{s.body}</p>
            </details>
          ))}
        </div>
      </div>
    );
  }

  if (output.rubric && Array.isArray(output.rubric)) {
    const crm = output as {
      rubric: Array<{ field: string; max_points: number }>;
      max_possible_score: number;
      segments: Record<string, string>;
    };
    return (
      <div className="space-y-3">
        <div className="bg-purple-50 border border-purple-200 rounded-xl p-3">
          <p className="text-xs font-bold text-purple-700 uppercase tracking-wide">Rúbrica CRM</p>
          <p className="text-sm text-gray-700 mt-1">Score máximo: {crm.max_possible_score}/100</p>
        </div>
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Pesos por campo</p>
          <div className="space-y-1">
            {crm.rubric.map((r, i) => (
              <div key={i} className="flex justify-between text-xs px-2 py-1 bg-gray-50 rounded">
                <span className="font-medium text-gray-700">{r.field}</span>
                <span className="text-purple-700 font-mono">+{r.max_points}</span>
              </div>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Segmentos</p>
          <div className="space-y-1">
            {Object.entries(crm.segments).map(([key, desc]) => (
              <div key={key} className="text-xs">
                <span className={`inline-block px-2 py-0.5 rounded font-bold uppercase ${
                  key === "hot" ? "bg-red-100 text-red-700" :
                  key === "warm" ? "bg-yellow-100 text-yellow-700" :
                  "bg-blue-100 text-blue-700"
                }`}>{key}</span>
                <span className="text-gray-600 ml-2">{desc}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (output.status === "pending_implementation") {
    return <p className="text-gray-400 text-sm">Este agente aún no está implementado.</p>;
  }

  return (
    <pre className="text-xs text-gray-700 bg-gray-50 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap">
      {JSON.stringify(output, null, 2)}
    </pre>
  );
}

function LandingOutputRenderer({ output }: { output: Record<string, unknown> }) {
  const landingIds = (output.landing_ids ?? {}) as Record<string, string>;
  const frontendUrl = window.location.origin;

  type VariantData = {
    headline?: string;
    subheadline?: string;
    benefits?: string[];
    cta_text?: string;
    redirect_url?: string;
  };

  const variants: Array<{ key: "a" | "b"; label: string; id: string | null; data: VariantData }> = (
    ["a", "b"] as const
  )
    .filter((k) => output[`variant_${k}`])
    .map((k) => ({
      key: k,
      label: k === "a" ? "Variante A — Emocional" : "Variante B — Racional",
      id: landingIds[k] ?? null,
      data: (output[`variant_${k}`] as VariantData) ?? {},
    }));

  const [editing, setEditing] = useState<"a" | "b" | null>(null);
  const [forms, setForms] = useState<Record<string, VariantData>>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState<string | null>(null);

  const startEdit = (v: (typeof variants)[0]) => {
    setForms((f) => ({ ...f, [v.key]: { ...v.data } }));
    setEditing(v.key);
  };

  const saveEdit = async (v: (typeof variants)[0]) => {
    setSaving(true);
    try {
      await api.patch(`/landings/${v.id}`, forms[v.key]);
      setSaved(v.key);
      setEditing(null);
      setTimeout(() => setSaved(null), 2000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Landing pages generadas</p>
      {variants.map((v) => {
        const landingUrl = v.id ? `${frontendUrl}/landing/${v.id}${v.key === "b" ? "?v=b" : ""}` : null;
        const isEditing = editing === v.key;
        const form = forms[v.key] ?? v.data;

        return (
          <div key={v.key} className="border border-gray-200 rounded-xl overflow-hidden">
            <div className="bg-gray-50 px-3 py-2 flex items-center justify-between border-b border-gray-100">
              <span className="text-xs font-semibold text-gray-700">{v.label}</span>
              <div className="flex items-center gap-2">
                {saved === v.key && <span className="text-xs text-green-600">Guardado ✓</span>}
                {v.id && (
                  <button
                    onClick={() => (isEditing ? setEditing(null) : startEdit(v))}
                    className="text-xs text-brand-600 hover:underline"
                  >
                    {isEditing ? "Cancelar" : "Editar"}
                  </button>
                )}
                {landingUrl ? (
                  <a
                    href={landingUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs bg-brand-600 text-white px-2.5 py-1 rounded-lg hover:bg-brand-700 transition-colors"
                  >
                    Ver landing →
                  </a>
                ) : (
                  <span className="text-xs text-gray-400">Sin URL (plan antiguo)</span>
                )}
              </div>
            </div>

            {isEditing ? (
              <div className="p-3 space-y-3">
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Headline</label>
                  <input
                    type="text"
                    value={(form.headline as string) ?? ""}
                    onChange={(e) => setForms((f) => ({ ...f, [v.key]: { ...form, headline: e.target.value } }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Subheadline</label>
                  <input
                    type="text"
                    value={(form.subheadline as string) ?? ""}
                    onChange={(e) => setForms((f) => ({ ...f, [v.key]: { ...form, subheadline: e.target.value } }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">CTA</label>
                  <input
                    type="text"
                    value={(form.cta_text as string) ?? ""}
                    onChange={(e) => setForms((f) => ({ ...f, [v.key]: { ...form, cta_text: e.target.value } }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                  />
                </div>
                {output.campaign_type === "direct_sale" && (
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">URL de redirección</label>
                    <input
                      type="url"
                      value={(form.redirect_url as string) ?? ""}
                      onChange={(e) => setForms((f) => ({ ...f, [v.key]: { ...form, redirect_url: e.target.value } }))}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                    />
                  </div>
                )}
                <button
                  onClick={() => saveEdit(v)}
                  disabled={saving}
                  className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white text-sm font-medium py-2 rounded-lg transition-colors"
                >
                  {saving ? "Guardando…" : "Guardar cambios"}
                </button>
              </div>
            ) : (
              <div className="p-3 space-y-1">
                <p className="font-semibold text-gray-900 text-sm">{v.data.headline}</p>
                <p className="text-gray-500 text-xs">{v.data.subheadline}</p>
                <ul className="mt-1 space-y-0.5">
                  {v.data.benefits?.map((b, i) => (
                    <li key={i} className="text-xs text-gray-600">✓ {b}</li>
                  ))}
                </ul>
                {landingUrl && <p className="text-xs text-gray-400 mt-1 break-all">{landingUrl}</p>}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

interface Props {
  planId: string;
  planSteps?: Array<{ agent: string; description: string; order: number }>;
  planStatus?: string;
}

export function AgentActivityFeed({ planId, planSteps = [], planStatus }: Props) {
  const { tasksByPlan, fetchTasks } = useTasksStore();
  const [selectedTask, setSelectedTask] = useState<AgentTask | null>(null);

  const tasks = tasksByPlan[planId] ?? [];
  const isActive = ["approved", "executing", "pending_copy_approval", "pending_ads_approval"].includes(planStatus ?? "") &&
    (tasks.length === 0 || tasks.some((t: AgentTask) => t.status === "pending" || t.status === "running"));

  useEffect(() => {
    fetchTasks(planId);
  }, [planId]);

  // Polling mientras el plan está activo
  useEffect(() => {
    if (!isActive) return;
    const interval = setInterval(() => fetchTasks(planId), 3000);
    return () => clearInterval(interval);
  }, [planId, isActive]);

  // Fetch final cuando el plan llega a done para capturar tareas del resume
  useEffect(() => {
    if (planStatus === "done") {
      fetchTasks(planId);
    }
  }, [planStatus, planId]);

  // Combinar steps del plan con tareas reales — mostrar todos los steps siempre
  const rows = planSteps.map((step) => {
    const task = tasks.find((t: AgentTask) => t.agent_name === step.agent);
    return { step, task };
  });

  if (rows.length === 0 && tasks.length === 0) return null;

  // Si hay steps del plan úsalos; si no, muestra solo las tareas reales
  const displayItems: Array<{ agentName: string; description: string; key: string; task: AgentTask | null }> =
    rows.length > 0
      ? rows.map((r, i) => ({
        agentName: r.task?.agent_name ?? r.step.agent,
        description: (r.task?.input?.description as string | undefined) ?? r.step.description,
        key: r.task?.id ?? `step-${i}`,
        task: r.task ?? null,
      }))
      : tasks.map((t) => ({
        agentName: t.agent_name,
        description: (t.input?.description as string | undefined) ?? t.tool_name,
        key: t.id,
        task: t,
      }));

  return (
    <>
      <div className="mt-3 border border-gray-200 rounded-xl overflow-hidden">
        <div className="bg-gray-50 px-3 py-2 border-b border-gray-100">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Actividad de agentes</p>
        </div>
        <ul className="divide-y divide-gray-100">
          {displayItems.map(({ agentName, description, key, task }) => {
            const status: AgentTask["status"] = task?.status ?? "pending";
            const isClickable = status === "completed" && !!task?.output;
            const images = status === "completed" && task?.output?.copies
              ? (task.output.copies as Array<{ image_url?: string }>).filter((c) => c.image_url)
              : [];

            return (
              <li
                key={key}
                className={`flex flex-col gap-2 px-3 py-2.5 ${isClickable ? "cursor-pointer hover:bg-gray-50" : ""}`}
                onClick={() => { if (isClickable && task) setSelectedTask(task); }}
              >
                <div className="flex items-start gap-3">
                  <span className={`text-base mt-0.5 ${status === "running" ? "animate-spin" : ""}`}>
                    {STATUS_ICON[status]}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800">{agentName}</p>
                    <p className="text-xs text-gray-400 truncate">{description}</p>
                  </div>
                  <span className={`text-xs shrink-0 ${status === "completed" ? "text-green-600" :
                      status === "failed" ? "text-red-500" :
                        status === "running" ? "text-brand-500" : "text-gray-400"
                    }`}>
                    {STATUS_LABEL[status]}
                    {isClickable && task?.output?.status !== "pending_implementation" && (
                      <span className="ml-1 text-gray-400">→ ver</span>
                    )}
                  </span>
                </div>

                {images.length > 0 && (
                  <div className="flex gap-2 ml-7">
                    {images.map((c, i) => (
                      <div key={i} className="relative group">
                        <img
                          src={c.image_url}
                          alt={`Creativo ${i + 1}`}
                          className="w-16 h-16 rounded-lg object-cover border border-gray-200"
                        />
                        <div className="absolute inset-0 bg-black/40 rounded-lg opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                          <span className="text-white text-xs font-medium">Ver</span>
                        </div>
                      </div>
                    ))}
                    <div className="flex items-center">
                      <span className="text-xs text-gray-400">{images.length} imagen{images.length > 1 ? "es" : ""} generada{images.length > 1 ? "s" : ""}</span>
                    </div>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      </div>

      {selectedTask && (
        <OutputModal task={selectedTask} onClose={() => setSelectedTask(null)} />
      )}
    </>
  );
}
