import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../lib/api";
import { useAuthStore } from "../store/authStore";

type PlanId = "starter" | "growth" | "agency";
type ResearchId = "research_10" | "research_100";
type AnyPlanId = PlanId | ResearchId;

interface PlanInfo {
  id: PlanId;
  name: string;
  amount: number;
  founder_amount: number;
  currency: string;
  interval: string;
  trial_days: number;
  active_campaigns_limit: number;
  team_seats: number;
  features: string[];
}

interface ResearchPlanInfo {
  id: ResearchId;
  name: string;
  description: string;
  amount: number;
  currency: string;
  scans_per_month: number;
  price_per_scan: number;
}

interface FounderStatus {
  spots_total: number;
  spots_taken: number;
  spots_left: number;
  is_open: boolean;
}

const FEATURES: Record<PlanId, { tagline: string; bullets: string[]; highlight: boolean }> = {
  starter: {
    tagline: "Para empezar y validar tu primera oferta",
    highlight: false,
    bullets: [
      "1 campaña activa",
      "Copies y landing pages con IA",
      "Lead magnets en PDF",
      "Secuencias de email + WhatsApp",
      "CRM con scoring automático",
      "Publicación directa en Meta Ads",
    ],
  },
  growth: {
    tagline: "Para negocios que escalan y testean ofertas",
    highlight: true,
    bullets: [
      "3 campañas activas simultáneas",
      "Todo lo de Starter",
      "Tests de oferta A/B",
      "Optimización automática 24h",
      "Equipo hasta 3 personas con roles",
      "Soporte estándar",
    ],
  },
  agency: {
    tagline: "Para agencias y equipos que gestionan varias marcas",
    highlight: false,
    bullets: [
      "Campañas activas ilimitadas",
      "Todo lo de Growth",
      "Multi-cuenta de Meta Ads",
      "Reportes white-label",
      "Equipo ilimitado con roles",
      "Soporte prioritario en menos de 2h",
    ],
  },
};

const ORDER: PlanId[] = ["starter", "growth", "agency"];
const RESEARCH_ORDER: ResearchId[] = ["research_10", "research_100"];

type Track = "platform" | "research";

