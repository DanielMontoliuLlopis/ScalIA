import { useEffect, useMemo, useState } from "react";
import { usePlansStore } from "../store/plansStore";
import { useAuthStore } from "../store/authStore";
import { useWebSocket } from "../hooks/useWebSocket";
import { ResearchModeScreen } from "./ResearchModeScreen";
import { ResearchGenerateModal } from "../components/research/ResearchGenerateModal";
import type { Plan } from "../store/plansStore";

const BUSINESS_LABELS: Record<string, string> = {
  saas: "SaaS",
  ecommerce: "Ecommerce",
  services: "Servicios",
  app: "App",
  local: "Local",
};

function businessTypeOf(plan: Plan): string | null {
  const step = (plan.steps as Array<{ business_type?: string }> | null)?.find((s) => s.business_type);
  return step?.business_type ?? null;
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("es-ES", { day: "2-digit", month: "short", year: "numeric" });
  } catch {
    return iso;
  }
}

export function ResearchLibrary() {
  const { plans, fetchPlans } = usePlansStore();
  const { features } = useAuthStore();
  const [showModal, setShowModal] = useState(false);
  const [selected, setSelected] = useState<Plan | null>(null);

  useWebSocket();

  useEffect(() => {
    fetchPlans();
  }, []);

  const researchPlans = useMemo(
    () => plans.filter((p) => p.research_export).sort((a, b) => b.created_at.localeCompare(a.created_at)),
    [plans]
  );

  // Fallback: si el WS se cae durante una generación larga (6 imágenes),
  // el evento plan_research_view se pierde. Poll mientras haya research generándose.
  const hasGenerating = researchPlans.some((p) => p.status === "executing");
  useEffect(() => {
    if (!hasGenerating) return;
    const id = setInterval(() => {
      fetchPlans();
    }, 4000);
    return () => clearInterval(id);
  }, [hasGenerating]);

  // Mantiene el drawer sincronizado con el plan actualizado (p.ej. al completar la generación)
  const selectedLive = selected ? plans.find((p) => p.id === selected.id) ?? selected : null;

  return (
    <div className="flex-1 overflow-y-auto bg-transparent">
      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Research</h1>
            <p className="text-sm text-gray-500 mt-1">
              Tu librería de research: ICP, pain points y 6 ángulos con copy e imagen.
            </p>
          </div>
          <div className="flex items-center gap-4">
            {features && (
              <span className="text-xs text-gray-500">
                Escaneos: <span className="font-semibold text-gray-800">{features.scans_remaining}</span>/
                {features.scans_per_month}
              </span>
            )}
            <button
              onClick={() => setShowModal(true)}
              className="bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg text-sm font-semibold"
            >
              + Generar nuevo
            </button>
          </div>
        </div>

        {researchPlans.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-gray-300 bg-white py-16 text-center">
            <p className="text-gray-500 text-sm">Aún no has generado ningún research.</p>
            <button
              onClick={() => setShowModal(true)}
              className="mt-4 bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg text-sm font-semibold"
            >
              Generar mi primer research
            </button>
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {researchPlans.map((plan) => {
              const bt = businessTypeOf(plan);
              const ready = plan.status === "research_view";
              const generating = plan.status === "executing";
              return (
                <button
                  key={plan.id}
                  onClick={() => ready && setSelected(plan)}
                  disabled={!ready}
                  className={`text-left rounded-2xl border bg-white p-5 transition-colors ${
                    ready ? "border-gray-200 hover:border-brand-400 cursor-pointer" : "border-gray-100 cursor-default"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    {bt && (
                      <span className="text-[10px] font-semibold uppercase tracking-wide bg-brand-50 text-brand-700 px-2 py-0.5 rounded-full">
                        {BUSINESS_LABELS[bt] ?? bt}
                      </span>
                    )}
                    {generating ? (
                      <span className="flex items-center gap-1.5 text-[11px] font-medium text-amber-600">
                        <span className="w-3 h-3 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
                        Generando…
                      </span>
                    ) : ready ? (
                      <span className="text-[11px] font-medium text-emerald-600">● Listo</span>
                    ) : (
                      <span className="text-[11px] font-medium text-gray-400">{plan.status}</span>
                    )}
                  </div>
                  <h3 className="font-semibold text-gray-900 text-sm leading-snug line-clamp-2">{plan.title}</h3>
                  <p className="mt-2 text-xs text-gray-400">{formatDate(plan.created_at)}</p>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {showModal && (
        <ResearchGenerateModal
          onClose={() => setShowModal(false)}
          onCreated={(plan) => {
            usePlansStore.getState().upsertPlan(plan);
            setShowModal(false);
          }}
        />
      )}

      {/* Drawer del research seleccionado */}
      {selectedLive && (
        <div className="fixed inset-0 z-40 flex justify-end bg-black/50" onClick={() => setSelected(null)}>
          <div
            className="w-full max-w-3xl h-full overflow-y-auto bg-[#15110e] shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sticky top-0 z-10 flex items-center justify-between bg-[#15110e] px-6 py-3 border-b border-amber-900/30">
              <span className="text-amber-100 text-sm font-medium truncate">{selectedLive.title}</span>
              <button
                onClick={() => setSelected(null)}
                className="text-amber-200/70 hover:text-amber-100 text-2xl leading-none"
              >
                ×
              </button>
            </div>
            <div className="px-4 pb-6">
              <ResearchModeScreen plan={selectedLive} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
