import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { useAuthStore } from "../../store/authStore";
import type { Plan } from "../../store/plansStore";

interface SettingsInfo {
  company_name: string | null;
  business_description: string | null;
  business_type: string | null;
}

interface Props {
  onClose: () => void;
  onCreated: (plan: Plan) => void;
}

const BUSINESS_TYPES = [
  { value: "saas", label: "SaaS" },
  { value: "ecommerce", label: "Ecommerce" },
  { value: "services", label: "Servicios" },
  { value: "app", label: "App" },
  { value: "local", label: "Negocio local" },
];

export function ResearchGenerateModal({ onClose, onCreated }: Props) {
  const { features, fetchFeatures } = useAuthStore();
  const [settings, setSettings] = useState<SettingsInfo | null>(null);
  const [targetCustomer, setTargetCustomer] = useState("");
  const [objective, setObjective] = useState("");
  // Override de empresa/producto: vacío → tira con la empresa del perfil (Settings)
  const [businessOverride, setBusinessOverride] = useState("");
  const [businessTypeOverride, setBusinessTypeOverride] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<SettingsInfo>("/settings").then(setSettings).catch(() => {});
  }, []);

  const placeholder = settings?.business_description
    ? `Ej: el cliente ideal de "${settings.business_description}"`
    : "Describe a quién va dirigido (edad, situación, dolor concreto)…";

  // Descripción/tipo efectivos: override si se rellenó, si no el perfil
  const effectiveDescription = businessOverride.trim() || settings?.business_description || "";
  const effectiveType = businessTypeOverride || settings?.business_type || "";
  const canResolveBusiness = Boolean(effectiveDescription && effectiveType);

  const scans = features?.scans_remaining ?? null;
  const noScans = scans !== null && scans <= 0;

  const handleSubmit = async () => {
    if (!targetCustomer.trim()) {
      setError("Indica la audiencia objetivo.");
      return;
    }
    if (!canResolveBusiness) {
      setError("Describe la empresa/producto o complétalo en Ajustes.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const plan = await api.post<Plan>("/plans/research", {
        target_customer: targetCustomer.trim(),
        objective: objective.trim() || null,
        // Solo se envía override si el usuario lo rellenó; si va null, el backend usa el perfil
        business_description: businessOverride.trim() || null,
        business_type: businessTypeOverride || null,
      });
      await fetchFeatures(); // refresca saldo de escaneos
      onCreated(plan);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo generar el research.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <div
        className="w-full max-w-lg rounded-2xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <h2 className="text-lg font-bold text-gray-900">Generar nuevo research</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700 text-xl leading-none">
            ×
          </button>
        </div>

        <div className="px-6 py-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Empresa / producto{" "}
              <span className="text-gray-400 font-normal">(opcional)</span>
            </label>
            <textarea
              value={businessOverride}
              onChange={(e) => setBusinessOverride(e.target.value)}
              placeholder={
                settings?.business_description
                  ? `Por defecto: ${settings.business_description}`
                  : "Describe qué hace la empresa o producto del research…"
              }
              rows={2}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
            <div className="mt-2 flex items-center gap-2">
              <select
                value={businessTypeOverride}
                onChange={(e) => setBusinessTypeOverride(e.target.value)}
                className="rounded-lg border border-gray-300 px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="">
                  Tipo{settings?.business_type ? ` (perfil: ${settings.business_type})` : ""}
                </option>
                {BUSINESS_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-400">
                Vacío → usa el negocio de{" "}
                <Link to="/settings" className="text-brand-600 underline">
                  Ajustes
                </Link>
                .
              </p>
            </div>
            {!canResolveBusiness && (
              <p className="mt-2 rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-800">
                No hay empresa en tu perfil. Describe la empresa/producto aquí o complétalo en{" "}
                <Link to="/settings" className="font-semibold underline">
                  Ajustes
                </Link>
                .
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Audiencia objetivo</label>
            <textarea
              value={targetCustomer}
              onChange={(e) => setTargetCustomer(e.target.value)}
              placeholder={placeholder}
              rows={3}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Objetivo <span className="text-gray-400 font-normal">(opcional)</span>
            </label>
            <input
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              placeholder="Ej: captar leads para una mentoría de ventas"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          {scans !== null && (
            <p className="text-xs text-gray-500">
              Escaneos restantes este ciclo:{" "}
              <span className={`font-semibold ${noScans ? "text-red-600" : "text-gray-800"}`}>{scans}</span>
              {noScans && (
                <>
                  {" "}— sin saldo. Mejora tu plan o espera al reinicio.
                </>
              )}
            </p>
          )}
        </div>

        <div className="flex justify-end gap-2 border-t border-gray-100 px-6 py-4">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100"
          >
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting || noScans || !canResolveBusiness}
            className="px-4 py-2 rounded-lg text-sm font-semibold bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {submitting ? "Generando…" : "Generar research"}
          </button>
        </div>
      </div>
    </div>
  );
}
