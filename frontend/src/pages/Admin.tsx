import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";

// ── Tipos (espejo de schemas/admin.py) ──────────────────────────────────────
interface Overview {
  total_users: number;
  active_subscriptions: number;
  mrr_cents: number;
  currency: string;
  total_closers: number;
  active_closers: number;
  commissions_pending_cents: number;
  commissions_paid_cents: number;
}

interface ClientRow {
  id: string;
  email: string;
  full_name: string | null;
  plan: string;
  subscription_status: string | null;
  is_founder: boolean;
  closer_id: string | null;
  closer_name: string | null;
  mrr_cents: number;
  created_at: string;
}

interface CloserRow {
  id: string;
  full_name: string;
  email: string;
  phone: string | null;
  commission_rate: number;
  referral_code: string;
  is_active: boolean;
  clients_count: number;
  commissions_pending_cents: number;
  commissions_paid_cents: number;
  created_at: string;
}

interface CommissionRow {
  id: string;
  closer_id: string;
  closer_name: string | null;
  user_id: string;
  client_email: string | null;
  stripe_invoice_id: string;
  type: "first_quota" | "recurring";
  base_amount: string;
  commission_amount: string;
  currency: string;
  period_start: string | null;
  status: "pending" | "paid";
  paid_at: string | null;
  created_at: string;
}

interface CloserDetailData {
  closer: CloserRow;
  clients: ClientRow[];
  commissions: CommissionRow[];
}

// ── Helpers ──────────────────────────────────────────────────────────────────
const fmtCents = (cents: number, currency = "eur") =>
  new Intl.NumberFormat("es-ES", { style: "currency", currency: currency.toUpperCase() }).format(
    cents / 100
  );

const fmtAmount = (amount: string, currency = "eur") =>
  new Intl.NumberFormat("es-ES", { style: "currency", currency: currency.toUpperCase() }).format(
    Number(amount)
  );

const fmtDate = (iso: string | null) =>
  iso ? new Date(iso).toLocaleDateString("es-ES", { day: "2-digit", month: "short", year: "numeric" }) : "—";

const fmtUSD = (amount: number) =>
  new Intl.NumberFormat("es-ES", { style: "currency", currency: "USD" }).format(amount);

interface ApiCosts {
  month: string;
  total_plans_executed: number;
  estimated_total_tokens: number;
  estimated_cost_usd: number;
  by_agent: Record<string, { prompt_tokens: number; completion_tokens: number; cost_usd: number }>;
}

type Tab = "overview" | "clients" | "closers" | "commissions" | "costs";

// ── Página principal ──────────────────────────────────────────────────────────
export function Admin() {
  const [tab, setTab] = useState<Tab>("overview");

  return (
    <div className="min-h-screen bg-transparent">
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl">🛡️</span>
          <h1 className="font-bold text-gray-900">Panel de administración</h1>
        </div>
        <Link to="/campaigns/new" className="text-sm text-brand-600 hover:underline">
          ← Volver a la app
        </Link>
      </header>

      <nav className="bg-white border-b border-gray-200 px-6 flex gap-1">
        {([
          ["overview", "Resumen"],
          ["clients", "Clientes"],
          ["closers", "Closers"],
          ["commissions", "Comisiones"],
          ["costs", "Costes API"],
        ] as [Tab, string][]).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              tab === key
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {label}
          </button>
        ))}
      </nav>

      <main className="p-6 max-w-7xl mx-auto">
        {tab === "overview" && <OverviewTab />}
        {tab === "clients" && <ClientsTab />}
        {tab === "closers" && <ClosersTab />}
        {tab === "commissions" && <CommissionsTab />}
        {tab === "costs" && <CostsTab />}
      </main>
    </div>
  );
}