export function Onboarding() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { user, logout } = useAuthStore();
  const preselectedPlan = params.get("plan") as AnyPlanId | null;
  const canceled = params.get("canceled");

  const [plans, setPlans] = useState<PlanInfo[]>([]);
  const [researchPlans, setResearchPlans] = useState<ResearchPlanInfo[]>([]);
  const [founder, setFounder] = useState<FounderStatus | null>(null);
  const [loading, setLoading] = useState<AnyPlanId | null>(null);
  const [error, setError] = useState("");
  const [track, setTrack] = useState<Track>("research");

  useEffect(() => {
    api.get<PlanInfo[]>("/billing/plans").then(setPlans).catch(() => setError("Error cargando planes"));
    api
      .get<ResearchPlanInfo[]>("/billing/research-plans")
      .then(setResearchPlans)
      .catch(() => setResearchPlans([]));
    api.get<FounderStatus>("/billing/founder-status").then(setFounder).catch(() => setFounder(null));
  }, []);

  const founderOpen = founder?.is_open ?? false;

  const handleSelect = async (planId: AnyPlanId) => {
    setLoading(planId);
    setError("");
    try {
      const { url } = await api.post<{ url: string }>("/billing/checkout-session", {
        plan: planId,
        founder: founderOpen,
      });
      window.location.href = url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear sesión de pago");
      setLoading(null);
    }
  };

  const formatPrice = (amount: number) => `${(amount / 100).toFixed(0)}€`;
  const ordered = ORDER.map((id) => plans.find((p) => p.id === id)).filter(Boolean) as PlanInfo[];
  const orderedResearch = RESEARCH_ORDER.map((id) =>
    researchPlans.find((p) => p.id === id)
  ).filter(Boolean) as ResearchPlanInfo[];

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-50 via-white to-violet-50 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <div className="text-xl font-bold mb-4">
            Scal<span className="text-brand-600">IA</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
            {user?.full_name ? `${user.full_name.split(" ")[0]}, elige tu plan` : "Elige tu plan"}
          </h1>
          <p className="mt-3 text-gray-600">
            Suscripción mensual. Cancela cuando quieras desde Ajustes.
          </p>
          {canceled && (
            <p className="mt-3 inline-block bg-amber-50 text-amber-800 text-sm px-3 py-1 rounded-full">
              Has cancelado el pago. Selecciona un plan cuando quieras continuar.
            </p>
          )}
        </div>

        {/* Toggle de línea de producto */}
        <div className="flex justify-center mb-10">
          <div className="inline-flex bg-white border border-gray-200 rounded-full p-1 shadow-sm">
            <button
              onClick={() => setTrack("research")}
              className={`px-5 py-2 rounded-full text-sm font-medium transition-colors ${
                track === "research" ? "bg-slate-900 text-white" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Research Mode
            </button>
            <button
              onClick={() => setTrack("platform")}
              className={`px-5 py-2 rounded-full text-sm font-medium transition-colors inline-flex items-center gap-2 ${
                track === "platform" ? "bg-brand-600 text-white" : "text-gray-400 hover:text-gray-600"
              }`}
            >
              Plataforma completa
              <span
                className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded-full ${
                  track === "platform" ? "bg-white/20 text-white" : "bg-amber-100 text-amber-700"
                }`}
              >
                Pronto
              </span>
            </button>
          </div>
        </div>

        {track === "platform" && (
          <div className="max-w-3xl mx-auto rounded-3xl bg-gradient-to-br from-slate-900 to-slate-800 text-white p-10 md:p-14 text-center shadow-2xl">
            <div className="text-xs font-semibold tracking-widest text-amber-400 uppercase">
              Próximamente
            </div>
            <h3 className="text-2xl md:text-3xl font-extrabold mt-3">
              La plataforma completa llega pronto
            </h3>
            <p className="text-slate-300 text-sm mt-4 max-w-xl mx-auto">
              El flujo agéntico end-to-end: research → copy → funnel → ads → leads → optimización.
              Mientras lo terminamos, empieza con Research Mode y quédate con el output más valioso:
              ICP, pain points y los 6 ángulos.
            </p>
            <button
              onClick={() => setTrack("research")}
              className="mt-8 inline-block bg-amber-400 text-slate-900 hover:bg-amber-300 px-6 py-3 rounded-lg font-medium text-sm"
            >
              Ver planes de Research Mode →
            </button>
          </div>
        )}

        {false && founder && founderOpen && (
          <div className="max-w-3xl mx-auto mb-10 rounded-2xl bg-slate-900 text-white p-6 text-center shadow-xl">
            <div className="text-xs font-semibold tracking-widest text-amber-400 uppercase">
              Programa Fundadores
            </div>
            <div className="text-2xl md:text-3xl font-extrabold text-amber-400 mt-2">
              50% DE DESCUENTO. DE POR VIDA.
            </div>
            <p className="text-slate-300 text-sm mt-2">
              Para los primeros {founder?.spots_total} clientes. El precio que pagas hoy lo mantienes para siempre.
            </p>
            <div className="mt-3 inline-block bg-amber-500 text-slate-900 font-bold text-sm px-4 py-1.5 rounded-full">
              Quedan {founder?.spots_left} de {founder?.spots_total} cupos
            </div>
          </div>
        )}

        {false && (
        <div className="grid md:grid-cols-3 gap-6">
          {ordered.map((plan) => {
            const meta = FEATURES[plan.id];
            const isPreselected = preselectedPlan === plan.id;
            const price = founderOpen ? plan.founder_amount : plan.amount;
            return (
              <div
                key={plan.id}
                className={`rounded-2xl p-8 transition-all flex flex-col ${
                  meta.highlight
                    ? "bg-gradient-to-br from-brand-600 to-violet-600 text-white shadow-2xl shadow-brand-200"
                    : "bg-white border border-gray-200"
                } ${isPreselected ? "ring-4 ring-brand-300" : ""}`}
              >
                {meta.highlight && (
                  <div className="inline-block self-start text-xs font-medium bg-white/20 text-white px-2 py-1 rounded-full mb-3">
                    Más popular
                  </div>
                )}
                <h3 className="text-2xl font-bold capitalize">{plan.id}</h3>
                <p className={`text-sm mt-1 ${meta.highlight ? "text-brand-100" : "text-gray-600"}`}>
                  {meta.tagline}
                </p>
                <div className="mt-6 flex items-end gap-2">
                  <span className="text-5xl font-bold">{formatPrice(price)}</span>
                  <span className={`text-sm pb-1 ${meta.highlight ? "text-brand-100" : "text-gray-500"}`}>
                    /mes
                  </span>
                </div>
                <p className={`text-xs ${meta.highlight ? "text-brand-100" : "text-gray-400"}`}>
                  IVA no incluido
                </p>
                {founderOpen && (
                  <p className={`mt-1 text-sm ${meta.highlight ? "text-brand-100" : "text-gray-500"}`}>
                    <span className="line-through">{formatPrice(plan.amount)}</span>{" "}
                    <span className={meta.highlight ? "text-amber-300 font-semibold" : "text-emerald-600 font-semibold"}>
                      precio fundador de por vida
                    </span>
                  </p>
                )}
                <p
                  className={`mt-1 text-sm font-medium ${
                    meta.highlight ? "text-brand-100" : "text-brand-600"
                  }`}
                >
                  {formatPrice(price)}/mes
                </p>
                <button
                  onClick={() => handleSelect(plan.id)}
                  disabled={loading !== null}
                  className={`block w-full text-center mt-6 py-3 rounded-lg font-medium text-sm transition-colors disabled:opacity-60 ${
                    meta.highlight
                      ? "bg-white text-brand-700 hover:bg-brand-50"
                      : "bg-brand-600 text-white hover:bg-brand-700"
                  }`}
                >
                  {loading === plan.id ? "Redirigiendo a Stripe…" : "Empezar ahora"}
                </button>
                <ul className="mt-8 space-y-3 text-sm flex-1">
                  {meta.bullets.map((b) => (
                    <li key={b} className="flex items-start gap-2">
                      <svg
                        className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                          meta.highlight ? "text-white" : "text-brand-600"
                        }`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>{b}</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
        )}

        {track === "research" && (
          <>
            <p className="text-center text-gray-600 mb-8 max-w-2xl mx-auto text-sm">
              Solo research y los 6 ángulos. Sin funnel, sin publicar ads. Suscripción mensual por
              escaneos — el contador se reinicia cada ciclo y no acumula.
            </p>
            <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
              {orderedResearch.map((plan) => {
                const highlight = plan.id === "research_100";
                const isPreselected = preselectedPlan === plan.id;
                return (
                  <div
                    key={plan.id}
                    className={`rounded-2xl p-8 transition-all flex flex-col ${
                      highlight
                        ? "bg-gradient-to-br from-slate-900 to-slate-800 text-white shadow-2xl"
                        : "bg-white border border-gray-200"
                    } ${isPreselected ? "ring-4 ring-amber-300" : ""}`}
                  >
                    {highlight && (
                      <div className="inline-block self-start text-xs font-medium bg-amber-400 text-slate-900 px-2 py-1 rounded-full mb-3">
                        Mejor valor
                      </div>
                    )}
                    <h3 className="text-2xl font-bold">{plan.name}</h3>
                    <p className={`text-sm mt-1 ${highlight ? "text-slate-300" : "text-gray-600"}`}>
                      {plan.description}
                    </p>
                    <div className="mt-6 flex items-end gap-2">
                      <span className="text-5xl font-bold">{formatPrice(plan.amount)}</span>
                      <span className={`text-sm pb-1 ${highlight ? "text-slate-300" : "text-gray-500"}`}>
                        /mes
                      </span>
                    </div>
                    <p className={`text-xs ${highlight ? "text-slate-400" : "text-gray-400"}`}>
                      IVA no incluido
                    </p>
                    <p className={`mt-1 text-sm font-medium ${highlight ? "text-amber-400" : "text-amber-600"}`}>
                      {plan.scans_per_month} escaneos/mes · {plan.price_per_scan.toFixed(2)}€/escaneo
                    </p>
                    <button
                      onClick={() => handleSelect(plan.id)}
                      disabled={loading !== null}
                      className={`block w-full text-center mt-6 py-3 rounded-lg font-medium text-sm transition-colors disabled:opacity-60 ${
                        highlight
                          ? "bg-amber-400 text-slate-900 hover:bg-amber-300"
                          : "bg-slate-900 text-white hover:bg-slate-800"
                      }`}
                    >
                      {loading === plan.id ? "Redirigiendo a Stripe…" : "Empezar ahora"}
                    </button>
                    <ul className="mt-8 space-y-3 text-sm flex-1">
                      {[
                        `${plan.scans_per_month} escaneos de research al mes`,
                        "ICP + pain points reales con fuentes",
                        "6 ángulos con copy + imagen",
                        "Vista interactiva + export PDF",
                        "Histórico de ángulos por business_type",
                      ].map((b) => (
                        <li key={b} className="flex items-start gap-2">
                          <svg
                            className={`w-5 h-5 flex-shrink-0 mt-0.5 ${highlight ? "text-amber-400" : "text-slate-700"}`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          <span>{b}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </div>
          </>
        )}

        {error && <p className="text-center text-red-600 text-sm mt-6">{error}</p>}

        <p className="text-center text-xs text-gray-400 mt-8">
          {track === "platform"
            ? "Plataforma completa muy pronto. Mientras tanto, empieza con Research Mode."
            : "Suscripción mensual. El saldo de escaneos no usado no se acumula al siguiente mes."}
        </p>

        <div className="text-center mt-6">
          <button
            onClick={() => {
              logout();
              navigate("/");
            }}
            className="text-sm text-gray-400 hover:text-gray-600"
          >
            Cerrar sesión
          </button>
        </div>
      </div>
    </div>
  );
}
