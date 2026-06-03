import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useClientStore, type ClientAccount } from "../store/clientStore";

type BusinessType = "saas" | "ecommerce" | "services" | "app" | "local";

const BUSINESS_TYPES: { value: BusinessType; label: string }[] = [
  { value: "saas", label: "SaaS" },
  { value: "ecommerce", label: "Ecommerce" },
  { value: "services", label: "Servicios" },
  { value: "app", label: "App" },
  { value: "local", label: "Negocio local" },
];

export function ClientAccounts() {
  const { clientAccounts, activeClientId, fetchClientAccounts, setActiveClient } = useClientStore();
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [businessType, setBusinessType] = useState<BusinessType>("saas");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchClientAccounts();
  }, []);

  const handleCreate = async () => {
    if (name.trim().length < 2) {
      setError("El nombre debe tener al menos 2 caracteres");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.post<ClientAccount>("/client-accounts", {
        name: name.trim(),
        business_type: businessType,
      });
      await fetchClientAccounts();
      setName("");
      setBusinessType("saas");
      setShowForm(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error creando workspace");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("¿Eliminar este workspace y todos sus datos?")) return;
    try {
      await api.delete(`/client-accounts/${id}`);
      await fetchClientAccounts();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Error eliminando workspace");
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Clientes</h1>
            <p className="text-sm text-gray-500">Gestiona los workspaces de tus clientes.</p>
          </div>
          <button
            onClick={() => setShowForm((v) => !v)}
            className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm font-medium"
          >
            {showForm ? "Cancelar" : "+ Nuevo cliente"}
          </button>
        </div>

        {showForm && (
          <div className="bg-white border border-gray-200 rounded-xl p-5 mb-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nombre del cliente</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="ej: Acme Corp"
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de negocio</label>
              <select
                value={businessType}
                onChange={(e) => setBusinessType(e.target.value as BusinessType)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500"
              >
                {BUSINESS_TYPES.map((b) => (
                  <option key={b.value} value={b.value}>
                    {b.label}
                  </option>
                ))}
              </select>
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
              onClick={handleCreate}
              disabled={saving}
              className="px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium"
            >
              {saving ? "Creando…" : "Crear cliente"}
            </button>
          </div>
        )}

        <div className="space-y-2">
          {clientAccounts.map((ca) => (
            <div
              key={ca.id}
              className="flex items-center justify-between bg-white border border-gray-200 rounded-xl p-4"
            >
              <div>
                <p className="font-medium text-gray-900">{ca.name}</p>
                <p className="text-xs text-gray-400">
                  {ca.business_type ?? "—"}
                  {ca.id === activeClientId && (
                    <span className="ml-2 text-brand-600 font-medium">· activo</span>
                  )}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {ca.id !== activeClientId && (
                  <button
                    onClick={() => {
                      setActiveClient(ca.id);
                      window.location.reload();
                    }}
                    className="px-3 py-1.5 text-xs font-medium text-brand-600 hover:bg-brand-50 rounded-lg"
                  >
                    Cambiar a este
                  </button>
                )}
                <button
                  onClick={() => handleDelete(ca.id)}
                  className="px-3 py-1.5 text-xs font-medium text-red-500 hover:bg-red-50 rounded-lg"
                >
                  Eliminar
                </button>
              </div>
            </div>
          ))}
          {clientAccounts.length === 0 && (
            <p className="text-sm text-gray-400 text-center py-8">No hay clientes todavía.</p>
          )}
        </div>
      </div>
    </div>
  );
}