// ── Resumen ────────────────────────────────────────────────────────────────────
function OverviewTab() {
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<Overview>("/admin/overview").then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorBox msg={error} />;
  if (!data) return <Spinner />;

  const cards = [
    { label: "Usuarios totales", value: String(data.total_users) },
    { label: "Suscripciones activas", value: String(data.active_subscriptions) },
    { label: "MRR (aprox.)", value: fmtCents(data.mrr_cents, data.currency) },
    { label: "Closers activos", value: `${data.active_closers} / ${data.total_closers}` },
    { label: "Comisiones pendientes", value: fmtCents(data.commissions_pending_cents, data.currency), accent: "amber" },
    { label: "Comisiones pagadas", value: fmtCents(data.commissions_paid_cents, data.currency), accent: "emerald" },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {cards.map((c) => (
        <div key={c.label} className="bg-white/70 backdrop-blur-xl rounded-xl border border-white/50 shadow-glass p-5">
          <p className="text-sm text-gray-500">{c.label}</p>
          <p
            className={`text-2xl font-bold mt-1 ${
              c.accent === "amber" ? "text-amber-600" : c.accent === "emerald" ? "text-emerald-600" : "text-gray-900"
            }`}
          >
            {c.value}
          </p>
        </div>
      ))}
    </div>
  );
}

