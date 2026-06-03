import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import type { Plan } from "../../store/plansStore";
import { usePlansStore } from "../../store/plansStore";
import { useAuthStore } from "../../store/authStore";

type FunnelType = "instant_form" | "landing_direct" | "landing_lm" | "landing_lm_direct" | "external_url";
type SaleType = "call" | "payment";

interface FunnelOption {
  id: FunnelType;
  title: string;
  description: string;
  icon: string;
  needsSaleType: boolean;
  needsRedirectUrl: boolean;
  redirectLabel?: string;
  redirectPlaceholder?: string;
}

const OPTIONS: FunnelOption[] = [
  {
    id: "instant_form",
    title: "Formulario instantáneo Meta",
    description: "El usuario llena el form sin salir de Meta. Ideal para captar leads rápido sin landing.",
    icon: "⚡",
    needsSaleType: false,
    needsRedirectUrl: false,
  },
  {
    id: "landing_direct",
    title: "Landing de venta directa",
    description: "Una página que lleva al usuario directo a tu pricing o checkout. Sin form.",
    icon: "🎯",
    needsSaleType: false,
    needsRedirectUrl: true,
    redirectLabel: "URL de pricing o checkout",
    redirectPlaceholder: "https://tudominio.com/pricing",
  },
  {
    id: "landing_lm",
    title: "Landing lead magnet + email nurturing",
    description: "Entrega un PDF gratis, nutre por email/WhatsApp y cierra con tu URL de venta externa.",
    icon: "📥",
    needsSaleType: true,
    needsRedirectUrl: true,
  },
  {
    id: "landing_lm_direct",
    title: "Lead magnet + landing de venta propia",
    description: "Captura con PDF gratis, nutre por email/WhatsApp y cierra en una landing de venta que generamos.",
    icon: "🚀",
    needsSaleType: true,
    needsRedirectUrl: true,
  },
  {
    id: "external_url",
    title: "URL externa directa",
    description: "Los anuncios llevan al usuario directo a tu web, tienda o landing ya existente. Sin generar nada.",
    icon: "🔗",
    needsSaleType: false,
    needsRedirectUrl: true,
    redirectLabel: "URL de destino",
    redirectPlaceholder: "https://tudominio.com",
  },
];

interface Props {
  plan: Plan;
}

function getRecommendedFunnel(tipoOferta: string | null): FunnelType | null {
  switch (tipoOferta) {
    case "prueba_gratuita": return "landing_direct";
    case "lanzamiento": return "landing_lm_direct";
    case "descuento_limitado": return "landing_lm_direct";
    case "evergreen": return "landing_lm";
    default: return null;
  }
}

type AbMode = "ab_classic" | "multi_angle";

interface AngleHistorySummary {
  by_business_type: Record<string, { angle: string; total: number; win_rate: number }[]>;
}

const ANGLE_LABELS: Record<string, string> = {
  dolor: "Dolor",
  aspiracion: "Aspiración",
  miedo_urgencia: "Miedo/Urgencia",
  social_proof: "Prueba social",
  curiosidad: "Curiosidad",
  credibilidad: "Credibilidad",
};

