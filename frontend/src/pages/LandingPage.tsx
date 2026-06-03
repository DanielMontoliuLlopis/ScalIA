import { useEffect, useState } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import { API_URL } from "../lib/runtimeConfig";

interface FormField {
  name: string;
  label: string;
  type: string;
  required: boolean;
  placeholder: string;
  options?: string[];
  helper?: string;
}

interface ValueProp { icon_hint?: string; title: string; text: string; }
interface Testimonial { name: string; role: string; quote: string; result?: string | null; }
interface Objection { question: string; answer: string; }
interface ProcessStep { step: number; title: string; text: string; }

interface SaleContent {
  value_props?: ValueProp[];
  social_proof_logos?: string[];
  testimonials?: Testimonial[];
  objections?: Objection[];
  process?: ProcessStep[];
  authority?: { headline: string; bullets: string[] };
  urgency?: { headline: string; subtext: string; deadline_hint?: string | null };
  guarantee?: { headline: string; text: string };
  pricing?: {
    price: string;
    billing_note?: string | null;
    includes: string[];
    value_anchor?: string;
    comparison?: string | null;
  };
  cta_repeat?: { hero: string; mid: string; final: string };
  closing_line?: string;
}

interface Landing {
  id: string;
  variant: string;
  campaign_type: string;
  landing_subtype: string | null;
  sale_type: string | null;
  funnel_type: string | null;
  template_id: string | null;
  headline: string;
  subheadline: string;
  benefits: string[];
  cta_text: string;
  hero_image_url: string | null;
  primary_color: string;
  secondary_color: string;
  logo_url: string | null;
  meta_pixel_id: string | null;
  redirect_url: string | null;
  form_fields: FormField[];
  sale_content: SaleContent | null;
}

const ICONS: Record<string, string> = {
  clock: "⏱", shield: "🛡", chart: "📈", target: "🎯", users: "👥",
  lightning: "⚡", sparkles: "✨", check: "✓", rocket: "🚀", lock: "🔒",
};

