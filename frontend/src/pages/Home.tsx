import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

interface PricingPlan {
  id: "starter" | "growth" | "agency";
  name: string;
  tagline: string;
  price: number; // precio normal
  founderPrice: number; // precio fundador de por vida (50%)
  campaigns: string;
  highlight: boolean;
  features: string[];
}

interface ResearchPlan {
  id: "research_10" | "research_100";
  name: string;
  tagline: string;
  price: number; // €/mes
  scans: number;
  pricePerScan: string;
  highlight: boolean;
  features: string[];
}

const PLANS: PricingPlan[] = [
  {
    id: "starter",
    name: "Starter",
    tagline: "Para empezar y validar tu primera oferta",
    price: 97,
    founderPrice: 48,
    campaigns: "1 campaña activa",
    highlight: false,
    features: [
      "1 campaña activa",
      "Copies y landing pages A/B con IA",
      "Lead magnets en PDF generados por IA",
      "Secuencias de email + WhatsApp",
      "CRM con scoring automático",
      "Publicación directa en Meta Ads",
    ],
  },
  {
    id: "growth",
    name: "Growth",
    tagline: "Para negocios que escalan y testean ángulos",
    price: 247,
    founderPrice: 123,
    campaigns: "3 campañas activas",
    highlight: true,
    features: [
      "3 campañas activas simultáneas",
      "Todo lo de Starter",
      "Multi-Angle Testing (N ángulos en paralelo)",
      "Optimización automática cada 24h",
      "Histórico de ángulos por tipo de negocio",
      "Equipo hasta 3 personas con roles",
    ],
  },
  {
    id: "agency",
    name: "Agency",
    tagline: "Para agencias y equipos multi-marca",
    price: 497,
    founderPrice: 248,
    campaigns: "Campañas ilimitadas",
    highlight: false,
    features: [
      "Campañas activas ilimitadas",
      "Todo lo de Growth",
      "Multi-cuenta de Meta Ads",
      "Agregación de histórico por agencia",
      "Equipo ilimitado con roles",
      "Soporte prioritario en menos de 2h",
    ],
  },
];

const RESEARCH_PLANS: ResearchPlan[] = [
  {
    id: "research_10",
    name: "Research 10",
    tagline: "Para empezar y probar el valor del research",
    price: 15,
    scans: 10,
    pricePerScan: "1,50€",
    highlight: false,
    features: [
      "10 escaneos de research al mes",
      "ICP + pain points reales con fuentes",
      "6 ángulos con copy + imagen",
      "Vista interactiva de ángulos en la web",
      "Export PDF incluido",
      "Histórico de ángulos por business_type",
    ],
  },
  {
    id: "research_100",
    name: "Research 100",
    tagline: "Para agencias y media buyers de alto volumen",
    price: 99,
    scans: 100,
    pricePerScan: "0,99€",
    highlight: true,
    features: [
      "100 escaneos de research al mes",
      "Todo lo de Research 10",
      "Mejor precio por escaneo (0,99€)",
      "Histórico de ángulos que mejora con el uso",
      "Ideal para lanzar muchas campañas",
      "Sin funnel — solo research + ángulos",
    ],
  },
];

const AGENTS = [
  { name: "Research", desc: "Investiga pain points reales, ICP y 6 ángulos de copy" },
  { name: "Copy", desc: "Genera anuncios + imágenes listas para publicar" },
  { name: "Landing", desc: "Crea landing pages A/B con tu marca y pixel" },
  { name: "Lead Magnet", desc: "Diseña recursos descargables en PDF con IA" },
  { name: "Email", desc: "Secuencias de nurturing por email y WhatsApp" },
  { name: "CRM", desc: "Clasifica leads en hot/warm/cold automáticamente" },
  { name: "Ads", desc: "Publica y optimiza tus campañas Meta directamente" },
  { name: "Optimization", desc: "Redistribuye presupuesto hacia los ángulos ganadores" },
];

