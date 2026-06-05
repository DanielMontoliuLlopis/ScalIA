import { useEffect } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";
import { usePlansStore } from "../../store/plansStore";
import { useClientStore } from "../../store/clientStore";

const PLAN_STATUS_LABEL: Record<string, string> = {
  pending_approval: "Pendiente",
  approved: "Aprobado",
  executing: "Ejecutando",
  awaiting_creative_choice: "Elige creativo",
  pending_copy_approval: "Revisa copies",
  awaiting_funnel_choice: "Elige funnel",
  pending_ads_approval: "Revisa ads",
  done: "Completado",
};

export function Layout() {
  const { user, features, logout } = useAuthStore();
  const navigate = useNavigate();
  const { plans, fetchPlans } = usePlansStore();
  const { clientAccounts, activeClientId, setActiveClient } = useClientStore();
  const isAgency = user?.plan === "agency";
  // Usuarios Research Mode: solo ven Research + Ajustes (resto de pestañas ocultas)
  const researchOnly = features?.research_only ?? false;

  useEffect(() => {
    if (!researchOnly) fetchPlans();
  }, [researchOnly]);

  const handleSwitchClient = (id: string) => {
    if (id === activeClientId) return;
    setActiveClient(id);
    // Recarga completa para limpiar datos cacheados del workspace anterior.
    window.location.reload();
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  // Campañas en curso (no research, no terminadas/rechazadas) — reemplazan el historial de chat
  const activePlans = plans
    .filter((p) => !p.research_export && p.status !== "done" && p.status !== "rejected")
    .sort((a, b) => b.created_at.localeCompare(a.created_at));

  return (
    <div className="flex h-screen">
      <aside className="w-60 m-3 mr-0 glass flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-white/40">
          <h1 className="font-bold text-lg bg-brand-gradient bg-clip-text text-transparent">ScalIA</h1>
          <p className="text-xs text-slate-400 truncate">{user?.email}</p>

          {/* Selector de cliente (agency) */}
          {isAgency && clientAccounts.length > 0 && (
            <div className="mt-2">
              <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">
                Cliente activo
              </label>
              <select
                value={activeClientId ?? ""}
                onChange={(e) => handleSwitchClient(e.target.value)}
                className="mt-1 w-full text-xs bg-white/60 border border-white/50 rounded-lg px-2 py-1.5 text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-400"
              >
                {clientAccounts.map((ca) => (
                  <option key={ca.id} value={ca.id}>
                    {ca.name}
                  </option>
                ))}
              </select>
            </div>
          )}
          {!isAgency && clientAccounts[0] && (
            <p className="mt-1 text-xs text-slate-500 truncate">{clientAccounts[0].name}</p>
          )}
        </div>

        {/* Nueva campaña */}
        {!researchOnly && (
          <div className="p-3 border-b border-white/40">
            <NavLink
              to="/campaigns/new"
              className="w-full flex items-center justify-center gap-2 px-3 py-2 btn-brand text-sm"
            >
              <span className="text-base">＋</span>
              Nueva campaña
            </NavLink>
          </div>
        )}

        {/* Campañas en curso */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {!researchOnly && activePlans.length > 0 && (
            <>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide px-2 mb-2">En curso</p>
              {activePlans.map((plan) => (
                <NavLink
                  key={plan.id}
                  to={`/plan/${plan.id}`}
                  className={({ isActive }) =>
                    `block px-3 py-2 rounded-xl text-sm transition ${
                      isActive ? "bg-white/70 text-brand-700 font-medium shadow-glass" : "text-slate-600 hover:bg-white/50"
                    }`
                  }
                >
                  <span className="block truncate">{plan.title}</span>
                  <span className="block text-[10px] text-slate-400 mt-0.5">
                    {PLAN_STATUS_LABEL[plan.status] ?? plan.status}
                  </span>
                </NavLink>
              ))}
            </>
          )}
        </div>

        {/* Nav inferior */}
        <nav className="p-3 border-t border-white/40 space-y-1">
          <NavLink
            to="/research"
            className={({ isActive }) =>
              `nav-item ${isActive ? "nav-item-active" : ""}`
            }
          >
            <span>🔬</span>
            Research
          </NavLink>
          {!researchOnly && (
            <NavLink
              to="/campaigns"
              className={({ isActive }) =>
                `nav-item ${isActive ? "nav-item-active" : ""}`
              }
            >
              <span>📣</span>
              Mis Campañas
            </NavLink>
          )}
          {!researchOnly && (
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                `nav-item ${isActive ? "nav-item-active" : ""}`
              }
            >
              <span>📊</span>
              Dashboard
            </NavLink>
          )}
          {!researchOnly && (
            <NavLink
              to="/lead-forms"
              className={({ isActive }) =>
                `nav-item ${isActive ? "nav-item-active" : ""}`
              }
            >
              <span>📝</span>
              Formularios
            </NavLink>
          )}
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `nav-item ${isActive ? "nav-item-active" : ""}`
            }
          >
            <span>⚙️</span>
            Ajustes
          </NavLink>
          {isAgency && (
            <NavLink
              to="/clients"
              className={({ isActive }) =>
                `nav-item ${isActive ? "nav-item-active" : ""}`
              }
            >
              <span>🏢</span>
              Clientes
            </NavLink>
          )}
          {user?.is_superadmin && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                `nav-item ${isActive ? "bg-amber-100/70 text-amber-700 shadow-glass" : ""}`
              }
            >
              <span>🛡️</span>
              Admin
            </NavLink>
          )}
          <button
            onClick={handleLogout}
            className="w-full text-left nav-item text-slate-500"
          >
            <span>↩️</span>
            Cerrar sesión
          </button>
        </nav>
      </aside>

      <main className="flex-1 flex flex-col overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