export function FunnelTypeSelector({ plan }: Props) {
  const { upsertPlan } = usePlansStore();
  const hasFeature = useAuthStore((s) => s.hasFeature);
  const canMultiAngle = hasFeature("multi_angle");
  const canResearch = hasFeature("research_export");
  const recommended = getRecommendedFunnel(plan.tipo_oferta);
  const [selected, setSelected] = useState<FunnelType | null>(recommended);
  const [saleType, setSaleType] = useState<SaleType>("call");
  const [redirectUrl, setRedirectUrl] = useState("");
  const [abMode, setAbMode] = useState<AbMode>("ab_classic");
  const [numAngles, setNumAngles] = useState(3);
  const [angleHistory, setAngleHistory] = useState<{ angle: string; win_rate: number }[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Histórico de win rate por ángulo para este tipo de negocio (feedback loop)
  useEffect(() => {
    if (!canMultiAngle) return;
    api
      .get<AngleHistorySummary>("/analytics/angle-performance/summary")
      .then((res) => {
        // Combinar todos los business_type disponibles y ordenar por win rate
        const groups = Object.values(res.by_business_type ?? {});
        const flat = groups.flat().filter((a) => a.total > 0);
        flat.sort((a, b) => b.win_rate - a.win_rate);
        setAngleHistory(flat.slice(0, 6));
      })
      .catch(() => setAngleHistory([]));
  }, [canMultiAngle]);

  const selectedOpt = OPTIONS.find((o) => o.id === selected);
  // El modo de testeo aplica a cualquier funnel que genere anuncios (todos menos URL externa pura)
  const showTestMode = selected != null && selected !== "external_url";

  const handleConfirm = async () => {
    if (!selected) return;
    if (selectedOpt?.needsRedirectUrl && !redirectUrl.trim()) {
      setError("Falta la URL");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const updated = await api.post<Plan>(`/plans/${plan.id}/funnel-choice`, {
        funnel_type: selected,
        sale_type: selectedOpt?.needsSaleType ? saleType : null,
        redirect_url: selectedOpt?.needsRedirectUrl ? redirectUrl.trim() : null,
        ab_mode: showTestMode ? abMode : "ab_classic",
        num_angles: showTestMode && abMode === "multi_angle" ? numAngles : null,
      });
      upsertPlan(updated);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Error al enviar";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleResearchOnly = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const updated = await api.post<Plan>(`/plans/${plan.id}/funnel-choice`, {
        research_export: true,
      });
      upsertPlan(updated);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Error al enviar";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mt-3 border border-brand-200 bg-brand-50/50 rounded-xl p-4">
      <div className="mb-3">
        <p className="text-xs font-bold text-brand-700 uppercase tracking-wide">Elige tu funnel</p>
        <p className="text-sm text-gray-700 mt-0.5">
          El copy está listo. Ahora elige cómo capturar y convertir clientes.
        </p>
      </div>

      <div className="space-y-2">
        {OPTIONS.map((opt) => (
          <button
            key={opt.id}
            onClick={() => setSelected(opt.id)}
            className={`w-full text-left rounded-lg border-2 p-3 transition-all ${
              selected === opt.id
                ? "border-brand-500 bg-white"
                : "border-gray-200 bg-white hover:border-brand-300"
            }`}
          >
            <div className="flex items-start gap-2.5">
              <span className="text-xl">{opt.icon}</span>
              <div className="flex-1">
                <div className="flex items-center gap-1.5">
                  <p className="font-semibold text-gray-900 text-sm">{opt.title}</p>
                  {opt.id === recommended && (
                    <span className="text-xs bg-brand-100 text-brand-700 font-semibold px-1.5 py-0.5 rounded">
                      Recomendado
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-600 mt-0.5">{opt.description}</p>
              </div>
              <div
                className={`w-4 h-4 rounded-full border-2 flex-shrink-0 mt-1 ${
                  selected === opt.id ? "border-brand-600 bg-brand-600" : "border-gray-300"
                }`}
              >
                {selected === opt.id && (
                  <div className="w-1.5 h-1.5 rounded-full bg-white m-auto mt-0.5" />
                )}
              </div>
            </div>
          </button>
        ))}
      </div>

      {selectedOpt?.needsSaleType && (
        <div className="mt-3 space-y-2 border-t border-brand-200 pt-3">
          <p className="text-xs font-semibold text-gray-700">¿Cómo cierras la venta?</p>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => setSaleType("call")}
              className={`text-xs rounded-lg border-2 py-2 px-3 font-medium ${
                saleType === "call"
                  ? "border-brand-500 bg-brand-500 text-white"
                  : "border-gray-200 bg-white text-gray-700"
              }`}
            >
              📞 Llamada (Calendly)
            </button>
            <button
              onClick={() => setSaleType("payment")}
              className={`text-xs rounded-lg border-2 py-2 px-3 font-medium ${
                saleType === "payment"
                  ? "border-brand-500 bg-brand-500 text-white"
                  : "border-gray-200 bg-white text-gray-700"
              }`}
            >
              💳 Pago directo
            </button>
          </div>
        </div>
      )}

      {selectedOpt?.needsRedirectUrl && (
        <div className="mt-3 space-y-1">
          <label className="text-xs font-semibold text-gray-700 block">
            {selectedOpt.redirectLabel ||
              (saleType === "call" ? "URL de Calendly" : "URL de checkout/pago")}
          </label>
          <input
            type="url"
            value={redirectUrl}
            onChange={(e) => setRedirectUrl(e.target.value)}
            placeholder={
              selectedOpt.redirectPlaceholder ||
              (saleType === "call"
                ? "https://calendly.com/tu-usuario/llamada"
                : "https://tudominio.com/checkout")
            }
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
          />
        </div>
      )}

      {showTestMode && (
        <div className="mt-3 space-y-2 border-t border-brand-200 pt-3">
          <p className="text-xs font-semibold text-gray-700">Modo de testeo</p>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => setAbMode("ab_classic")}
              className={`text-left text-xs rounded-lg border-2 py-2 px-3 font-medium ${
                abMode === "ab_classic"
                  ? "border-brand-500 bg-white"
                  : "border-gray-200 bg-white text-gray-700"
              }`}
            >
              <span className="block font-semibold text-gray-900">A/B clásico</span>
              <span className="block text-gray-600 mt-0.5">2 variantes de copy de 1 ángulo.</span>
            </button>
            <button
              onClick={() => canMultiAngle && setAbMode("multi_angle")}
              disabled={!canMultiAngle}
              className={`relative text-left text-xs rounded-lg border-2 py-2 px-3 font-medium ${
                !canMultiAngle
                  ? "border-gray-200 bg-gray-50 opacity-70 cursor-not-allowed"
                  : abMode === "multi_angle"
                  ? "border-brand-500 bg-white"
                  : "border-gray-200 bg-white text-gray-700"
              }`}
            >
              <span className="block font-semibold text-gray-900">Multi-Angle</span>
              <span className="block text-gray-600 mt-0.5">N ángulos en paralelo, gana presupuesto el mejor.</span>
              {!canMultiAngle && (
                <span className="inline-block mt-1 text-[10px] bg-amber-100 text-amber-700 font-semibold px-1.5 py-0.5 rounded">
                  Disponible en Growth
                </span>
              )}
            </button>
          </div>

          {abMode === "multi_angle" && canMultiAngle && (
            <>
              <div className="flex items-center gap-2 pt-1">
                <label className="text-xs font-semibold text-gray-700">Nº de ángulos</label>
                <select
                  value={numAngles}
                  onChange={(e) => setNumAngles(Number(e.target.value))}
                  className="border border-gray-300 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                >
                  {[2, 3, 4, 5, 6].map((n) => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
                <span className="text-xs text-gray-500">Recomendado: 3-6</span>
              </div>

              {angleHistory.length > 0 && (
                <div className="pt-1">
                  <p className="text-[11px] text-gray-500 mb-1">Histórico — priorizaremos los de mejor win rate:</p>
                  <div className="flex flex-wrap gap-1.5">
                    {angleHistory.map((a) => (
                      <span
                        key={a.angle}
                        className="text-[10px] bg-brand-50 text-brand-700 border border-brand-200 px-1.5 py-0.5 rounded-full"
                      >
                        {ANGLE_LABELS[a.angle] || a.angle} · {a.win_rate}% win
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}

      <button
        onClick={handleConfirm}
        disabled={!selected || submitting}
        className="mt-3 w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white text-sm font-medium py-2 rounded-lg transition-colors"
      >
        {submitting ? "Configurando..." : "Confirmar funnel y continuar"}
      </button>

      <div className="mt-3 border-t border-brand-200 pt-3">
        <button
          onClick={handleResearchOnly}
          disabled={submitting || !canResearch}
          className="w-full text-left rounded-lg border-2 border-dashed border-gray-300 bg-white hover:border-brand-300 p-3 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <p className="font-semibold text-gray-900 text-sm">🔍 Solo quiero el research y los ángulos</p>
          <p className="text-xs text-gray-600 mt-0.5">
            Explora el ICP y los 6 ángulos en la web. Expórtalos en PDF cuando quieras.
          </p>
          {!canResearch && (
            <span className="inline-block mt-1 text-[10px] bg-amber-100 text-amber-700 font-semibold px-1.5 py-0.5 rounded">
              Disponible en Starter+
            </span>
          )}
        </button>
      </div>
    </div>
  );
}