export function LandingPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const variant = searchParams.get("v") ?? "a";
  void variant;

  const [landing, setLanding] = useState<Landing | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!id) return;
    fetch(`${API_URL}/landings/${id}`)
      .then((r) => {
        if (!r.ok) { setNotFound(true); return null; }
        return r.json();
      })
      .then((data) => {
        if (data) {
          setLanding(data);
          if (data.meta_pixel_id) injectMetaPixel(data.meta_pixel_id);
        }
      });
  }, [id]);

  const injectMetaPixel = (pixelId: string) => {
    if (document.getElementById("meta-pixel")) return;
    const script = document.createElement("script");
    script.id = "meta-pixel";
    script.innerHTML = `
      !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
      n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
      n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
      t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,
      document,'script','https://connect.facebook.net/en_US/fbevents.js');
      fbq('init', '${pixelId}');
      fbq('track', 'PageView');
    `;
    document.head.appendChild(script);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!landing) return;
    setSubmitting(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/landings/${landing.id}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (!res.ok) throw new Error("Error al enviar");
      if ((window as any).fbq) (window as any).fbq("track", "Lead");
      navigate(`/landing/${landing.id}/thanks`);
    } catch {
      setError("Algo salió mal. Inténtalo de nuevo.");
    } finally {
      setSubmitting(false);
    }
  };

  if (notFound) return (
    <div className="min-h-screen flex items-center justify-center text-gray-400">
      <p>Landing page no encontrada.</p>
    </div>
  );

  if (!landing) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  const isSale = landing.landing_subtype === "sale";

  if (isSale) {
    return <SaleLanding landing={landing} onLeadTrack={() => {
      if ((window as any).fbq) (window as any).fbq("track", "Lead");
    }} />;
  }

  const tid = landing.template_id;
  const isLeadMagnet = tid === "lead_magnet_clean" || landing.landing_subtype === "lm";
  const isSaasTemplate = tid === "saas_trial" || tid === "saas_demo";
  const isServicesTemplate = tid === "services_call" || tid === "services_launch";
  const isEcommerceTemplate = tid === "ecommerce_product";
  const isAppTemplate = tid === "app_download";
  const isLocalTemplate = tid === "local_offer";

  if (isLeadMagnet) {
    return <LeadMagnetLanding landing={landing} onSubmit={handleSubmit} formData={formData} setFormData={setFormData} submitting={submitting} error={error} />;
  }
  if (isSaasTemplate) {
    return <SaasLanding landing={landing} onSubmit={handleSubmit} formData={formData} setFormData={setFormData} submitting={submitting} error={error} isTrial={tid === "saas_trial"} />;
  }
  if (isServicesTemplate) {
    return <ServicesLanding landing={landing} onSubmit={handleSubmit} formData={formData} setFormData={setFormData} submitting={submitting} error={error} isLaunch={tid === "services_launch"} />;
  }
  if (isEcommerceTemplate) {
    return <EcommerceLanding landing={landing} onSubmit={handleSubmit} formData={formData} setFormData={setFormData} submitting={submitting} error={error} />;
  }
  if (isAppTemplate) {
    return <AppLanding landing={landing} onSubmit={handleSubmit} formData={formData} setFormData={setFormData} submitting={submitting} error={error} />;
  }
  if (isLocalTemplate) {
    return <LocalLanding landing={landing} onSubmit={handleSubmit} formData={formData} setFormData={setFormData} submitting={submitting} error={error} />;
  }

  const { primary_color, secondary_color } = landing;

  return (
    <div className="min-h-screen bg-white">
      <div className="px-6 py-16 max-w-3xl mx-auto text-center">
        {landing.logo_url && (
          <img src={landing.logo_url} alt="logo" className="h-10 mx-auto mb-8 object-contain" />
        )}
        <h1 className="text-4xl md:text-5xl font-extrabold text-gray-900 leading-tight mb-4">
          {landing.headline}
        </h1>
        <p className="text-xl text-gray-500 mb-8">{landing.subheadline}</p>

        {landing.hero_image_url && (
          <img
            src={landing.hero_image_url}
            alt="hero"
            className="w-full max-w-lg mx-auto rounded-2xl shadow-lg mb-10 object-cover aspect-square"
          />
        )}

        <ul className="text-left max-w-md mx-auto space-y-3 mb-10">
          {landing.benefits.map((b, i) => (
            <li key={i} className="flex items-start gap-2 text-gray-700">
              <span className="mt-0.5 text-lg" style={{ color: primary_color }}>✓</span>
              <span>{b}</span>
            </li>
          ))}
        </ul>

        {landing.campaign_type === "direct_sale" && landing.redirect_url ? (
          <a
            href={landing.redirect_url}
            className="inline-block px-8 py-4 rounded-xl text-white font-bold text-lg shadow-lg hover:opacity-90 transition-opacity"
            style={{ backgroundColor: primary_color }}
          >
            {landing.cta_text}
          </a>
        ) : (
          <div
            className="rounded-2xl p-6 max-w-md mx-auto shadow-sm"
            style={{ backgroundColor: secondary_color }}
          >
            <p className="font-semibold text-gray-800 mb-5 text-lg">{landing.cta_text}</p>
            <form onSubmit={handleSubmit} className="space-y-4">
              {landing.form_fields.map((field) => (
                <div key={field.name} className="text-left">
                  <label className="block text-xs font-semibold text-gray-600 mb-1 uppercase tracking-wide">
                    {field.label}
                    {field.required && <span className="text-red-400 ml-0.5">*</span>}
                  </label>

                  {field.type === "select" && field.options ? (
                    <select
                      required={field.required}
                      value={formData[field.name] ?? ""}
                      onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
                      className="w-full border border-gray-300 bg-white rounded-lg px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:ring-2 appearance-none"
                      style={{ "--tw-ring-color": primary_color } as React.CSSProperties}
                    >
                      <option value="" disabled>{field.placeholder || `Selecciona ${field.label.toLowerCase()}`}</option>
                      {field.options.map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                  ) : field.type === "radio" && field.options ? (
                    <div className="flex flex-wrap gap-2">
                      {field.options.map((opt) => (
                        <label
                          key={opt}
                          className={`cursor-pointer px-3 py-2 rounded-lg border text-sm font-medium transition-all ${
                            formData[field.name] === opt
                              ? "text-white border-transparent"
                              : "bg-white text-gray-600 border-gray-300 hover:border-gray-400"
                          }`}
                          style={formData[field.name] === opt ? { backgroundColor: primary_color, borderColor: primary_color } : {}}
                        >
                          <input
                            type="radio"
                            name={field.name}
                            value={opt}
                            required={field.required}
                            checked={formData[field.name] === opt}
                            onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
                            className="sr-only"
                          />
                          {opt}
                        </label>
                      ))}
                    </div>
                  ) : (
                    <input
                      type={field.type}
                      placeholder={field.placeholder || field.label}
                      required={field.required}
                      value={formData[field.name] ?? ""}
                      onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
                      className="w-full border border-gray-300 bg-white rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2"
                      style={{ "--tw-ring-color": primary_color } as React.CSSProperties}
                    />
                  )}

                  {field.helper && (
                    <p className="text-xs text-gray-400 mt-1">{field.helper}</p>
                  )}
                </div>
              ))}

              {error && <p className="text-red-500 text-sm">{error}</p>}

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3 rounded-xl text-white font-bold text-sm disabled:opacity-50 transition-opacity hover:opacity-90 mt-2"
                style={{ backgroundColor: primary_color }}
              >
                {submitting ? "Enviando…" : landing.cta_text}
              </button>
            </form>
            <p className="text-xs text-gray-400 mt-3 text-center">Sin spam. Cancela cuando quieras.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function SaleLanding({ landing, onLeadTrack }: { landing: Landing; onLeadTrack: () => void }) {
  const { primary_color, secondary_color, sale_type, redirect_url, cta_text } = landing;
  const sc = landing.sale_content ?? {};
  const isPayment = sale_type === "payment";

  const ctaHero = sc.cta_repeat?.hero || cta_text;
  const ctaMid = sc.cta_repeat?.mid || cta_text;
  const ctaFinal = sc.cta_repeat?.final || cta_text;

  const handleCtaClick = () => {
    onLeadTrack();
  };

  const CtaButton = ({ label, big = false }: { label: string; big?: boolean }) => (
    <a
      href={redirect_url ?? "#"}
      target={redirect_url?.startsWith("http") ? "_blank" : undefined}
      rel="noopener noreferrer"
      onClick={handleCtaClick}
      className={`inline-block rounded-xl text-white font-bold shadow-lg hover:opacity-90 transition-opacity ${
        big ? "px-10 py-5 text-lg" : "px-8 py-4 text-base"
      }`}
      style={{ backgroundColor: primary_color }}
    >
      {label}
    </a>
  );

  return (
    <div className="min-h-screen bg-white text-gray-900">
      {/* HERO */}
      <section className="px-6 pt-16 pb-12 max-w-5xl mx-auto">
        {landing.logo_url && (
          <img src={landing.logo_url} alt="logo" className="h-10 mb-8 object-contain" />
        )}
        <div className="grid md:grid-cols-2 gap-10 items-center">
          <div>
            <h1 className="text-4xl md:text-5xl font-extrabold leading-tight mb-4">
              {landing.headline}
            </h1>
            <p className="text-xl text-gray-500 mb-6">{landing.subheadline}</p>

            {sc.value_props && sc.value_props.length > 0 && (
              <ul className="space-y-3 mb-8">
                {sc.value_props.map((vp, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span
                      className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-lg"
                      style={{ backgroundColor: secondary_color, color: primary_color }}
                    >
                      {ICONS[vp.icon_hint ?? "check"] || "✓"}
                    </span>
                    <div>
                      <p className="font-semibold">{vp.title}</p>
                      <p className="text-sm text-gray-500">{vp.text}</p>
                    </div>
                  </li>
                ))}
              </ul>
            )}

            <CtaButton label={ctaHero} big />
            {!isPayment && (
              <p className="text-xs text-gray-400 mt-3">Sin compromiso. Cancela cuando quieras.</p>
            )}
          </div>

          {landing.hero_image_url && (
            <img
              src={landing.hero_image_url}
              alt="hero"
              className="w-full rounded-2xl shadow-lg object-cover aspect-square"
            />
          )}
        </div>
      </section>

      {/* SOCIAL PROOF LOGOS */}
      {sc.social_proof_logos && sc.social_proof_logos.length > 0 && (
        <section className="px-6 py-8 border-y border-gray-100 bg-gray-50">
          <div className="max-w-5xl mx-auto">
            <p className="text-center text-xs uppercase tracking-widest text-gray-400 mb-4">
              Confían en nosotros
            </p>
            <div className="flex flex-wrap justify-center gap-x-10 gap-y-3">
              {sc.social_proof_logos.map((logo, i) => (
                <span key={i} className="text-gray-500 font-semibold text-sm">{logo}</span>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* BENEFITS */}
      {landing.benefits.length > 0 && (
        <section className="px-6 py-16 max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-10">Qué obtienes</h2>
          <ul className="space-y-4">
            {landing.benefits.map((b, i) => (
              <li key={i} className="flex items-start gap-3 text-lg">
                <span className="mt-1 text-xl" style={{ color: primary_color }}>✓</span>
                <span>{b}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* TESTIMONIALS */}
      {sc.testimonials && sc.testimonials.length > 0 && (
        <section className="px-6 py-16 bg-gray-50">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-10">Lo que dicen</h2>
            <div className="grid md:grid-cols-3 gap-6">
              {sc.testimonials.map((t, i) => (
                <div key={i} className="bg-white p-6 rounded-2xl shadow-sm">
                  <p className="text-gray-700 mb-4 leading-relaxed">"{t.quote}"</p>
                  {t.result && (
                    <p
                      className="text-sm font-semibold mb-3 inline-block px-3 py-1 rounded-full"
                      style={{ backgroundColor: secondary_color, color: primary_color }}
                    >
                      {t.result}
                    </p>
                  )}
                  <p className="font-semibold text-gray-900">{t.name}</p>
                  <p className="text-sm text-gray-500">{t.role}</p>
                </div>
              ))}
            </div>
            <div className="text-center mt-12">
              <CtaButton label={ctaMid} />
            </div>
          </div>
        </section>
      )}

      {/* PROCESS (call) o PRICING (payment) */}
      {!isPayment && sc.process && sc.process.length > 0 && (
        <section className="px-6 py-16 max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-10">Cómo funciona</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {sc.process.map((p) => (
              <div key={p.step} className="text-center">
                <div
                  className="w-12 h-12 rounded-full mx-auto mb-3 flex items-center justify-center font-bold text-lg"
                  style={{ backgroundColor: primary_color, color: "white" }}
                >
                  {p.step}
                </div>
                <p className="font-semibold mb-1">{p.title}</p>
                <p className="text-sm text-gray-500">{p.text}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {isPayment && sc.pricing && (
        <section className="px-6 py-16 max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-10">Plan e inversión</h2>
          <div className="border-2 rounded-2xl p-8 shadow-lg" style={{ borderColor: primary_color }}>
            <div className="text-center mb-6">
              <p className="text-5xl font-extrabold" style={{ color: primary_color }}>
                {sc.pricing.price}
              </p>
              {sc.pricing.billing_note && (
                <p className="text-sm text-gray-500 mt-1">{sc.pricing.billing_note}</p>
              )}
              {sc.pricing.value_anchor && (
                <p className="text-sm text-gray-600 mt-3 italic">{sc.pricing.value_anchor}</p>
              )}
            </div>
            {sc.pricing.includes.length > 0 && (
              <ul className="space-y-3 mb-6">
                {sc.pricing.includes.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-gray-700">
                    <span style={{ color: primary_color }}>✓</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            )}
            {sc.pricing.comparison && (
              <p className="text-center text-sm text-gray-500 italic mb-6">{sc.pricing.comparison}</p>
            )}
            <div className="text-center">
              <CtaButton label={ctaMid} big />
            </div>
          </div>
        </section>
      )}

      {/* AUTHORITY (call) */}
      {!isPayment && sc.authority?.headline && (
        <section className="px-6 py-16 bg-gray-50">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl font-bold mb-6">{sc.authority.headline}</h2>
            <ul className="space-y-3 inline-block text-left">
              {sc.authority.bullets.map((b, i) => (
                <li key={i} className="flex items-start gap-2 text-gray-700">
                  <span style={{ color: primary_color }}>✓</span>
                  <span>{b}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {/* URGENCY (payment) */}
      {isPayment && sc.urgency?.headline && (
        <section className="px-6 py-12">
          <div
            className="max-w-3xl mx-auto rounded-2xl p-8 text-center"
            style={{ backgroundColor: secondary_color }}
          >
            <p className="text-2xl font-bold mb-2" style={{ color: primary_color }}>
              {sc.urgency.headline}
            </p>
            {sc.urgency.subtext && (
              <p className="text-gray-700">{sc.urgency.subtext}</p>
            )}
            {sc.urgency.deadline_hint && (
              <p className="text-sm font-semibold mt-3 text-gray-500">{sc.urgency.deadline_hint}</p>
            )}
          </div>
        </section>
      )}

      {/* GUARANTEE */}
      {sc.guarantee?.headline && (
        <section className="px-6 py-16">
          <div className="max-w-3xl mx-auto flex items-start gap-6 bg-white border border-gray-200 rounded-2xl p-8">
            <div
              className="flex-shrink-0 w-16 h-16 rounded-full flex items-center justify-center text-3xl"
              style={{ backgroundColor: secondary_color }}
            >
              🛡
            </div>
            <div>
              <h3 className="text-xl font-bold mb-2">{sc.guarantee.headline}</h3>
              <p className="text-gray-600">{sc.guarantee.text}</p>
            </div>
          </div>
        </section>
      )}

      {/* OBJECTIONS / FAQ */}
      {sc.objections && sc.objections.length > 0 && (
        <section className="px-6 py-16 bg-gray-50">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-10">Preguntas frecuentes</h2>
            <div className="space-y-4">
              {sc.objections.map((o, i) => (
                <details key={i} className="bg-white rounded-xl p-5 shadow-sm group">
                  <summary className="font-semibold cursor-pointer list-none flex justify-between items-center">
                    <span>{o.question}</span>
                    <span className="text-gray-400 group-open:rotate-45 transition-transform text-xl leading-none">+</span>
                  </summary>
                  <p className="text-gray-600 mt-3">{o.answer}</p>
                </details>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* FINAL CTA */}
      <section className="px-6 py-20 text-center">
        <div className="max-w-2xl mx-auto">
          {sc.closing_line && (
            <p className="text-2xl font-semibold mb-8 text-gray-800">{sc.closing_line}</p>
          )}
          <CtaButton label={ctaFinal} big />
          {!isPayment && (
            <p className="text-xs text-gray-400 mt-4">Llamada de 30 minutos. Sin compromiso.</p>
          )}
        </div>
      </section>
    </div>
  );
}

interface ThanksPageData {
  headline: string;
  subheadline: string;
  next_step_title?: string;
  next_step_description?: string;
  cta_text?: string;
  cta_url?: string;
  ps_text?: string;
  lead_magnet_url?: string;
  lead_magnet_title?: string;
  primary_color: string;
  logo_url?: string;
}

// ─── Shared types for template props ──────────────────────────────────────────
interface TemplateProps {
  landing: Landing;
  onSubmit: (e: React.FormEvent) => void;
  formData: Record<string, string>;
  setFormData: React.Dispatch<React.SetStateAction<Record<string, string>>>;
  submitting: boolean;
  error: string;
}

// ─── Shared form renderer ─────────────────────────────────────────────────────
function SharedForm({ landing, onSubmit, formData, setFormData, submitting, error }: TemplateProps) {
  const { primary_color, secondary_color } = landing;
  if (!landing.form_fields.length) return null;
  return (
    <div className="rounded-2xl p-6 shadow-sm" style={{ backgroundColor: secondary_color }}>
      <p className="font-semibold text-gray-800 mb-5 text-lg">{landing.cta_text}</p>
      <form onSubmit={onSubmit} className="space-y-4">
        {landing.form_fields.map((field) => (
          <div key={field.name} className="text-left">
            <label className="block text-xs font-semibold text-gray-600 mb-1 uppercase tracking-wide">
              {field.label}{field.required && <span className="text-red-400 ml-0.5">*</span>}
            </label>
            {field.type === "select" && field.options ? (
              <select required={field.required} value={formData[field.name] ?? ""} onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })} className="w-full border border-gray-300 bg-white rounded-lg px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:ring-2 appearance-none">
                <option value="" disabled>{field.placeholder || `Selecciona ${field.label.toLowerCase()}`}</option>
                {field.options.map((opt) => <option key={opt} value={opt}>{opt}</option>)}
              </select>
            ) : field.type === "radio" && field.options ? (
              <div className="flex flex-wrap gap-2">
                {field.options.map((opt) => (
                  <label key={opt} className={`cursor-pointer px-3 py-2 rounded-lg border text-sm font-medium transition-all ${formData[field.name] === opt ? "text-white border-transparent" : "bg-white text-gray-600 border-gray-300 hover:border-gray-400"}`} style={formData[field.name] === opt ? { backgroundColor: primary_color, borderColor: primary_color } : {}}>
                    <input type="radio" name={field.name} value={opt} required={field.required} checked={formData[field.name] === opt} onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })} className="sr-only" />{opt}
                  </label>
                ))}
              </div>
            ) : (
              <input type={field.type} placeholder={field.placeholder || field.label} required={field.required} value={formData[field.name] ?? ""} onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })} className="w-full border border-gray-300 bg-white rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2" style={{ "--tw-ring-color": primary_color } as React.CSSProperties} />
            )}
            {field.helper && <p className="text-xs text-gray-400 mt-1">{field.helper}</p>}
          </div>
        ))}
        {error && <p className="text-red-500 text-sm">{error}</p>}
        <button type="submit" disabled={submitting} className="w-full py-3 rounded-xl text-white font-bold text-sm disabled:opacity-50 hover:opacity-90 transition-opacity mt-2" style={{ backgroundColor: primary_color }}>
          {submitting ? "Enviando…" : landing.cta_text}
        </button>
      </form>
      <p className="text-xs text-gray-400 mt-3 text-center">Sin spam. Cancela cuando quieras.</p>
    </div>
  );
}

// ─── Template: lead_magnet_clean ──────────────────────────────────────────────
function LeadMagnetLanding(props: TemplateProps) {
  const { landing } = props;
  const { primary_color } = landing;
  return (
    <div className="min-h-screen bg-white">
      <div className="px-6 py-16 max-w-2xl mx-auto text-center">
        {landing.logo_url && <img src={landing.logo_url} alt="logo" className="h-10 mx-auto mb-8 object-contain" />}
        <h1 className="text-4xl md:text-5xl font-extrabold text-gray-900 leading-tight mb-4">{landing.headline}</h1>
        <p className="text-xl text-gray-500 mb-8">{landing.subheadline}</p>
        {landing.hero_image_url && <img src={landing.hero_image_url} alt="hero" className="w-full max-w-sm mx-auto rounded-2xl shadow-lg mb-10 object-cover aspect-square" />}
        <ul className="text-left max-w-md mx-auto space-y-3 mb-10">
          {landing.benefits.map((b, i) => (
            <li key={i} className="flex items-start gap-2 text-gray-700">
              <span className="mt-0.5 text-lg" style={{ color: primary_color }}>✓</span><span>{b}</span>
            </li>
          ))}
        </ul>
        <div className="max-w-md mx-auto">
          <SharedForm {...props} />
        </div>
      </div>
    </div>
  );
}

// ─── Template: saas_trial / saas_demo ────────────────────────────────────────
function SaasLanding(props: TemplateProps & { isTrial: boolean }) {
  const { landing, isTrial } = props;
  const { primary_color } = landing;
  return (
    <div className="min-h-screen bg-white">
      {/* Navbar */}
      <nav className="border-b border-gray-100 px-6 py-4 flex items-center justify-between max-w-6xl mx-auto">
        {landing.logo_url ? <img src={landing.logo_url} alt="logo" className="h-8 object-contain" /> : <div className="w-8 h-8 rounded-lg" style={{ backgroundColor: primary_color }} />}
        <a href="#form" className="text-sm font-semibold px-4 py-2 rounded-lg text-white" style={{ backgroundColor: primary_color }}>{isTrial ? "Probar gratis" : "Ver demo"}</a>
      </nav>
      {/* Hero */}
      <section className="px-6 pt-16 pb-12 max-w-5xl mx-auto">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h1 className="text-4xl md:text-5xl font-extrabold leading-tight mb-4 text-gray-900">{landing.headline}</h1>
            <p className="text-xl text-gray-500 mb-8">{landing.subheadline}</p>
            <ul className="space-y-3 mb-8">
              {landing.benefits.map((b, i) => (
                <li key={i} className="flex items-start gap-2.5 text-gray-700">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold text-white mt-0.5" style={{ backgroundColor: primary_color }}>✓</span><span>{b}</span>
                </li>
              ))}
            </ul>
          </div>
          {landing.hero_image_url && <img src={landing.hero_image_url} alt="hero" className="w-full rounded-2xl shadow-xl object-cover aspect-video" />}
        </div>
      </section>
      {/* Social proof */}
      <section className="border-y border-gray-100 bg-gray-50 py-6 px-6">
        <p className="text-center text-xs uppercase tracking-widest text-gray-400">Confían en nosotros</p>
      </section>
      {/* Form */}
      <section id="form" className="px-6 py-16 max-w-lg mx-auto">
        <SharedForm {...props} />
      </section>
    </div>
  );
}

// ─── Template: services_call / services_launch ────────────────────────────────
function ServicesLanding(props: TemplateProps & { isLaunch: boolean }) {
  const { landing, isLaunch } = props;
  const { primary_color, secondary_color } = landing;
  return (
    <div className="min-h-screen bg-white">
      {/* Hero */}
      <section className="px-6 pt-16 pb-12" style={{ backgroundColor: secondary_color }}>
        <div className="max-w-4xl mx-auto text-center">
          {landing.logo_url && <img src={landing.logo_url} alt="logo" className="h-10 mx-auto mb-8 object-contain" />}
          {isLaunch && (
            <div className="inline-block mb-4 px-4 py-1.5 rounded-full text-sm font-bold text-white" style={{ backgroundColor: primary_color }}>
              Oferta por tiempo limitado
            </div>
          )}
          <h1 className="text-4xl md:text-5xl font-extrabold text-gray-900 leading-tight mb-4">{landing.headline}</h1>
          <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">{landing.subheadline}</p>
        </div>
      </section>
      {/* 3-step process */}
      <section className="px-6 py-16 max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-center mb-10 text-gray-900">Cómo funciona</h2>
        <div className="grid md:grid-cols-3 gap-8">
          {landing.benefits.slice(0, 3).map((b, i) => (
            <div key={i} className="text-center">
              <div className="w-12 h-12 rounded-full mx-auto mb-4 flex items-center justify-center text-white font-bold text-xl" style={{ backgroundColor: primary_color }}>{i + 1}</div>
              <p className="text-gray-700">{b}</p>
            </div>
          ))}
        </div>
      </section>
      {/* Form */}
      <section className="px-6 py-16 max-w-lg mx-auto">
        <SharedForm {...props} />
      </section>
    </div>
  );
}

// ─── Template: ecommerce_product ──────────────────────────────────────────────
function EcommerceLanding(props: TemplateProps) {
  const { landing } = props;
  const { primary_color, secondary_color } = landing;
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-5xl mx-auto px-6 py-12">
        {landing.logo_url && <img src={landing.logo_url} alt="logo" className="h-8 mb-10 object-contain" />}
        <div className="grid md:grid-cols-2 gap-12 items-start">
          {/* Product image */}
          <div>
            {landing.hero_image_url ? (
              <img src={landing.hero_image_url} alt="producto" className="w-full rounded-2xl shadow-lg object-cover aspect-square" />
            ) : (
              <div className="w-full aspect-square rounded-2xl" style={{ backgroundColor: secondary_color }} />
            )}
          </div>
          {/* Product info */}
          <div>
            <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 mb-3">{landing.headline}</h1>
            <p className="text-lg text-gray-500 mb-6">{landing.subheadline}</p>
            <ul className="space-y-2.5 mb-8">
              {landing.benefits.map((b, i) => (
                <li key={i} className="flex items-start gap-2 text-gray-700">
                  <span style={{ color: primary_color }} className="text-lg">✓</span><span>{b}</span>
                </li>
              ))}
            </ul>
            {landing.campaign_type === "direct_sale" && landing.redirect_url ? (
              <a href={landing.redirect_url} className="inline-block w-full text-center py-4 rounded-xl text-white font-bold text-lg hover:opacity-90 transition-opacity" style={{ backgroundColor: primary_color }}>{landing.cta_text}</a>
            ) : (
              <SharedForm {...props} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Template: app_download ───────────────────────────────────────────────────
function AppLanding(props: TemplateProps) {
  const { landing } = props;
  const { primary_color, secondary_color } = landing;
  return (
    <div className="min-h-screen bg-white">
      {/* Hero */}
      <section className="px-6 pt-16 pb-12" style={{ background: `linear-gradient(135deg, ${secondary_color} 0%, white 100%)` }}>
        <div className="max-w-4xl mx-auto text-center">
          {landing.logo_url && <img src={landing.logo_url} alt="logo" className="h-10 mx-auto mb-8 object-contain" />}
          <h1 className="text-4xl md:text-5xl font-extrabold text-gray-900 mb-4">{landing.headline}</h1>
          <p className="text-xl text-gray-500 mb-8 max-w-xl mx-auto">{landing.subheadline}</p>
          {landing.hero_image_url && <img src={landing.hero_image_url} alt="app" className="w-64 mx-auto rounded-3xl shadow-2xl mb-8 object-cover" />}
        </div>
      </section>
      {/* Features */}
      <section className="px-6 py-12 max-w-4xl mx-auto">
        <div className="grid md:grid-cols-2 gap-4">
          {landing.benefits.map((b, i) => (
            <div key={i} className="flex items-start gap-3 p-4 rounded-xl" style={{ backgroundColor: secondary_color }}>
              <span className="text-xl" style={{ color: primary_color }}>✓</span>
              <span className="text-gray-700">{b}</span>
            </div>
          ))}
        </div>
      </section>
      {/* Form / CTA */}
      <section className="px-6 py-12 max-w-md mx-auto">
        <SharedForm {...props} />
      </section>
    </div>
  );
}

// ─── Template: local_offer ────────────────────────────────────────────────────
function LocalLanding(props: TemplateProps) {
  const { landing } = props;
  const { primary_color } = landing;
  return (
    <div className="min-h-screen bg-white">
      {/* Hero with offer */}
      <section className="px-6 py-16 text-center" style={{ backgroundColor: primary_color }}>
        {landing.logo_url && <img src={landing.logo_url} alt="logo" className="h-10 mx-auto mb-6 object-contain filter brightness-0 invert" />}
        <h1 className="text-4xl md:text-5xl font-extrabold text-white leading-tight mb-4">{landing.headline}</h1>
        <p className="text-xl text-white/80 max-w-lg mx-auto">{landing.subheadline}</p>
      </section>
      {/* Benefits */}
      <section className="px-6 py-12 max-w-3xl mx-auto">
        <ul className="space-y-4">
          {landing.benefits.map((b, i) => (
            <li key={i} className="flex items-start gap-3 text-lg text-gray-700">
              <span className="text-2xl" style={{ color: primary_color }}>✓</span><span>{b}</span>
            </li>
          ))}
        </ul>
      </section>
      {/* Form */}
      <section className="px-6 py-12 max-w-lg mx-auto">
        <SharedForm {...props} />
      </section>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────

export function LandingThanks() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<ThanksPageData | null>(null);

  useEffect(() => {
    if (!id) return;
    fetch(`${API_URL}/landings/${id}/thanks`)
      .then((r) => r.ok ? r.json() : null)
      .then((d) => d && setData(d))
      .catch(() => null);
  }, [id]);

  const color = data?.primary_color ?? "#6366f1";

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center max-w-lg px-6 py-12 bg-white rounded-2xl shadow-sm">
        {data?.logo_url && (
          <img src={data.logo_url} alt="Logo" className="h-10 mx-auto mb-6 object-contain" />
        )}
        <div className="text-5xl mb-5">🎉</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-3">
          {data?.headline ?? "¡Gracias!"}
        </h1>
        <p className="text-gray-500 mb-6">
          {data?.subheadline ?? "Hemos recibido tus datos. Nos pondremos en contacto contigo pronto."}
        </p>

        {data?.next_step_title && (
          <div className="bg-gray-50 rounded-xl p-4 mb-6 text-left">
            <p className="font-semibold text-gray-800 mb-1">{data.next_step_title}</p>
            {data.next_step_description && (
              <p className="text-sm text-gray-500">{data.next_step_description}</p>
            )}
          </div>
        )}

        {data?.lead_magnet_url && (
          <a
            href={data.lead_magnet_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 w-full py-3 px-5 rounded-xl font-semibold text-white mb-4 hover:opacity-90 transition-opacity"
            style={{ backgroundColor: color }}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            {data.lead_magnet_title ? `Descargar: ${data.lead_magnet_title}` : "Descargar tu recurso"}
          </a>
        )}

        {data?.cta_url && data?.cta_text && (
          <a
            href={data.cta_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center w-full py-3 px-5 rounded-xl font-semibold border-2 mb-4 hover:bg-gray-50 transition-colors"
            style={{ borderColor: color, color }}
          >
            {data.cta_text}
          </a>
        )}

        {data?.ps_text && (
          <p className="text-xs text-gray-400 mt-4">{data.ps_text}</p>
        )}
      </div>
    </div>
  );
}
