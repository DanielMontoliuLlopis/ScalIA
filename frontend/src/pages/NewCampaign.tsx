import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { usePlansStore } from "../store/plansStore";
import type { Plan } from "../store/plansStore";

interface SettingsInfo {
  company_name: string | null;
  business_description: string | null;
  business_type: string | null;
}

const BUSINESS_LABELS: Record<string, string> = {
  saas: "SaaS",
  ecommerce: "Ecommerce",
  services: "Servicios",
  app: "App",
  local: "Local",
};

const GARANTIAS = [
  "Ninguna",
  "30 días de devolución",
  "Garantía de satisfacción",
  "Garantía de resultados",
  "Sin permanencia",
];

const ACTIONS = [
  { value: "Agendar una llamada conmigo", needsUrl: true, urlLabel: "Enlace de Calendly / reservas" },
  { value: "Probar el producto gratis (free trial)", needsUrl: true, urlLabel: "URL del registro del trial" },
  { value: "Ver una demo", needsUrl: true, urlLabel: "URL de la demo (si existe)" },
  { value: "Descargar un recurso gratuito", needsUrl: false, urlLabel: "" },
  { value: "Comprar directamente", needsUrl: true, urlLabel: "URL de pricing / checkout" },
  { value: "Dejarme sus datos y ya les contacto yo", needsUrl: false, urlLabel: "" },
];

interface FormState {
  target_customer: string;
  location: string;
  monthly_budget: string;
  precio_base: string;
  transformacion: string;
  garantia: string;
  post_conversion_action: string;
  post_conversion_url: string;
}

const STEPS = ["Tu negocio", "Tu oferta", "Audiencia", "Objetivo"];

