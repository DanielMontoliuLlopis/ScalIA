import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { closerApi } from "../lib/closerApi";
import { useCloserAuthStore } from "../store/closerAuthStore";

interface MonthlyCommission {
  month: string;
  label: string;
  count: number;
  first_quota_cents: number;
  recurring_cents: number;
  total_cents: number;
  pending_cents: number;
  paid_cents: number;
}

interface Dashboard {
  currency: string;
  clients_count: number;
  active_clients_count: number;
  total_earned_cents: number;
  pending_cents: number;
  paid_cents: number;
  months: MonthlyCommission[];
}

const fmt = (cents: number, currency = "eur") =>
  new Intl.NumberFormat("es-ES", { style: "currency", currency: currency.toUpperCase() }).format(
    cents / 100
  );

export function CloserDashboard() {
  const { closer, logout, fetchMe } = useCloserAuthStore();
  const navigate = useNavigate();
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchMe();
    closerApi
      .get<Dashboard>("/closer-portal/dashboard")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/closer/login");
  };

  const referralLink = closer
    ? `${window.location.origin}/?ref=${closer.referral_code}`
    : "";

  return (
    <div className="min-h-screen bg-transparent">
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl">🤝</span>
          <div>
            <h1 className="font-bold text-gray-900 leading-tight">
              {closer?.full_name ?? "Mi panel"}
            </h1>
            <p className="text-xs text-gray-400">
              Comisión recurrente {closer ? (closer.commission_rate * 100).toFixed(0) : 6}%
            </p>
          </div>
        </div>
        <button onClick={handleLogout} className="text-sm text-gray-500 hover:text-gray-700">
          Cerrar sesión
        </button>
      </header>

      <main className="p-6 max-w-5xl mx-auto space-y-6">
        {error && <div className="bg-red-50 text-red-700 text-sm rounded-lg p-3">{error}</div>}

        {/* Link referido */}
        {referralLink && (
          <div className="bg-white/70 backdrop-blur-xl rounded-xl border border-white/50 shadow-glass p-4 flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="text-xs text-gray-500 mb-0.5">Tu link de referido</p>
              <code className="text-sm text-brand-600 break-all">{referralLink}</code>
            </div>
            <button
              onClick={() => navigator.clipboard.writeText(referralLink)}
              className="shrink-0 px-3 py-1.5 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
            >
              Copiar
            </button>
          </div>
        )}

        {!data ? (
          <p className="text-center py-12 text-gray-400 text-sm">Cargando…</p>
        ) : (
          <>
            {/* Totales */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <Card label="Total generado" value={fmt(data.total_earned_cents, data.currency)} />
              <Card label="Pendiente de cobro" value={fmt(data.pending_cents, data.currency)} accent="amber" />
              <Card label="Cobrado" value={fmt(data.paid_cents, data.currency)} accent="emerald" />
              <Card
                label="Clientes"
                value={`${data.active_clients_count} activos / ${data.clients_count}`}
              />
            </div>

            {/* Desglose mensual */}
            <div className="bg-white/70 backdrop-blur-xl rounded-xl border border-white/50 shadow-glass overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-100">
                <h2 className="font-semibold text-gray-900 text-sm">Comisiones por mes</h2>
              </div>
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-500 text-left">
                  <tr>
                    <th className="px-5 py-3 font-medium">Mes</th>
                    <th className="px-5 py-3 font-medium">Pagos</th>
                    <th className="px-5 py-3 font-medium">1ª cuota</th>
                    <th className="px-5 py-3 font-medium">Recurrente</th>
                    <th className="px-5 py-3 font-medium">Total</th>
                    <th className="px-5 py-3 font-medium">Pendiente</th>
                    <th className="px-5 py-3 font-medium">Cobrado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.months.map((m) => (
                    <tr key={m.month} className="hover:bg-gray-50">
                      <td className="px-5 py-3 font-medium text-gray-900">{m.label}</td>
                      <td className="px-5 py-3 text-gray-500">{m.count}</td>
                      <td className="px-5 py-3 text-violet-600">{fmt(m.first_quota_cents, data.currency)}</td>
                      <td className="px-5 py-3 text-sky-600">{fmt(m.recurring_cents, data.currency)}</td>
                      <td className="px-5 py-3 font-medium text-gray-900">{fmt(m.total_cents, data.currency)}</td>
                      <td className="px-5 py-3 text-amber-600">{fmt(m.pending_cents, data.currency)}</td>
                      <td className="px-5 py-3 text-emerald-600">{fmt(m.paid_cents, data.currency)}</td>
                    </tr>
                  ))}
                  {data.months.length === 0 && (
                    <tr>
                      <td colSpan={7} className="px-5 py-8 text-center text-gray-400">
                        Todavía no tienes comisiones. Comparte tu link de referido.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

function Card({ label, value, accent }: { label: string; value: string; accent?: "amber" | "emerald" }) {
  return (
    <div className="bg-white/70 backdrop-blur-xl rounded-xl border border-white/50 shadow-glass p-5">
      <p className="text-sm text-gray-500">{label}</p>
      <p
        className={`text-xl font-bold mt-1 ${
          accent === "amber" ? "text-amber-600" : accent === "emerald" ? "text-emerald-600" : "text-gray-900"
        }`}
      >
        {value}
      </p>
    </div>
  );
}
