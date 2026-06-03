import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../lib/api";
import { useAuthStore } from "../store/authStore";
import { TeamSection } from "../components/settings/TeamSection";

interface UserSettings {
  id: string;
  meta_pixel_id: string | null;
  meta_ad_account_id: string | null;
  color_palette: string;
  logo_url: string | null;
  company_name: string | null;
  business_description: string | null;
  business_type: string | null;
  has_meta_token?: boolean;
  has_resend_key?: boolean;
  resend_from_email?: string | null;
  whatsapp_phone_number_id?: string | null;
  whatsapp_phone_display?: string | null;
}

const BUSINESS_TYPES = [
  { value: "saas",      label: "SaaS / Software B2B" },
  { value: "ecommerce", label: "Ecommerce / Tienda online" },
  { value: "services",  label: "Servicios / Consultoría / Agencia" },
  { value: "app",       label: "App móvil / web de consumo" },
  { value: "local",     label: "Negocio local / físico" },
];

interface AdAccount {
  id: string;
  name: string;
  account_status: number;
  currency: string;
  timezone_name: string;
}

interface Page {
  id: string;
  name: string;
  category: string;
}

const PALETTES = [
  { name: "indigo",  label: "Tech / SaaS",         primary: "#6366f1", secondary: "#e0e7ff" },
  { name: "emerald", label: "Fintech / Salud",      primary: "#10b981", secondary: "#d1fae5" },
  { name: "violet",  label: "Creativo / Marketing", primary: "#8b5cf6", secondary: "#ede9fe" },
  { name: "sky",     label: "Productividad",        primary: "#0ea5e9", secondary: "#e0f2fe" },
  { name: "rose",    label: "Ecommerce / Lifestyle", primary: "#f43f5e", secondary: "#ffe4e6" },
  { name: "amber",   label: "Educación / Consulting", primary: "#f59e0b", secondary: "#fef3c7" },
  { name: "cyan",    label: "Datos / Analytics / IA", primary: "#06b6d4", secondary: "#cffafe" },
  { name: "slate",   label: "Enterprise / Legal / B2B", primary: "#475569", secondary: "#f1f5f9" },
  { name: "orange",  label: "Retail / Energía",    primary: "#f97316", secondary: "#ffedd5" },
  { name: "teal",    label: "Bienestar / RRHH",    primary: "#14b8a6", secondary: "#ccfbf1" },
];