// ── Clientes ────────────────────────────────────────────────────────────────────
function ClientsTab() {
  const [clients, setClients] = useState<ClientRow[]>([]);
  const [closers, setClosers] = useState<CloserRow[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [c, cl] = await Promise.all([
        api.get<ClientRow[]>("/admin/users"),
        api.get<CloserRow[]>("/admin/closers"),
      ]);
      setClients(c);
      setClosers(cl);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const assign = async (userId: string, closerId: string) => {
    const updated = await api.patch<ClientRow>(`/admin/users/${userId}/closer`, {
      closer_id: closerId || null,
    });
    setClients((prev) => prev.map((c) => (c.id === userId ? updated : c)));
  };

  if (error) return <ErrorBox msg={error} />;
  if (loading) return <Spinner />;

  return (
    <div className="bg-white/70 backdrop-blur-xl rounded-xl border border-white/50 shadow-glass overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-gray-500 text-left">
          <tr>
            <th className="px-4 py-3 font-medium">Cliente</th>
            <th className="px-4 py-3 font-medium">Plan</th>
            <th className="px-4 py-3 font-medium">Estado</th>
            <th className="px-4 py-3 font-medium">MRR</th>
            <th className="px-4 py-3 font-medium">Alta</th>
            <th className="px-4 py-3 font-medium">Closer</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {clients.map((c) => (
            <tr key={c.id} className="hover:bg-gray-50">
              <td className="px-4 py-3">
                <div className="font-medium text-gray-900">{c.full_name || "—"}</div>
                <div className="text-gray-400 text-xs">{c.email}</div>
              </td>
              <td className="px-4 py-3 capitalize">
                {c.plan}
                {c.is_founder && <span className="ml-1 text-amber-500" title="Fundador">★</span>}
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={c.subscription_status} />
              </td>
              <td className="px-4 py-3">{fmtCents(c.mrr_cents)}</td>
              <td className="px-4 py-3 text-gray-500">{fmtDate(c.created_at)}</td>
              <td className="px-4 py-3">
                <select
                  value={c.closer_id ?? ""}
                  onChange={(e) => assign(c.id, e.target.value)}
                  className="border border-gray-300 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                >
                  <option value="">— Sin closer —</option>
                  {closers.map((cl) => (
                    <option key={cl.id} value={cl.id}>
                      {cl.full_name}
                    </option>
                  ))}
                </select>
              </td>
            </tr>
          ))}
          {clients.length === 0 && (
            <tr>
              <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                Sin clientes todavía.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

// ── Closers ────────────────────────────────────────────────────────────────────
function ClosersTab() {
  const [closers, setClosers] = useState<CloserRow[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [detailId, setDetailId] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      setClosers(await api.get<CloserRow[]>("/admin/closers"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const toggleActive = async (c: CloserRow) => {
    await api.patch<CloserRow>(`/admin/closers/${c.id}`, { is_active: !c.is_active });
    load();
  };

  if (error) return <ErrorBox msg={error} />;

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm font-medium"
        >
          + Nuevo closer
        </button>
      </div>

      {showForm && <CloserForm onClose={() => setShowForm(false)} onCreated={() => { setShowForm(false); load(); }} />}
      {detailId && <CloserDetailModal closerId={detailId} onClose={() => setDetailId(null)} onChanged={load} />}

      {loading ? (
        <Spinner />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {closers.map((c) => (
            <div key={c.id} className="bg-white/70 backdrop-blur-xl rounded-xl border border-white/50 shadow-glass p-5 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-semibold text-gray-900">{c.full_name}</p>
                  <p className="text-xs text-gray-400">{c.email}</p>
                </div>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    c.is_active ? "bg-emerald-50 text-emerald-700" : "bg-gray-100 text-gray-500"
                  }`}
                >
                  {c.is_active ? "Activo" : "Inactivo"}
                </span>
              </div>

              <div className="text-sm text-gray-600 space-y-1">
                <div className="flex justify-between">
                  <span>Comisión</span>
                  <span className="font-medium">{(c.commission_rate * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between">
                  <span>Clientes</span>
                  <span className="font-medium">{c.clients_count}</span>
                </div>
                <div className="flex justify-between">
                  <span>Pendiente</span>
                  <span className="font-medium text-amber-600">{fmtCents(c.commissions_pending_cents)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Pagado</span>
                  <span className="font-medium text-emerald-600">{fmtCents(c.commissions_paid_cents)}</span>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg px-3 py-2 text-xs flex items-center justify-between">
                <span className="text-gray-500">Link referido</span>
                <code className="text-brand-600">?ref={c.referral_code}</code>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setDetailId(c.id)}
                  className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
                >
                  Detalle
                </button>
                <button
                  onClick={() => toggleActive(c)}
                  className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
                >
                  {c.is_active ? "Desactivar" : "Activar"}
                </button>
              </div>
            </div>
          ))}
          {closers.length === 0 && (
            <p className="text-gray-400 text-sm col-span-full text-center py-8">
              Sin closers. Crea el primero.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function CloserForm({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [rate, setRate] = useState("6");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [created, setCreated] = useState<{ email: string; password: string } | null>(null);

  const submit = async () => {
    setError("");
    setSaving(true);
    try {
      const res = await api.post<CloserRow & { temp_password: string | null }>("/admin/closers", {
        full_name: fullName,
        email,
        phone: phone || null,
        commission_rate: Number(rate) / 100,
      });
      setCreated({ email, password: res.temp_password ?? "(definida)" });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setSaving(false);
    }
  };

  if (created) {
    return (
      <Modal onClose={() => { onCreated(); }} title="Closer creado">
        <div className="space-y-3">
          <p className="text-sm text-gray-600">
            Comparte estas credenciales con el closer. La contraseña solo se muestra ahora.
          </p>
          <Credential label="Acceso" value={`${window.location.origin}/closer/login`} />
          <Credential label="Email" value={created.email} />
          <Credential label="Contraseña temporal" value={created.password} />
          <button
            onClick={() => onCreated()}
            className="w-full px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm font-medium mt-2"
          >
            Entendido
          </button>
        </div>
      </Modal>
    );
  }

  return (
    <Modal onClose={onClose} title="Nuevo closer">
      <div className="space-y-3">
        <Field label="Nombre completo">
          <input className={inputCls} value={fullName} onChange={(e) => setFullName(e.target.value)} />
        </Field>
        <Field label="Email">
          <input className={inputCls} type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </Field>
        <Field label="Teléfono (opcional)">
          <input className={inputCls} value={phone} onChange={(e) => setPhone(e.target.value)} />
        </Field>
        <Field label="Comisión recurrente (%)">
          <input className={inputCls} type="number" min={0} max={100} value={rate} onChange={(e) => setRate(e.target.value)} />
        </Field>
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <div className="flex gap-2 pt-2">
          <button onClick={onClose} className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm">
            Cancelar
          </button>
          <button
            onClick={submit}
            disabled={saving || !fullName || !email}
            className="flex-1 px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium"
          >
            {saving ? "Creando…" : "Crear closer"}
          </button>
        </div>
      </div>
    </Modal>
  );
}

function Credential({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-50 rounded-lg px-3 py-2">
      <p className="text-xs text-gray-500">{label}</p>
      <code className="text-sm text-gray-900 break-all">{value}</code>
    </div>
  );
}

function CloserDetailModal({
  closerId,
  onClose,
  onChanged,
}: {
  closerId: string;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [data, setData] = useState<CloserDetailData | null>(null);
  const [error, setError] = useState("");
  const [newPassword, setNewPassword] = useState<string | null>(null);

  const load = () =>
    api.get<CloserDetailData>(`/admin/closers/${closerId}`).then(setData).catch((e) => setError(e.message));

  useEffect(() => {
    load();
  }, [closerId]);

  const liquidate = async () => {
    const pending = (data?.commissions ?? []).filter((c) => c.status === "pending").map((c) => c.id);
    if (pending.length === 0) return;
    await api.post("/admin/commissions/liquidate", { commission_ids: pending });
    await load();
    onChanged();
  };

  const resetPassword = async () => {
    const res = await api.post<{ temp_password: string }>(`/admin/closers/${closerId}/reset-password`);
    setNewPassword(res.temp_password);
  };

  return (
    <Modal onClose={onClose} title={data ? data.closer.full_name : "Closer"} wide>
      {error && <ErrorBox msg={error} />}
      {!data ? (
        <Spinner />
      ) : (
        <div className="space-y-5">
          <div className="grid grid-cols-3 gap-3">
            <Stat label="Clientes" value={String(data.closer.clients_count)} />
            <Stat label="Pendiente" value={fmtCents(data.closer.commissions_pending_cents)} accent="amber" />
            <Stat label="Pagado" value={fmtCents(data.closer.commissions_paid_cents)} accent="emerald" />
          </div>

          <div className="flex items-center justify-between gap-2">
            <button
              onClick={resetPassword}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
            >
              Resetear contraseña
            </button>
            <button
              onClick={liquidate}
              disabled={data.closer.commissions_pending_cents === 0}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium"
            >
              Liquidar todo lo pendiente
            </button>
          </div>

          {newPassword && (
            <Credential label="Nueva contraseña temporal (cópiala ahora)" value={newPassword} />
          )}

          <div className="bg-gray-50 rounded-lg px-3 py-2 text-xs flex items-center justify-between">
            <span className="text-gray-500">Link referido</span>
            <code className="text-brand-600">
              {window.location.origin}/?ref={data.closer.referral_code}
            </code>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Comisiones</h3>
            <CommissionsTable rows={data.commissions} />
          </div>
        </div>
      )}
    </Modal>
  );
}

// ── Comisiones ──────────────────────────────────────────────────────────────────
function CommissionsTab() {
  const [rows, setRows] = useState<CommissionRow[]>([]);
  const [status, setStatus] = useState<"" | "pending" | "paid">("pending");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const load = async () => {
    setLoading(true);
    try {
      const qs = status ? `?status=${status}` : "";
      setRows(await api.get<CommissionRow[]>(`/admin/commissions${qs}`));
      setSelected(new Set());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [status]);

  const selectedTotal = useMemo(
    () =>
      rows
        .filter((r) => selected.has(r.id))
        .reduce((acc, r) => acc + Number(r.commission_amount), 0),
    [rows, selected]
  );

  const liquidate = async () => {
    if (selected.size === 0) return;
    await api.post("/admin/commissions/liquidate", { commission_ids: [...selected] });
    await load();
  };

  if (error) return <ErrorBox msg={error} />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-1">
          {([["pending", "Pendientes"], ["paid", "Pagadas"], ["", "Todas"]] as [string, string][]).map(
            ([key, label]) => (
              <button
                key={key}
                onClick={() => setStatus(key as "" | "pending" | "paid")}
                className={`px-3 py-1.5 text-sm rounded-lg ${
                  status === key ? "bg-brand-600 text-white" : "bg-white border border-gray-300 text-gray-600"
                }`}
              >
                {label}
              </button>
            )
          )}
        </div>
        {selected.size > 0 && (
          <button
            onClick={liquidate}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium"
          >
            Liquidar {selected.size} ({fmtCents(Math.round(selectedTotal * 100))})
          </button>
        )}
      </div>

      {loading ? <Spinner /> : <CommissionsTable rows={rows} selected={selected} onToggle={setSelected} />}
    </div>
  );
}

function CommissionsTable({
  rows,
  selected,
  onToggle,
}: {
  rows: CommissionRow[];
  selected?: Set<string>;
  onToggle?: (s: Set<string>) => void;
}) {
  const toggle = (id: string) => {
    if (!onToggle || !selected) return;
    const next = new Set(selected);
    next.has(id) ? next.delete(id) : next.add(id);
    onToggle(next);
  };

  return (
    <div className="bg-white/70 backdrop-blur-xl rounded-xl border border-white/50 shadow-glass overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-gray-500 text-left">
          <tr>
            {onToggle && <th className="px-4 py-3 w-10"></th>}
            <th className="px-4 py-3 font-medium">Cliente</th>
            <th className="px-4 py-3 font-medium">Closer</th>
            <th className="px-4 py-3 font-medium">Tipo</th>
            <th className="px-4 py-3 font-medium">Base</th>
            <th className="px-4 py-3 font-medium">Comisión</th>
            <th className="px-4 py-3 font-medium">Periodo</th>
            <th className="px-4 py-3 font-medium">Estado</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {rows.map((r) => (
            <tr key={r.id} className="hover:bg-gray-50">
              {onToggle && (
                <td className="px-4 py-3">
                  {r.status === "pending" && (
                    <input
                      type="checkbox"
                      checked={selected?.has(r.id) ?? false}
                      onChange={() => toggle(r.id)}
                    />
                  )}
                </td>
              )}
              <td className="px-4 py-3 text-gray-700">{r.client_email ?? "—"}</td>
              <td className="px-4 py-3 text-gray-700">{r.closer_name ?? "—"}</td>
              <td className="px-4 py-3">
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    r.type === "first_quota" ? "bg-violet-50 text-violet-700" : "bg-sky-50 text-sky-700"
                  }`}
                >
                  {r.type === "first_quota" ? "1ª cuota" : "Recurrente"}
                </span>
              </td>
              <td className="px-4 py-3 text-gray-500">{fmtAmount(r.base_amount, r.currency)}</td>
              <td className="px-4 py-3 font-medium text-gray-900">{fmtAmount(r.commission_amount, r.currency)}</td>
              <td className="px-4 py-3 text-gray-500">{fmtDate(r.period_start)}</td>
              <td className="px-4 py-3">
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    r.status === "paid" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
                  }`}
                >
                  {r.status === "paid" ? "Pagada" : "Pendiente"}
                </span>
              </td>
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={onToggle ? 8 : 7} className="px-4 py-8 text-center text-gray-400">
                Sin comisiones.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

// ── UI helpers ──────────────────────────────────────────────────────────────────
const inputCls =
  "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {children}
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: "amber" | "emerald" }) {
  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <p className="text-xs text-gray-500">{label}</p>
      <p
        className={`text-lg font-bold ${
          accent === "amber" ? "text-amber-600" : accent === "emerald" ? "text-emerald-600" : "text-gray-900"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

// ── Costes API ──────────────────────────────────────────────────────────────────
function CostsTab() {
  const [costs, setCosts] = useState<ApiCosts | null>(null);
  const [error, setError] = useState("");
  const [month, setMonth] = useState("");

  useEffect(() => {
    const today = new Date();
    const m = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;
    setMonth(m);
    loadCosts(m);
  }, []);

  const loadCosts = async (m: string) => {
    try {
      const data = await api.get<ApiCosts>(`/admin/api-costs?month=${m}`);
      setCosts(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  };

  const handleMonthChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const m = e.target.value;
    setMonth(m);
    loadCosts(m);
  };

  if (error) return <ErrorBox msg={error} />;
  if (!costs) return <Spinner />;

  const agentKeys = Object.keys(costs.by_agent).sort();

  return (
    <div className="space-y-6">
      {/* Selector de mes */}
      <div className="flex items-center gap-4">
        <label className="text-sm font-medium text-gray-700">Mes:</label>
        <input
          type="month"
          value={month}
          onChange={handleMonthChange}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
        />
      </div>

      {/* Resumen */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-xs text-gray-500 uppercase font-semibold">Planes ejecutados</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{costs.total_plans_executed}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-xs text-gray-500 uppercase font-semibold">Tokens estimados</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">
            {(costs.estimated_total_tokens / 1_000_000).toFixed(2)}M
          </p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-xs text-gray-500 uppercase font-semibold">Coste OpenAI</p>
          <p className="text-3xl font-bold text-brand-600 mt-2">{fmtUSD(costs.estimated_cost_usd)}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-xs text-gray-500 uppercase font-semibold">Coste por plan</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">
            {costs.total_plans_executed > 0
              ? fmtUSD(costs.estimated_cost_usd / costs.total_plans_executed)
              : "—"}
          </p>
        </div>
      </div>

      {/* Desglose por agente */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900">Costes por agente</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left font-semibold text-gray-700">Agente</th>
                <th className="px-6 py-3 text-right font-semibold text-gray-700">Tokens entrada</th>
                <th className="px-6 py-3 text-right font-semibold text-gray-700">Tokens salida</th>
                <th className="px-6 py-3 text-right font-semibold text-gray-700">Coste USD</th>
                <th className="px-6 py-3 text-right font-semibold text-gray-700">% Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {agentKeys.map((agent) => {
                const data = costs.by_agent[agent];
                const pct =
                  costs.estimated_cost_usd > 0
                    ? ((data.cost_usd / costs.estimated_cost_usd) * 100).toFixed(1)
                    : "0";
                return (
                  <tr key={agent} className="hover:bg-gray-50">
                    <td className="px-6 py-3 font-medium text-gray-900">{agent}</td>
                    <td className="px-6 py-3 text-right text-gray-600">
                      {(data.prompt_tokens / 1_000_000).toFixed(2)}M
                    </td>
                    <td className="px-6 py-3 text-right text-gray-600">
                      {(data.completion_tokens / 1_000_000).toFixed(2)}M
                    </td>
                    <td className="px-6 py-3 text-right font-semibold text-gray-900">{fmtUSD(data.cost_usd)}</td>
                    <td className="px-6 py-3 text-right text-gray-600">{pct}%</td>
                  </tr>
                );
              })}
              <tr className="bg-amber-50 border-t-2 border-amber-200">
                <td className="px-6 py-3 font-bold text-gray-900">TOTAL</td>
                <td className="px-6 py-3 text-right font-semibold text-gray-900">
                  {(costs.estimated_total_tokens / 1_000_000).toFixed(2)}M
                </td>
                <td></td>
                <td className="px-6 py-3 text-right font-bold text-amber-600">{fmtUSD(costs.estimated_cost_usd)}</td>
                <td className="px-6 py-3 text-right font-semibold text-gray-900">100%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <p className="text-xs text-gray-500">
        💡 Costes reales capturados de cada llamada a OpenAI. Precios gpt-4o: $5/1M input, $15/1M output.
      </p>
    </div>
  );
}

function StatusBadge({ status }: { status: string | null }) {
  const map: Record<string, string> = {
    active: "bg-emerald-50 text-emerald-700",
    trialing: "bg-sky-50 text-sky-700",
    past_due: "bg-amber-50 text-amber-700",
    canceled: "bg-gray-100 text-gray-500",
  };
  const cls = map[status ?? ""] ?? "bg-gray-100 text-gray-500";
  return <span className={`text-xs px-2 py-0.5 rounded-full ${cls}`}>{status ?? "—"}</span>;
}

function Modal({
  title,
  children,
  onClose,
  wide,
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
  wide?: boolean;
}) {
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className={`bg-white/90 backdrop-blur-2xl rounded-2xl shadow-glass-lg p-6 w-full ${wide ? "max-w-3xl" : "max-w-md"} max-h-[90vh] overflow-y-auto`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-bold text-gray-900">{title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

function Spinner() {
  return <div className="text-center py-12 text-gray-400 text-sm">Cargando…</div>;
}

function ErrorBox({ msg }: { msg: string }) {
  return <div className="bg-red-50 text-red-700 text-sm rounded-lg p-3 my-2">{msg}</div>;
}