const STEPS = [
  {
    n: 1,
    title: "Describe tu objetivo",
    desc: "Cuéntale a la IA qué quieres lograr: más leads, más ventas, más clientes locales.",
  },
  {
    n: 2,
    title: "Aprueba el plan",
    desc: "Los agentes proponen research, copies, landing, emails y anuncios. Tú decides.",
  },
  {
    n: 3,
    title: "Publica y optimiza",
    desc: "Con un clic se publica en Meta Ads y los agentes optimizan según los resultados.",
  },
];

type Track = "platform" | "research";

export function Home() {
  const { token } = useAuthStore();
  const ctaTarget = token ? "/campaigns/new" : "/register";
  const { hash } = useLocation();
  const [track, setTrack] = useState<Track>("research");

  useEffect(() => {
    if (!hash) return;
    const el = document.querySelector(hash);
    if (el) el.scrollIntoView({ behavior: "smooth" });
  }, [hash]);

  return (
    <div className="min-h-screen bg-white text-gray-900">
      {/* Nav */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold">
            Scal<span className="text-brand-600">IA</span>
          </Link>
          <div className="hidden md:flex items-center gap-8 text-sm text-gray-600">
            <a href="#how" className="hover:text-gray-900">
              Cómo funciona
            </a>
            <a href="#agents" className="hover:text-gray-900">
              Agentes
            </a>
            <a href="#research" className="hover:text-gray-900">
              Research Mode
            </a>
            <a href="#pricing" className="hover:text-gray-900">
              Precios
            </a>
          </div>
          <div className="flex items-center gap-3">
            {token ? (
              <Link
                to="/campaigns/new"
                className="text-sm bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg font-medium"
              >
                Ir a mi cuenta
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-sm text-gray-700 hover:text-gray-900 font-medium"
                >
                  Iniciar sesión
                </Link>
                <Link
                  to="/register"
                  className="text-sm bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg font-medium"
                >
                  Empezar
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-50 via-white to-violet-50" />
        <div className="relative max-w-6xl mx-auto px-6 pt-20 pb-24 text-center">
          <div className="inline-flex items-center gap-2 bg-brand-100 text-brand-700 px-3 py-1 rounded-full text-xs font-medium mb-6">
            <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse" />
            Marketing autónomo con IA
          </div>
          <h1 className="text-5xl md:text-6xl font-bold tracking-tight leading-tight">
            Analiza, lanza y optimiza.
            <br />
            <span className="bg-gradient-to-r from-brand-600 to-violet-600 bg-clip-text text-transparent">
              Todo tu marketing, en un agente.
            </span>
          </h1>
          <p className="mt-6 text-lg text-gray-600 max-w-2xl mx-auto">
            Describe tu objetivo en lenguaje natural. Los agentes investigan, generan copies, diseñan
            landing pages, lanzan secuencias de email y publican tus anuncios en Meta — y después
            redistribuyen el presupuesto hacia los ángulos que ganan. Tú apruebas, ellos ejecutan.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              to={ctaTarget}
              className="bg-brand-600 hover:bg-brand-700 text-white px-6 py-3 rounded-lg font-medium text-sm shadow-lg shadow-brand-200"
            >
              Empezar ahora →
            </Link>
            <a
              href="#research"
              className="bg-white border border-gray-300 hover:border-gray-400 text-gray-900 px-6 py-3 rounded-lg font-medium text-sm"
            >
              Solo quiero el research →
            </a>
          </div>
          <p className="mt-4 text-xs text-gray-400">
            Research Mode disponible ya. Plataforma completa muy pronto.
          </p>
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="max-w-6xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold">Cómo funciona</h2>
          <p className="mt-3 text-gray-600">Propone → apruebas → ejecuta. Tú mandas.</p>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {STEPS.map((s) => (
            <div
              key={s.n}
              className="bg-white border border-gray-200 rounded-2xl p-6 hover:border-brand-300 transition-colors"
            >
              <div className="w-10 h-10 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center font-bold mb-4">
                {s.n}
              </div>
              <h3 className="font-semibold text-lg">{s.title}</h3>
              <p className="mt-2 text-sm text-gray-600">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Agents */}
      <section id="agents" className="bg-gray-50 py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold">8 agentes trabajando para ti</h2>
            <p className="mt-3 text-gray-600">
              Cada uno experto en una parte del funnel. Todos coordinados.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {AGENTS.map((a) => (
              <div key={a.name} className="bg-white/70 backdrop-blur-xl rounded-xl border border-white/50 shadow-glass p-5">
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <h3 className="font-semibold">{a.name}Agent</h3>
                </div>
                <p className="text-sm text-gray-600">{a.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Research Mode */}
      <section id="research" className="max-w-6xl mx-auto px-6 py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-flex items-center gap-2 bg-amber-100 text-amber-800 px-3 py-1 rounded-full text-xs font-semibold tracking-wide uppercase mb-4">
              Research Mode
            </div>
            <h2 className="text-3xl md:text-4xl font-bold">
              ¿Ya tienes tus sistemas? Quédate solo con el research.
            </h2>
            <p className="mt-4 text-gray-600">
              Si eres media buyer o agencia y ya tienes tus landings y secuencias, lo que más vale es
              el output del research: pain points reales, ICP y los 6 ángulos con su copy e imagen. Sin
              montar el funnel completo.
            </p>
            <ul className="mt-6 space-y-3 text-sm text-gray-700">
              {[
                "Cada escaneo = 1 research completo (ICP + 6 ángulos con copy e imagen)",
                "Explora los ángulos en la web y exporta en PDF",
                "Histórico de ángulos por tipo de negocio que mejora con el uso",
                "Suscripción mensual por escaneos — sin permanencia",
              ].map((f) => (
                <li key={f} className="flex items-start gap-2">
                  <svg
                    className="w-5 h-5 flex-shrink-0 mt-0.5 text-amber-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span>{f}</span>
                </li>
              ))}
            </ul>
            <button
              onClick={() => {
                setTrack("research");
                document.getElementById("pricing")?.scrollIntoView({ behavior: "smooth" });
              }}
              className="mt-8 inline-block bg-slate-900 hover:bg-slate-800 text-white px-6 py-3 rounded-lg font-medium text-sm"
            >
              Ver planes de Research Mode →
            </button>
          </div>
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-3xl p-8 text-white shadow-2xl">
            <div className="text-xs uppercase tracking-widest text-amber-400 font-semibold">
              Un escaneo incluye
            </div>
            <div className="mt-6 space-y-4">
              {[
                ["ICP", "Perfil de cliente ideal con objeciones"],
                ["Pain points", "Reales, con fuentes de Brave Search"],
                ["6 ángulos", "Dolor · Aspiración · Miedo · Social · Curiosidad · Credibilidad"],
                ["Copy + imagen", "Cada ángulo con su hook e imagen"],
                ["Export", "PDF listo para tu cliente"],
              ].map(([t, d]) => (
                <div key={t} className="border-l-2 border-amber-400 pl-4">
                  <div className="font-semibold">{t}</div>
                  <div className="text-sm text-slate-300">{d}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="bg-gray-50 py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-8">
            <h2 className="text-3xl md:text-4xl font-bold">Precios simples</h2>
            <p className="mt-3 text-gray-600">
              Dos formas de usar ScalIA. Elige la que encaja contigo.
            </p>
          </div>

          {/* Toggle de línea de producto */}
          <div className="flex justify-center mb-12">
            <div className="inline-flex bg-white border border-gray-200 rounded-full p-1 shadow-sm">
              <button
                onClick={() => setTrack("research")}
                className={`px-5 py-2 rounded-full text-sm font-medium transition-colors ${
                  track === "research"
                    ? "bg-slate-900 text-white"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                Research Mode
              </button>
              <button
                onClick={() => setTrack("platform")}
                className={`px-5 py-2 rounded-full text-sm font-medium transition-colors inline-flex items-center gap-2 ${
                  track === "platform"
                    ? "bg-brand-600 text-white"
                    : "text-gray-400 hover:text-gray-600"
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

          {track === "platform" ? (
            <div className="max-w-3xl mx-auto rounded-3xl bg-gradient-to-br from-slate-900 to-slate-800 text-white p-10 md:p-14 text-center shadow-2xl">
              <div className="text-xs font-semibold tracking-widest text-amber-400 uppercase">
                Próximamente
              </div>
              <h3 className="text-2xl md:text-3xl font-extrabold mt-3">
                La plataforma completa llega pronto
              </h3>
              <p className="text-slate-300 text-sm mt-4 max-w-xl mx-auto">
                El flujo agéntico end-to-end: research → copy → funnel → ads → leads → optimización.
                Estamos puliendo los últimos detalles. Mientras tanto, empieza con Research Mode y
                quédate con el output más valioso: ICP, pain points y los 6 ángulos.
              </p>
              <button
                onClick={() => {
                  setTrack("research");
                  document.getElementById("pricing")?.scrollIntoView({ behavior: "smooth" });
                }}
                className="mt-8 inline-block bg-amber-400 text-slate-900 hover:bg-amber-300 px-6 py-3 rounded-lg font-medium text-sm"
              >
                Ver planes de Research Mode →
              </button>
            </div>
          ) : false ? (
            <>
              <p className="text-center text-gray-600 mb-8 max-w-2xl mx-auto text-sm">
                El flujo agéntico end-to-end: research → copy → funnel → ads → leads → optimización.
              </p>

              {/* Programa Fundadores */}
              <div className="max-w-3xl mx-auto mb-10 rounded-2xl bg-slate-900 text-white p-6 text-center shadow-xl">
                <div className="text-xs font-semibold tracking-widest text-amber-400 uppercase">
                  Programa Fundadores — solo 20 cupos
                </div>
                <div className="text-2xl md:text-3xl font-extrabold text-amber-400 mt-2">
                  50% DE DESCUENTO. DE POR VIDA.
                </div>
                <p className="text-slate-300 text-sm mt-2">
                  Para los primeros 20 clientes. El precio que pagas hoy lo mantienes para siempre — sin
                  fecha de vencimiento.
                </p>
              </div>

              <div className="grid md:grid-cols-3 gap-6">
                {PLANS.map((plan) => (
                  <div
                    key={plan.id}
                    className={`rounded-2xl p-8 ${
                      plan.highlight
                        ? "bg-gradient-to-br from-brand-600 to-violet-600 text-white shadow-2xl shadow-brand-200 scale-[1.02]"
                        : "bg-white border border-gray-200"
                    }`}
                  >
                    {plan.highlight && (
                      <div className="inline-block text-xs font-medium bg-white/20 text-white px-2 py-1 rounded-full mb-3">
                        Más popular
                      </div>
                    )}
                    <h3 className="text-2xl font-bold">{plan.name}</h3>
                    <p className={`text-sm mt-1 ${plan.highlight ? "text-brand-100" : "text-gray-600"}`}>
                      {plan.tagline}
                    </p>
                    <div className="mt-6 flex items-end gap-2">
                      <span className="text-5xl font-bold">{plan.founderPrice}€</span>
                      <span className={`text-sm pb-1 ${plan.highlight ? "text-brand-100" : "text-gray-500"}`}>
                        /mes
                      </span>
                    </div>
                    <p className={`mt-1 text-sm ${plan.highlight ? "text-brand-100" : "text-gray-500"}`}>
                      <span className="line-through">{plan.price}€</span>{" "}
                      <span
                        className={
                          plan.highlight ? "text-amber-300 font-semibold" : "text-emerald-600 font-semibold"
                        }
                      >
                        precio fundador de por vida
                      </span>
                    </p>
                    <p
                      className={`mt-1 text-sm font-medium ${
                        plan.highlight ? "text-brand-100" : "text-brand-600"
                      }`}
                    >
                      {plan.campaigns}
                    </p>
                    <Link
                      to={`/register?plan=${plan.id}`}
                      className={`block text-center mt-6 py-3 rounded-lg font-medium text-sm transition-colors ${
                        plan.highlight
                          ? "bg-white text-brand-700 hover:bg-brand-50"
                          : "bg-brand-600 text-white hover:bg-brand-700"
                      }`}
                    >
                      Empezar ahora
                    </Link>
                    <ul className="mt-8 space-y-3 text-sm">
                      {plan.features.map((f) => (
                        <li key={f} className="flex items-start gap-2">
                          <svg
                            className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                              plan.highlight ? "text-white" : "text-brand-600"
                            }`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          <span>{f}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
              <p className="text-center text-xs text-gray-400 mt-8">
                IVA no incluido. El gasto en Meta Ads no está incluido — se carga a tu cuenta de Meta.
              </p>
            </>
          ) : (
            <>
              <p className="text-center text-gray-600 mb-10 max-w-2xl mx-auto text-sm">
                Solo research y los 6 ángulos. Sin funnel, sin publicar ads. Suscripción mensual por
                escaneos — el contador se reinicia cada ciclo y no acumula.
              </p>

              <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
                {RESEARCH_PLANS.map((plan) => (
                  <div
                    key={plan.id}
                    className={`rounded-2xl p-8 ${
                      plan.highlight
                        ? "bg-gradient-to-br from-slate-900 to-slate-800 text-white shadow-2xl scale-[1.02]"
                        : "bg-white border border-gray-200"
                    }`}
                  >
                    {plan.highlight && (
                      <div className="inline-block text-xs font-medium bg-amber-400 text-slate-900 px-2 py-1 rounded-full mb-3">
                        Mejor valor
                      </div>
                    )}
                    <h3 className="text-2xl font-bold">{plan.name}</h3>
                    <p className={`text-sm mt-1 ${plan.highlight ? "text-slate-300" : "text-gray-600"}`}>
                      {plan.tagline}
                    </p>
                    <div className="mt-6 flex items-end gap-2">
                      <span className="text-5xl font-bold">{plan.price}€</span>
                      <span className={`text-sm pb-1 ${plan.highlight ? "text-slate-300" : "text-gray-500"}`}>
                        /mes
                      </span>
                    </div>
                    <p
                      className={`mt-1 text-sm font-medium ${
                        plan.highlight ? "text-amber-400" : "text-amber-600"
                      }`}
                    >
                      {plan.scans} escaneos/mes · {plan.pricePerScan}/escaneo
                    </p>
                    <Link
                      to={`/register?plan=${plan.id}`}
                      className={`block text-center mt-6 py-3 rounded-lg font-medium text-sm transition-colors ${
                        plan.highlight
                          ? "bg-amber-400 text-slate-900 hover:bg-amber-300"
                          : "bg-slate-900 text-white hover:bg-slate-800"
                      }`}
                    >
                      Empezar ahora
                    </Link>
                    <ul className="mt-8 space-y-3 text-sm">
                      {plan.features.map((f) => (
                        <li key={f} className="flex items-start gap-2">
                          <svg
                            className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                              plan.highlight ? "text-amber-400" : "text-slate-700"
                            }`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          <span>{f}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
              <p className="text-center text-xs text-gray-400 mt-8">
                El saldo no usado no se acumula al siguiente mes.
              </p>
            </>
          )}
        </div>
      </section>

      {/* FAQ + CTA final */}
      <section className="bg-gradient-to-br from-brand-600 to-violet-700 text-white py-20">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-3xl md:text-4xl font-bold">
            Tu próxima campaña, lista en 10 minutos
          </h2>
          <p className="mt-4 text-brand-100">
            Genera research accionable — ICP, pain points y 6 ángulos con copy e imagen — en minutos.
          </p>
          <Link
            to={ctaTarget}
            className="inline-block mt-8 bg-white text-brand-700 hover:bg-brand-50 px-8 py-3 rounded-lg font-medium text-sm shadow-lg"
          >
            Empezar ahora →
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-8">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center text-sm text-gray-500">
          <div className="font-semibold text-gray-900">
            Scal<span className="text-brand-600">IA</span>
          </div>
          <div className="mt-3 md:mt-0">© 2026 ScalIA. Todos los derechos reservados.</div>
        </div>
      </footer>
    </div>
  );
}