export function Settings() {
  const [searchParams] = useSearchParams();
  const [, setSettings] = useState<UserSettings | null>(null);
  const [form, setForm] = useState({
    company_name: "",
    business_description: "",
    business_type: "",
    meta_pixel_id: "",
    logo_url: "",
    color_palette: "indigo",
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Resend state
  const [resendForm, setResendForm] = useState({ resend_api_key: "", resend_from_email: "" });
  const [hasResendKey, setHasResendKey] = useState(false);
  const [savingResend, setSavingResend] = useState(false);
  const [savedResend, setSavedResend] = useState(false);

  // WhatsApp state
  const [waForm, setWaForm] = useState({ whatsapp_phone_number_id: "", whatsapp_phone_display: "" });
  const [savingWA, setSavingWA] = useState(false);
  const [savedWA, setSavedWA] = useState(false);

  // Meta OAuth state
  const [metaConnected, setMetaConnected] = useState(false);
  const [connectingMeta, setConnectingMeta] = useState(false);
  const [adAccounts, setAdAccounts] = useState<AdAccount[]>([]);
  const [pages, setPages] = useState<Page[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<string>("");
  const [selectedPage, setSelectedPage] = useState<string>("");
  const [savingAccount, setSavingAccount] = useState(false);
  const [accountSaved, setAccountSaved] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [creatingPixel, setCreatingPixel] = useState(false);

  useEffect(() => {
    api.get<UserSettings & { has_meta_token: boolean }>("/settings").then((s) => {
      setSettings(s);
      setForm({
        company_name: s.company_name ?? "",
        business_description: s.business_description ?? "",
        business_type: s.business_type ?? "",
        meta_pixel_id: s.meta_pixel_id ?? "",
        logo_url: s.logo_url ?? "",
        color_palette: s.color_palette ?? "indigo",
      });
      setMetaConnected(!!s.has_meta_token);
      if (s.meta_ad_account_id) setSelectedAccount(s.meta_ad_account_id);
      setHasResendKey(!!s.has_resend_key);
      setResendForm((f) => ({ ...f, resend_from_email: s.resend_from_email ?? "" }));
      setWaForm({
        whatsapp_phone_number_id: s.whatsapp_phone_number_id ?? "",
        whatsapp_phone_display: s.whatsapp_phone_display ?? "",
      });
    });
  }, []);

  // Tras redirigir desde Meta OAuth callback
  useEffect(() => {
    if (searchParams.get("meta") === "connected") {
      setMetaConnected(true);
      loadAdAccounts();
    }
  }, [searchParams]);

  const loadAdAccounts = async () => {
    try {
      const data = await api.get<{ ad_accounts: AdAccount[] }>("/meta/ad-accounts");
      setAdAccounts(data.ad_accounts);
    } catch {
      // token inválido o sin permisos
    }
    try {
      const data = await api.get<{ pages: Page[] }>("/meta/pages");
      setPages(data.pages);
    } catch {
      // sin pages
    }
  };

  useEffect(() => {
    if (metaConnected) loadAdAccounts();
  }, [metaConnected]);

  const handleConnectMeta = async () => {
    setConnectingMeta(true);
    try {
      const { url } = await api.get<{ url: string }>("/meta/connect-url");
      window.location.href = url;
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Error obteniendo URL de Meta");
      setConnectingMeta(false);
    }
  };

  const handleDisconnect = async () => {
setDisconnecting(true);
    try {
      await api.delete("/meta/disconnect");
      setMetaConnected(false);
      setAdAccounts([]);
      setPages([]);
      setSelectedAccount("");
      setSelectedPage("");
      setSettings((s) => s ? { ...s, meta_ad_account_id: null, meta_pixel_id: null } : s);
    } finally {
      setDisconnecting(false);
    }
  };

  const handleCreatePixel = async () => {
    setCreatingPixel(true);
    try {
      const data = await api.post<{ pixel_id: string }>("/settings/meta/create-pixel", {});
      setForm((f) => ({ ...f, meta_pixel_id: data.pixel_id }));
      setSettings((s) => s ? { ...s, meta_pixel_id: data.pixel_id } : s);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Error creando pixel");
    } finally {
      setCreatingPixel(false);
    }
  };

  const handleSaveAccount = async () => {
    if (!selectedAccount) return;
    setSavingAccount(true);
    try {
      await api.post("/meta/select-account", {
        ad_account_id: selectedAccount,
        meta_pixel_id: form.meta_pixel_id || undefined,
      });
      if (selectedPage) {
        await api.post("/meta/select-page", { page_id: selectedPage });
      }
      setAccountSaved(true);
      setTimeout(() => setAccountSaved(false), 2500);
    } finally {
      setSavingAccount(false);
    }
  };

  const handleSaveResend = async () => {
    setSavingResend(true);
    try {
      await api.put("/settings", {
        resend_api_key: resendForm.resend_api_key || null,
        resend_from_email: resendForm.resend_from_email || null,
      });
      if (resendForm.resend_api_key) setHasResendKey(true);
      setResendForm((f) => ({ ...f, resend_api_key: "" }));
      setSavedResend(true);
      setTimeout(() => setSavedResend(false), 2500);
    } finally {
      setSavingResend(false);
    }
  };

  const handleSaveWhatsApp = async () => {
    setSavingWA(true);
    try {
      await api.put("/settings", {
        whatsapp_phone_number_id: waForm.whatsapp_phone_number_id || null,
        whatsapp_phone_display: waForm.whatsapp_phone_display || null,
      });
      setSavedWA(true);
      setTimeout(() => setSavedWA(false), 2500);
    } finally {
      setSavingWA(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload: Record<string, string | null> = {
        company_name: form.company_name || null,
        business_description: form.business_description || null,
        business_type: form.business_type || null,
        logo_url: form.logo_url || null,
        color_palette: form.color_palette,
      };
      const updated = await api.put<UserSettings>("/settings", payload);
      setSettings(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 max-w-2xl mx-auto w-full">
      <h1 className="text-xl font-bold text-gray-900 mb-6">Configuración</h1>

      <div className="space-y-6">
        <SubscriptionSection />

        <TeamSection />

        {/* Tu empresa — obligatorio para crear campañas */}
        <section className="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/50 shadow-glass p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-800">Tu empresa</h2>
            {(!form.company_name || !form.business_description || !form.business_type) && (
              <span className="text-xs font-medium text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-2.5 py-1">
                Requerido para crear campañas
              </span>
            )}
          </div>
          <Field
            label="Nombre de la empresa"
            value={form.company_name}
            onChange={(v) => setForm({ ...form, company_name: v })}
            placeholder="Mi SaaS S.L."
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tipo de negocio
            </label>
            <select
              value={form.business_type}
              onChange={(e) => setForm({ ...form, business_type: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
            >
              <option value="">— Selecciona —</option>
              {BUSINESS_TYPES.map((bt) => (
                <option key={bt.value} value={bt.value}>{bt.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descripción del negocio
            </label>
            <textarea
              value={form.business_description}
              onChange={(e) => setForm({ ...form, business_description: e.target.value })}
              placeholder="Ej: SaaS de gestión de facturas para autónomos y pymes en España. Automatiza el proceso de facturación y reduce el tiempo de gestión un 80%."
              rows={3}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 resize-none"
            />
            <p className="text-xs text-gray-400 mt-1">
              Esta descripción se usa en todos los agentes. Cuanto más específica, mejor el resultado.
            </p>
          </div>
        </section>

        {/* General */}
        <section className="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/50 shadow-glass p-5 space-y-4">
          <h2 className="font-semibold text-gray-800">General</h2>
          <Field label="URL del logo" value={form.logo_url} onChange={(v) => setForm({ ...form, logo_url: v })} placeholder="https://..." />
        </section>

        {/* Meta Ads — OAuth */}
        <section className="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/50 shadow-glass p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-800">Meta Ads</h2>
            {metaConnected && (
              <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2.5 py-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
                Conectado
              </span>
            )}
          </div>

          {!metaConnected ? (
            <div className="space-y-3">
              <p className="text-xs text-gray-500">
                Conecta tu cuenta de Meta para publicar campañas directamente desde la plataforma.
              </p>
              <button
                onClick={handleConnectMeta}
                disabled={connectingMeta}
                className="w-full flex items-center justify-center gap-2 bg-[#1877F2] hover:bg-[#166FE5] disabled:opacity-60 text-white font-medium py-2.5 rounded-xl text-sm transition-colors"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                </svg>
                {connectingMeta ? "Redirigiendo…" : "Conectar con Facebook / Meta"}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Selector de Ad Account */}
              {adAccounts.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Cuenta publicitaria
                  </label>
                  <select
                    value={selectedAccount}
                    onChange={(e) => setSelectedAccount(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                  >
                    <option value="">— Selecciona una cuenta —</option>
                    {adAccounts.map((acc) => (
                      <option key={acc.id} value={acc.id}>
                        {acc.name} ({acc.id}) · {acc.currency}
                        {acc.account_status !== 1 ? " ⚠️" : ""}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Selector de Page */}
              {pages.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Página de Facebook para los anuncios
                  </label>
                  <select
                    value={selectedPage}
                    onChange={(e) => setSelectedPage(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                  >
                    <option value="">— Selecciona una página —</option>
                    {pages.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} — {p.category}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Entrada manual (sandbox / cuentas que no aparecen en el dropdown) */}
              <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-3 space-y-3">
                <p className="text-xs text-gray-500">
                  ¿Cuenta sandbox o no aparece arriba? Pega el ID a mano (formato <code>act_123…</code> o solo el número).
                </p>
                <Field
                  label="Ad Account ID manual"
                  value={selectedAccount}
                  onChange={(v) => setSelectedAccount(v)}
                  placeholder="act_1889356911727041"
                />
                <Field
                  label="Page ID manual"
                  value={selectedPage}
                  onChange={(v) => setSelectedPage(v)}
                  placeholder="542745208925695"
                />
              </div>

              {/* Pixel ID */}
              <div>
                <Field
                  label="Pixel ID (opcional)"
                  value={form.meta_pixel_id}
                  onChange={(v) => setForm({ ...form, meta_pixel_id: v })}
                  placeholder="1234567890"
                />
                {!form.meta_pixel_id && selectedAccount && (
                  <button
                    onClick={handleCreatePixel}
                    disabled={creatingPixel}
                    className="mt-1.5 text-xs text-brand-600 hover:text-brand-800 disabled:opacity-50 underline underline-offset-2"
                  >
                    {creatingPixel ? "Creando pixel…" : "Crear pixel nuevo en esta cuenta"}
                  </button>
                )}
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleSaveAccount}
                  disabled={savingAccount || !selectedAccount}
                  className="flex-1 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-medium py-2 rounded-xl text-sm transition-colors"
                >
                  {savingAccount ? "Guardando…" : accountSaved ? "✓ Guardado" : "Guardar configuración Meta"}
                </button>
                <button
                  onClick={handleDisconnect}
                  disabled={disconnecting}
                  className="px-4 py-2 text-sm text-red-600 border border-red-200 rounded-xl hover:bg-red-50 transition-colors disabled:opacity-50"
                >
                  {disconnecting ? "…" : "Desconectar"}
                </button>
              </div>

              {adAccounts.length === 0 && (
                <p className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-lg p-3">
                  No se encontraron cuentas publicitarias. Asegúrate de que tu cuenta tiene acceso al Business Manager correcto.
                </p>
              )}
            </div>
          )}
        </section>

        {/* Paleta */}
        <section className="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/50 shadow-glass p-5 space-y-4">
          <h2 className="font-semibold text-gray-800">Paleta de color para landings</h2>
          <p className="text-xs text-gray-400">El agente usará esta paleta al generar las landing pages.</p>
          <div className="grid grid-cols-2 gap-2">
            {PALETTES.map((p) => (
              <button
                key={p.name}
                onClick={() => setForm({ ...form, color_palette: p.name })}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl border-2 text-left transition-all ${
                  form.color_palette === p.name ? "border-gray-900 shadow-sm" : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <div className="flex gap-1 shrink-0">
                  <div className="w-5 h-5 rounded-full" style={{ backgroundColor: p.primary }} />
                  <div className="w-5 h-5 rounded-full" style={{ backgroundColor: p.secondary }} />
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-800">{p.label}</p>
                  <p className="text-xs text-gray-400">{p.primary}</p>
                </div>
                {form.color_palette === p.name && (
                  <span className="ml-auto text-xs font-bold text-gray-900">✓</span>
                )}
              </button>
            ))}
          </div>
        </section>

        {/* Resend */}
        <section className="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/50 shadow-glass p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-800">Email (Resend)</h2>
            {hasResendKey && (
              <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2.5 py-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
                API key configurada
              </span>
            )}
          </div>
          <p className="text-xs text-gray-400">
            Los emails de nurturing se envían desde tu cuenta de Resend.
            La API key no se muestra una vez guardada.
          </p>
          <Field
            label={hasResendKey ? "Nueva API key (dejar vacío para mantener la actual)" : "API key de Resend"}
            value={resendForm.resend_api_key}
            onChange={(v) => setResendForm({ ...resendForm, resend_api_key: v })}
            placeholder="re_..."
            type="password"
          />
          <Field
            label="Email remitente"
            value={resendForm.resend_from_email}
            onChange={(v) => setResendForm({ ...resendForm, resend_from_email: v })}
            placeholder="hola@tudominio.com"
          />
          <button
            onClick={handleSaveResend}
            disabled={savingResend}
            className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-medium py-2 rounded-xl text-sm transition-colors"
          >
            {savingResend ? "Guardando…" : savedResend ? "✓ Guardado" : "Guardar configuración Resend"}
          </button>
        </section>

        {/* WhatsApp Business */}
        <section className="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/50 shadow-glass p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-800">WhatsApp Business</h2>
            {waForm.whatsapp_phone_number_id && (
              <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2.5 py-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
                Configurado
              </span>
            )}
          </div>
          <p className="text-xs text-gray-400">
            Los mensajes de WhatsApp se envían vía tu número de WhatsApp Business usando el token de Meta ya conectado.
            Necesitas tener Meta conectado arriba.
          </p>
          <div className="flex items-start gap-2 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 text-xs text-blue-700">
            <span>ℹ️</span>
            <span>Encuentra el <strong>Phone Number ID</strong> en <strong>Meta for Developers → WhatsApp → Getting Started</strong>.</span>
          </div>
          <Field
            label="Phone Number ID"
            value={waForm.whatsapp_phone_number_id}
            onChange={(v) => setWaForm({ ...waForm, whatsapp_phone_number_id: v })}
            placeholder="123456789012345"
          />
          <Field
            label="Número visible (opcional)"
            value={waForm.whatsapp_phone_display}
            onChange={(v) => setWaForm({ ...waForm, whatsapp_phone_display: v })}
            placeholder="+34 600 000 000"
          />
          <button
            onClick={handleSaveWhatsApp}
            disabled={savingWA || !metaConnected}
            className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-medium py-2 rounded-xl text-sm transition-colors"
          >
            {!metaConnected
              ? "Conecta Meta primero"
              : savingWA
              ? "Guardando…"
              : savedWA
              ? "✓ Guardado"
              : "Guardar configuración WhatsApp"}
          </button>
        </section>

        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-medium py-2.5 rounded-xl text-sm transition-colors"
        >
          {saving ? "Guardando…" : saved ? "✓ Guardado" : "Guardar cambios"}
        </button>
      </div>
    </div>
  );
}

function Field({
  label, value, onChange, placeholder, type = "text",
}: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string; type?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
      />
    </div>
  );
}

function SubscriptionSection() {
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(false);

  if (!user) return null;

  const statusLabel: Record<string, { text: string; color: string }> = {
    trialing: { text: "Trial activo", color: "bg-amber-50 text-amber-700 border-amber-200" },
    active: { text: "Activa", color: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    past_due: { text: "Pago atrasado", color: "bg-orange-50 text-orange-700 border-orange-200" },
    canceled: { text: "Cancelada", color: "bg-gray-100 text-gray-600 border-gray-200" },
    unpaid: { text: "Impagada", color: "bg-red-50 text-red-700 border-red-200" },
  };
  const status = user.subscription_status || "inactive";
  const badge = statusLabel[status] || { text: status, color: "bg-gray-100 text-gray-600 border-gray-200" };

  const periodEnd = user.subscription_current_period_end
    ? new Date(user.subscription_current_period_end).toLocaleDateString()
    : null;

  const openPortal = async () => {
    setLoading(true);
    try {
      const { url } = await api.post<{ url: string }>("/billing/portal-session", {});
      window.location.href = url;
    } catch (err) {
      alert(err instanceof Error ? err.message : "Error abriendo portal");
      setLoading(false);
    }
  };

  return (
    <section className="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/50 shadow-glass p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-gray-800">Suscripción</h2>
        <span className={`text-xs font-medium border rounded-full px-2.5 py-1 ${badge.color}`}>
          {badge.text}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <div className="text-gray-500 text-xs">Plan actual</div>
          <div className="font-medium text-gray-900 capitalize">{user.plan}</div>
        </div>
        <div>
          <div className="text-gray-500 text-xs">Campañas activas máx.</div>
          <div className="font-medium text-gray-900">
            {user.active_campaigns_limit >= 9999 ? "Ilimitadas" : user.active_campaigns_limit}
          </div>
        </div>
        {periodEnd && (
          <div className="col-span-2">
            <div className="text-gray-500 text-xs">
              {status === "trialing" ? "Trial finaliza" : "Próximo cobro"}
            </div>
            <div className="font-medium text-gray-900">{periodEnd}</div>
          </div>
        )}
      </div>

      {user.stripe_customer_id || status !== "inactive" ? (
        <button
          onClick={openPortal}
          disabled={loading}
          className="w-full bg-gray-900 hover:bg-gray-800 disabled:opacity-60 text-white text-sm font-medium py-2.5 rounded-lg transition-colors"
        >
          {loading ? "Abriendo portal…" : "Gestionar suscripción / facturas"}
        </button>
      ) : (
        <a
          href="/onboarding/plan"
          className="block text-center bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium py-2.5 rounded-lg transition-colors"
        >
          Activar suscripción
        </a>
      )}
    </section>
  );
}
