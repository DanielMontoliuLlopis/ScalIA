import { useState } from "react";
import { api } from "../../lib/api";
import { usePlansStore } from "../../store/plansStore";
import { ImageLightbox } from "../ui/ImageLightbox";
import type { Plan } from "../../store/plansStore";
import type { AgentTask } from "../../store/tasksStore";

interface Copy {
  hook: string;
  body: string;
  cta: string;
  score: number;
  angle?: string;
  image_url?: string;
}

interface DcoAssets {
  titles?: string[];
  bodies?: string[];
  descriptions?: string[];
  images?: string[];
}

interface Props {
  plan: Plan;
  copyTask: AgentTask;
  nextStep: number;
}

export function CopyApprovalPanel({ plan, copyTask, nextStep }: Props) {
  const { upsertPlan } = usePlansStore();
  const isDco = copyTask.output?.creative_type === "dco";
  const dcoAssets: DcoAssets = (copyTask.output?.dco_assets as DcoAssets) ?? {};
  const copies: Copy[] = (copyTask.output?.copies as Copy[]) ?? [];
  const maxSelect = plan.ab_testing ? 2 : 1;
  const [selected, setSelected] = useState<Set<number>>(
    new Set(copies.slice(0, maxSelect).map((_, i) => i))
  );
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);

  const toggle = (i: number) => {
    const next = new Set(selected);
    if (next.has(i)) {
      if (next.size > 1) next.delete(i);
    } else {
      if (next.size >= maxSelect) next.clear();
      next.add(i);
    }
    setSelected(next);
  };

  const handleContinue = async () => {
    setLoading(true);
    try {
      const updated = await api.post<Plan>(`/plans/${plan.id}/resume-copy`, {
        selected_copy_indices: isDco ? [] : Array.from(selected).sort(),
        next_step: nextStep,
      });
      upsertPlan(updated);
    } finally {
      setLoading(false);
    }
  };

  // ── Panel DCO ──────────────────────────────────────────────────────
  if (isDco) {
    const titles = dcoAssets.titles ?? [];
    const bodies = dcoAssets.bodies ?? [];
    const images = dcoAssets.images ?? [];
    return (
      <div className="mt-3 border-2 border-amber-300 bg-amber-50 rounded-xl p-4">
        <div className="mb-3">
          <div className="flex items-center gap-2 mb-0.5">
            <span className="text-base">⚡</span>
            <p className="text-sm font-semibold text-amber-900">Creativo dinámico (DCO) generado</p>
          </div>
          <p className="text-xs text-amber-700">
            Meta combinará automáticamente estos assets para hallar la mejor mezcla. No necesitas seleccionar variantes.
          </p>
        </div>

        <div className="space-y-3 mb-4">
          {/* Imágenes */}
          {images.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
                Imágenes ({images.length}) — haz clic para ampliar
              </p>
              <ImageLightbox images={images} title="Creativo DCO" />
            </div>
          )}

          {/* Titulares */}
          {titles.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
                Titulares ({titles.length})
              </p>
              <div className="space-y-1">
                {titles.map((t, i) => (
                  <div key={i} className="flex items-start gap-1.5 text-xs">
                    <span className="text-amber-500 shrink-0 font-bold">{i + 1}.</span>
                    <span className="text-gray-800">{t}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Textos principales */}
          {bodies.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
                Textos principales ({bodies.length})
              </p>
              <div className="space-y-1.5">
                {bodies.map((b, i) => (
                  <div key={i} className="flex items-start gap-1.5 text-xs">
                    <span className="text-amber-500 shrink-0 font-bold">{i + 1}.</span>
                    <span className="text-gray-600 leading-relaxed">{b}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <button
          onClick={handleContinue}
          disabled={loading}
          className="w-full bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-white font-medium py-2 rounded-xl text-sm transition-colors"
        >
          {loading ? "Continuando…" : "Aprobar assets DCO y continuar →"}
        </button>
      </div>
    );
  }

  // ── Panel clásico (variante A/B) ────────────────────────────────────
  return (
    <div className="mt-3 border-2 border-brand-300 bg-brand-50 rounded-xl p-4">
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-sm font-semibold text-brand-900">Selecciona los copies para la campaña</p>
          <p className="text-xs text-brand-600">
            {plan.ab_testing
              ? `Elige exactamente 2 variantes (${selected.size}/2 seleccionadas)`
              : `Elige 1 copy (${selected.size}/1 seleccionado)`}
          </p>
        </div>
      </div>

      <div className="space-y-2 mb-4">
        {copies.map((copy, i) => {
          const isSelected = selected.has(i);
          return (
            <div
              key={i}
              onClick={() => toggle(i)}
              className={`rounded-xl border-2 cursor-pointer transition-all overflow-hidden ${
                isSelected
                  ? "border-brand-500 bg-white shadow-sm"
                  : "border-gray-200 bg-white/60 opacity-70"
              }`}
            >
              <div className="flex gap-3 p-3">
                <div className={`mt-0.5 w-5 h-5 rounded-full border-2 flex-shrink-0 flex items-center justify-center ${
                  isSelected ? "border-brand-500 bg-brand-500" : "border-gray-300"
                }`}>
                  {isSelected && <span className="text-white text-xs font-bold">✓</span>}
                </div>
                {copy.image_url && (
                  <img
                    src={copy.image_url}
                    alt={`Variante ${i + 1}`}
                    className="w-14 h-14 rounded-lg object-cover flex-shrink-0"
                  />
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-semibold text-gray-700">Variante {i + 1}</span>
                    {copy.angle && (
                      <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full">{copy.angle}</span>
                    )}
                    <span className="ml-auto text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full font-medium">
                      {copy.score}/10
                    </span>
                  </div>
                  <p className="text-sm font-medium text-gray-900 truncate">{copy.hook}</p>
                  {expanded === i && (
                    <>
                      <p className="text-xs text-gray-500 mt-1">{copy.body}</p>
                      <p className="text-xs text-brand-600 mt-1 font-medium">→ {copy.cta}</p>
                    </>
                  )}
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); setExpanded(expanded === i ? null : i); }}
                  className="text-gray-400 hover:text-gray-600 text-xs shrink-0 self-start mt-0.5"
                >
                  {expanded === i ? "▲" : "▼"}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      <button
        onClick={handleContinue}
        disabled={loading || selected.size !== maxSelect}
        className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-medium py-2 rounded-xl text-sm transition-colors"
      >
        {loading
          ? "Continuando…"
          : plan.ab_testing
          ? "Continuar con estas 2 variantes →"
          : "Continuar con este copy →"}
      </button>
    </div>
  );
}