export function NewCampaign() {
  const navigate = useNavigate();
  const { upsertPlan } = usePlansStore();
  const [settings, setSettings] = useState<SettingsInfo | null>(null);
  const [loadingSettings, setLoadingSettings] = useState(true);
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>({
    target_customer: "",
    location: "",
    monthly_budget: "",
    precio_base: "",
    transformacion: "",
    garantia: "Ninguna",
    post_conversion_action: ACTIONS[0].value,
    post_conversion_url: "",
  });

  useEffect(() => {
    api
      .get<SettingsInfo>("/settings")
      .then(setSettings)
      .catch(() => {})
      .finally(() => setLoadingSettings(false));
  }, []);

  const set = (k: keyof FormState, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const profileComplete = !!settings?.business_description && !!settings?.business_type;
  const selectedAction = useMemo(
    () => ACTIONS.find((a) => a.value === form.post_conversion_action) ?? ACTIONS[0],
    [form.post_conversion_action]
  );

  const stepValid = (s: number): boolean => {
    switch (s) {
      case 0:
        return profileComplete;
      case 1:
        return form.precio_base.trim() !== "" && form.transformacion.trim() !== "";
      case 2:
        return form.target_customer.trim() !== "" && form.location.trim() !== "" && form.monthly_budget.trim() !== "";
      case 3:
        return form.post_conversion_action.trim() !== "";
      default:
        return true;
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const plan = await api.post<Plan>("/plans/wizard", {
        target_customer: form.target_customer.trim(),
        location: form.location.trim(),
        monthly_budget: Number(form.monthly_budget) || 0,
        precio_base: Number(form.precio_base) || 0,
        transformacion: form.transformacion.trim(),
        garantia: form.garantia,
        post_conversion_action: form.post_conversion_action,
        post_conversion_url: selectedAction.needsUrl ? form.post_conversion_url.trim() || null : null,
      });
      upsertPlan(plan);
      navigate(`/plan/${plan.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo crear la campaña.");
      setSubmitting(false);
    }
  };

  const inputCls =
    "w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500";

  return (
    <div className="flex-1 overflow-y-auto bg-transparent">
      <div className="max-w-2xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-bold text-gray-900">Nueva campaña</h1>
        <p className="text-sm text-gray-500 mt-1">
          Responde unas preguntas y los agentes montarán tu campaña. Tú apruebas cada paso.
        </p>

        {/* Stepper */}
        <div className="flex items-center gap-2 mt-6 mb-8">
          {STEPS.map((label, i) => (
            <div key={label} className="flex items-center gap-2 flex-1">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                  i < step
                    ? "bg-brand-600 text-white"
                    : i === step
                    ? "bg-brand-600 text-white ring-4 ring-brand-100"
                    : "bg-gray-200 text-gray-500"
                }`}
              >
                {i < step ? "✓" : i + 1}
              </div>
              <span className={`text-xs font-medium ${i === step ? "text-gray-900" : "text-gray-400"}`}>
                {label}
              </span>
              {i < STEPS.length - 1 && <div className="flex-1 h-px bg-gray-200" />}
            </div>
          ))}
        </div>

        <div className="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/50 shadow-glass p-6 min-h-[280px]">
          {/* Paso 1 — Negocio */}
          {step === 0 && (
            <div className="space-y-4">
              <h2 className="font-semibold text-gray-900">Tu negocio</h2>
              {loadingSettings ? (
                <p className="text-sm text-gray-400">Cargando…</p>
              ) : profileComplete ? (
                <div className="rounded-lg bg-gray-50 border border-gray-200 p-4 space-y-2">
                  <p className="text-sm">
                    <span className="font-medium text-gray-700">Empresa:</span>{" "}
                    {settings?.company_name || "—"}
                  </p>
                  <p className="text-sm">
                    <span className="font-medium text-gray-700">Tipo:</span>{" "}
                    {BUSINESS_LABELS[settings!.business_type!] ?? settings!.business_type}
                  </p>
                  <p className="text-sm">
                    <span className="font-medium text-gray-700">Descripción:</span>{" "}
                    {settings?.business_description}
                  </p>
                  <Link to="/settings" className="text-xs text-brand-600 underline">
                    Editar en Ajustes
                  </Link>
                </div>
              ) : (
                <div className="rounded-lg bg-amber-50 border border-amber-200 p-4 text-sm text-amber-800">
                  Completa el perfil de tu empresa (descripción y tipo) en{" "}
                  <Link to="/settings" className="font-semibold underline">
                    Ajustes
                  </Link>{" "}
                  antes de crear una campaña.
                </div>
              )}
            </div>
          )}

          {/* Paso 2 — Oferta */}
          {step === 1 && (
            <div className="space-y-4">
              <h2 className="font-semibold text-gray-900">Tu oferta</h2>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Precio del producto/servicio (€)
                </label>
                <input
                  type="number"
                  value={form.precio_base}
                  onChange={(e) => set("precio_base", e.target.value)}
                  placeholder="Ej: 97 (0 si es gratis)"
                  className={inputCls}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ¿Qué resultado concreto consigue el cliente?
                </label>
                <textarea
                  value={form.transformacion}
                  onChange={(e) => set("transformacion", e.target.value)}
                  rows={2}
                  placeholder="Ej: ahorrar 5 horas a la semana, perder 8kg en 2 meses…"
                  className={inputCls}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Garantía</label>
                <select value={form.garantia} onChange={(e) => set("garantia", e.target.value)} className={inputCls}>
                  {GARANTIAS.map((g) => (
                    <option key={g} value={g}>
                      {g}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {/* Paso 3 — Audiencia */}
          {step === 2 && (
            <div className="space-y-4">
              <h2 className="font-semibold text-gray-900">Audiencia y presupuesto</h2>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">¿A quién va dirigido?</label>
                <textarea
                  value={form.target_customer}
                  onChange={(e) => set("target_customer", e.target.value)}
                  rows={2}
                  placeholder="Edad, situación, dolor concreto del cliente ideal…"
                  className={inputCls}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">País o ciudad</label>
                  <input
                    value={form.location}
                    onChange={(e) => set("location", e.target.value)}
                    placeholder="Ej: España, Madrid…"
                    className={inputCls}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Presupuesto mensual (€)</label>
                  <input
                    type="number"
                    value={form.monthly_budget}
                    onChange={(e) => set("monthly_budget", e.target.value)}
                    placeholder="Ej: 300"
                    className={inputCls}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Paso 4 — Objetivo */}
          {step === 3 && (
            <div className="space-y-4">
              <h2 className="font-semibold text-gray-900">¿Qué quieres que haga el cliente?</h2>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Acción tras contactar</label>
                <select
                  value={form.post_conversion_action}
                  onChange={(e) => set("post_conversion_action", e.target.value)}
                  className={inputCls}
                >
                  {ACTIONS.map((a) => (
                    <option key={a.value} value={a.value}>
                      {a.value}
                    </option>
                  ))}
                </select>
              </div>
              {selectedAction.needsUrl && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {selectedAction.urlLabel} <span className="text-gray-400 font-normal">(opcional)</span>
                  </label>
                  <input
                    value={form.post_conversion_url}
                    onChange={(e) => set("post_conversion_url", e.target.value)}
                    placeholder="https://…"
                    className={inputCls}
                  />
                  <p className="text-xs text-gray-400 mt-1">Si no lo tienes, lo gestionamos nosotros.</p>
                </div>
              )}
              <p className="text-xs text-gray-500">
                Tras crear el plan elegirás el tipo de funnel y el modo de testeo (A/B o Multi-Angle).
              </p>
            </div>
          )}

          {error && <p className="text-sm text-red-600 mt-4">{error}</p>}
        </div>

        {/* Navegación */}
        <div className="flex items-center justify-between mt-6">
          <button
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            disabled={step === 0}
            className="px-4 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 disabled:opacity-40"
          >
            ← Atrás
          </button>
          {step < STEPS.length - 1 ? (
            <button
              onClick={() => setStep((s) => s + 1)}
              disabled={!stepValid(step)}
              className="px-5 py-2 rounded-lg text-sm font-semibold bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50"
            >
              Siguiente →
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!stepValid(step) || submitting}
              className="px-5 py-2 rounded-lg text-sm font-semibold bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
            >
              {submitting ? "Creando campaña…" : "Crear campaña"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
