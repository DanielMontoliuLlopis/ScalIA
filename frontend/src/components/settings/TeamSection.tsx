import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { useAuthStore } from "../../store/authStore";

type Role = "owner" | "admin" | "member" | "viewer";

interface Member {
  id: string;
  email: string;
  full_name: string | null;
  role: Role;
  is_owner: boolean;
  created_at: string;
}

interface TeamInfo {
  members: Member[];
  seats_used: number;
  seats_limit: number;
}

const ROLE_LABEL: Record<Role, string> = {
  owner: "Owner — control total",
  admin: "Admin — gestiona ajustes y campañas",
  member: "Member — crea y publica campañas",
  viewer: "Viewer — solo lectura",
};

const INVITE_ROLES: Role[] = ["admin", "member", "viewer"];

export function TeamSection() {
  const { user } = useAuthStore();
  const [team, setTeam] = useState<TeamInfo | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ email: "", full_name: "", password: "", role: "member" as Role });

  // El plan debe incluir equipo (growth | agency) y el usuario ser owner para gestionar
  const tierHasTeam = user?.plan === "growth" || user?.plan === "agency";
  const canManage = user?.role === "owner";

  const load = () => {
    api.get<TeamInfo>("/team").then(setTeam).catch(() => setError("Error cargando equipo"));
  };

  useEffect(() => {
    if (tierHasTeam) load();
  }, [tierHasTeam]);

  const invite = async () => {
    setLoading(true);
    setError("");
    try {
      await api.post("/team/members", form);
      setForm({ email: "", full_name: "", password: "", role: "member" });
      setShowForm(false);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al invitar");
    } finally {
      setLoading(false);
    }
  };

  const changeRole = async (id: string, role: Role) => {
    try {
      await api.patch(`/team/members/${id}`, { role });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cambiar rol");
    }
  };

  const remove = async (id: string) => {
    if (!confirm("¿Quitar este miembro del equipo?")) return;
    try {
      await api.delete(`/team/members/${id}`);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al quitar miembro");
    }
  };

  return (
    <section className="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/50 shadow-glass p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-gray-800">Equipo y roles</h2>
        {team && (
          <span className="text-xs font-medium text-gray-500 bg-gray-50 border border-gray-200 rounded-full px-2.5 py-1">
            {team.seats_used}/{team.seats_limit >= 9999 ? "∞" : team.seats_limit} asientos
          </span>
        )}
      </div>

      {!tierHasTeam ? (
        <p className="text-sm text-gray-500">
          La gestión de equipo está disponible en los planes <b>Growth</b> y <b>Agency</b>.{" "}
          <a href="/onboarding/plan" className="text-brand-600 hover:underline">Mejorar plan</a>
        </p>
      ) : (
        <>
          <div className="divide-y divide-gray-100">
            {team?.members.map((m) => (
              <div key={m.id} className="flex items-center justify-between py-2.5">
                <div className="min-w-0">
                  <div className="text-sm font-medium text-gray-900 truncate">
                    {m.full_name || m.email}
                  </div>
                  <div className="text-xs text-gray-500 truncate">{m.email}</div>
                </div>
                <div className="flex items-center gap-2">
                  {m.is_owner ? (
                    <span className="text-xs font-medium text-brand-700 bg-brand-50 border border-brand-200 rounded-full px-2.5 py-1">
                      Owner
                    </span>
                  ) : canManage ? (
                    <>
                      <select
                        value={m.role}
                        onChange={(e) => changeRole(m.id, e.target.value as Role)}
                        className="text-xs border border-gray-300 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-brand-400"
                      >
                        {INVITE_ROLES.map((r) => (
                          <option key={r} value={r}>{r}</option>
                        ))}
                      </select>
                      <button
                        onClick={() => remove(m.id)}
                        className="text-xs text-red-500 hover:text-red-700"
                      >
                        Quitar
                      </button>
                    </>
                  ) : (
                    <span className="text-xs text-gray-500 capitalize">{m.role}</span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {canManage && (
            showForm ? (
              <div className="space-y-3 border-t border-gray-100 pt-4">
                <input
                  placeholder="Nombre completo"
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                />
                <input
                  placeholder="Email"
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                />
                <input
                  placeholder="Contraseña temporal (mín. 8)"
                  type="text"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                />
                <select
                  value={form.role}
                  onChange={(e) => setForm({ ...form, role: e.target.value as Role })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                >
                  {INVITE_ROLES.map((r) => (
                    <option key={r} value={r}>{ROLE_LABEL[r]}</option>
                  ))}
                </select>
                <div className="flex gap-2">
                  <button
                    onClick={invite}
                    disabled={loading || !form.email || !form.full_name || form.password.length < 8}
                    className="flex-1 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white text-sm font-medium py-2 rounded-lg"
                  >
                    {loading ? "Invitando…" : "Añadir miembro"}
                  </button>
                  <button
                    onClick={() => setShowForm(false)}
                    className="px-4 text-sm text-gray-500 hover:text-gray-700"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowForm(true)}
                className="text-sm font-medium text-brand-600 hover:text-brand-700"
              >
                + Añadir miembro
              </button>
            )
          )}
        </>
      )}

      {error && <p className="text-red-600 text-sm">{error}</p>}
    </section>
  );
}
