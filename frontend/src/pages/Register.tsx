import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuthStore, type BusinessType } from "../store/authStore";

const BUSINESS_OPTIONS: { value: BusinessType; label: string; emoji: string }[] = [
  { value: "saas", label: "SaaS / Software", emoji: "💻" },
  { value: "ecommerce", label: "Ecommerce / Tienda", emoji: "🛒" },
  { value: "services", label: "Servicios / Consultoría", emoji: "🤝" },
  { value: "app", label: "App móvil", emoji: "📱" },
  { value: "local", label: "Negocio local", emoji: "📍" },
];

export function Register() {
  const { register } = useAuthStore();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const preselectedPlan = params.get("plan");

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [businessType, setBusinessType] = useState<BusinessType | "">("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const refCode = params.get("ref") || localStorage.getItem("ref_code") || undefined;
      await register({
        email,
        password,
        full_name: fullName,
        phone: phone || undefined,
        business_type: businessType || undefined,
        ref_code: refCode,
      });
      localStorage.removeItem("ref_code");
      const planQs = preselectedPlan ? `?plan=${preselectedPlan}` : "";
      navigate(`/onboarding/plan${planQs}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al registrarse");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-50 via-white to-violet-50 flex items-center justify-center p-4">
      <div className="bg-white/90 backdrop-blur-2xl rounded-2xl shadow-glass-lg border border-gray-200 p-8 w-full max-w-md">
        <Link to="/" className="text-2xl font-bold text-gray-900">
          Scal<span className="text-brand-600">IA</span>
        </Link>
        <h1 className="text-xl font-semibold text-gray-900 mt-4">Crea tu cuenta</h1>
        <p className="text-gray-500 text-sm mb-6">
          {preselectedPlan
            ? `Plan ${preselectedPlan} preseleccionado. Trial 7 días, cobro automático tras el periodo.`
            : "Trial 7 días con tarjeta. Cancela cuando quieras."}
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre completo *
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              minLength={2}
              placeholder="María García"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="tu@empresa.com"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Teléfono <span className="text-gray-400">(opcional)</span>
            </label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+34 600 000 000"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tipo de negocio *
            </label>
            <div className="grid grid-cols-2 gap-2">
              {BUSINESS_OPTIONS.map((opt) => (
                <button
                  type="button"
                  key={opt.value}
                  onClick={() => setBusinessType(opt.value)}
                  className={`text-left text-sm px-3 py-2 rounded-lg border transition-colors ${
                    businessType === opt.value
                      ? "border-brand-500 bg-brand-50 text-brand-700"
                      : "border-gray-300 text-gray-700 hover:border-gray-400"
                  }`}
                >
                  <span className="mr-1">{opt.emoji}</span>
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña *</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              placeholder="Mínimo 8 caracteres"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
            />
          </div>

          {error && <p className="text-red-600 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={loading || !businessType}
            className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2.5 rounded-lg text-sm transition-colors"
          >
            {loading ? "Creando cuenta…" : "Continuar al pago"}
          </button>
        </form>

        <p className="text-center text-xs text-gray-400 mt-4">
          Al registrarte aceptas nuestros términos y política de privacidad.
        </p>

        <p className="text-center text-sm text-gray-500 mt-4">
          ¿Ya tienes cuenta?{" "}
          <Link to="/login" className="text-brand-600 hover:underline font-medium">
            Inicia sesión
          </Link>
        </p>
      </div>
    </div>
  );
}
