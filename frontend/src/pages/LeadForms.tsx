import { useEffect, useState } from "react";
import { api } from "../lib/api";

// ── Tipos ────────────────────────────────────────────────────────────────────
type FieldType = "prefill" | "custom";
type FieldFormat = "text" | "select";

interface LeadFormField {
  type: FieldType;
  key: string;
  label: string;
  format?: FieldFormat;
  options?: string[];
}

interface LeadForm {
  id: string;
  name: string;
  locale: string;
  intro_headline: string | null;
  intro_description: string | null;
  fields: LeadFormField[];
  privacy_policy_url: string | null;
  privacy_policy_link_text: string | null;
  thank_you_title: string | null;
  thank_you_body: string | null;
  thank_you_button_text: string | null;
  thank_you_button_type: "VIEW_WEBSITE" | "DOWNLOAD" | "CALL_BUSINESS";
  thank_you_website_url: string | null;
  meta_form_id: string | null;
  synced_at: string | null;
  created_at: string;
  updated_at: string;
}

// Campos estándar de prefill que Meta autocompleta con datos del perfil
const PREFILL_OPTIONS: { key: string; label: string }[] = [
  { key: "FULL_NAME", label: "Nombre completo" },
  { key: "EMAIL", label: "Email" },
  { key: "PHONE", label: "Teléfono" },
  { key: "COMPANY_NAME", label: "Empresa" },
  { key: "JOB_TITLE", label: "Cargo" },
  { key: "CITY", label: "Ciudad" },
];

interface EditorState {
  id: string | null;
  name: string;
  intro_headline: string;
  intro_description: string;
  prefillKeys: string[];
  customQuestions: { label: string; format: FieldFormat; options: string[] }[];
  privacy_policy_url: string;
  privacy_policy_link_text: string;
  thank_you_title: string;
  thank_you_body: string;
  thank_you_button_type: "VIEW_WEBSITE" | "DOWNLOAD" | "CALL_BUSINESS";
  thank_you_website_url: string;
  thank_you_button_text: string;
}

function emptyEditor(): EditorState {
  return {
    id: null,
    name: "",
    intro_headline: "",
    intro_description: "",
    prefillKeys: ["FULL_NAME", "EMAIL", "PHONE"],
    customQuestions: [],
    privacy_policy_url: "",
    privacy_policy_link_text: "Política de privacidad",
    thank_you_title: "¡Gracias!",
    thank_you_body: "Hemos recibido tus datos. Nos pondremos en contacto pronto.",
    thank_you_button_type: "VIEW_WEBSITE",
    thank_you_website_url: "",
    thank_you_button_text: "Visitar web",
  };
}

function formToEditor(f: LeadForm): EditorState {
  const prefillKeys = f.fields.filter((x) => x.type === "prefill").map((x) => x.key);
  const customQuestions = f.fields
    .filter((x) => x.type === "custom")
    .map((x) => ({ label: x.label, format: x.format ?? "text", options: x.options ?? [] }));
  return {
    id: f.id,
    name: f.name,
    intro_headline: f.intro_headline ?? "",
    intro_description: f.intro_description ?? "",
    prefillKeys: prefillKeys.length ? prefillKeys : ["EMAIL"],
    customQuestions,
    privacy_policy_url: f.privacy_policy_url ?? "",
    privacy_policy_link_text: f.privacy_policy_link_text ?? "Política de privacidad",
    thank_you_title: f.thank_you_title ?? "",
    thank_you_body: f.thank_you_body ?? "",
    thank_you_button_type: f.thank_you_button_type ?? "VIEW_WEBSITE",
    thank_you_website_url: f.thank_you_website_url ?? "",
    thank_you_button_text: f.thank_you_button_text ?? "",
  };
}

function editorToPayload(e: EditorState) {
  const fields: LeadFormField[] = [
    ...e.prefillKeys.map((key) => ({
      type: "prefill" as const,
      key,
      label: PREFILL_OPTIONS.find((p) => p.key === key)?.label ?? key,
    })),
    ...e.customQuestions
      .filter((q) => q.label.trim())
      .map((q, i) => ({
        type: "custom" as const,
        key: `q${i + 1}`,
        label: q.label.trim(),
        format: q.format,
        options: q.format === "select" ? q.options.filter((o) => o.trim()) : [],
      })),
  ];
  return {
    name: e.name.trim(),
    locale: "es_ES",
    intro_headline: e.intro_headline.trim() || null,
    intro_description: e.intro_description.trim() || null,
    fields,
    privacy_policy_url: e.privacy_policy_url.trim() || null,
    privacy_policy_link_text: e.privacy_policy_link_text.trim() || null,
    thank_you_title: e.thank_you_title.trim() || null,
    thank_you_body: e.thank_you_body.trim() || null,
    thank_you_button_type: e.thank_you_button_type,
    thank_you_website_url: e.thank_you_website_url.trim() || null,
    thank_you_button_text: e.thank_you_button_text.trim() || null,
  };
}

// ── Página ───────────────────────────────────────────────────────────────────
export function LeadForms() {
  const [forms, setForms] = useState<LeadForm[]>([]);
  const [loading, setLoading] = useState(true);
  const [editor, setEditor] = useState<EditorState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      setForms(await api.get<LeadForm[]>("/lead-forms"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const save = async () => {
    if (!editor) return;
    if (!editor.name.trim()) {
      setError("El formulario necesita un nombre.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const payload = editorToPayload(editor);
      if (editor.id) {
        await api.patch(`/lead-forms/${editor.id}`, payload);
      } else {
        await api.post("/lead-forms", payload);
      }
      setEditor(null);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al guardar");
    } finally {
      setBusy(false);
    }
  };

  const syncMeta = async (id: string) => {
    setBusy(true);
    setError(null);
    try {
      await api.post(`/lead-forms/${id}/sync-meta`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al sincronizar");
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id: string) => {
    if (!confirm("¿Eliminar este formulario?")) return;
    setBusy(true);
    try {
      await api.delete(`/lead-forms/${id}`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al eliminar");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-1">
          <h1 className="text-2xl font-bold text-slate-800">Formularios de Lead Ad</h1>
          <button className="btn-brand px-4 py-2 text-sm" onClick={() => setEditor(emptyEditor())}>
            ＋ Nuevo formulario
          </button>
        </div>
        <p className="text-sm text-slate-500 mb-5">
          Formularios nativos de Meta (instant_form) reutilizables en tus campañas. Si no eliges
          ninguno, se crea uno automático al publicar.
        </p>

        {error && (
          <div className="mb-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm px-4 py-3">
            {error}
          </div>
        )}

        {loading ? (
          <p className="text-slate-400 text-sm">Cargando…</p>
        ) : forms.length === 0 ? (
          <div className="glass p-8 text-center text-slate-500 text-sm">
            Aún no tienes formularios. Crea uno o deja que se genere solo al publicar.
          </div>
        ) : (
          <div className="space-y-3">
            {forms.map((f) => (
              <div key={f.id} className="glass p-4 flex items-center justify-between">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-slate-800 truncate">{f.name}</span>
                    {f.meta_form_id ? (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">
                        Sincronizado
                      </span>
                    ) : (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">
                        Sin sincronizar
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {f.fields.length} campos · {f.fields.map((x) => x.label).slice(0, 4).join(", ")}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    className="text-xs px-3 py-1.5 rounded-lg bg-white/60 hover:bg-white text-slate-600"
                    disabled={busy}
                    onClick={() => syncMeta(f.id)}
                  >
                    Sincronizar
                  </button>
                  <button
                    className="text-xs px-3 py-1.5 rounded-lg bg-white/60 hover:bg-white text-slate-600"
                    onClick={() => setEditor(formToEditor(f))}
                  >
                    Editar
                  </button>
                  <button
                    className="text-xs px-3 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-600"
                    disabled={busy}
                    onClick={() => remove(f.id)}
                  >
                    Eliminar
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {editor && (
        <FormEditor
          state={editor}
          setState={setEditor}
          onSave={save}
          onClose={() => setEditor(null)}
          busy={busy}
        />
      )}
    </div>
  );
}

// ── Editor (drawer) ───────────────────────────────────────────────────────────
function FormEditor({
  state,
  setState,
  onSave,
  onClose,
  busy,
}: {
  state: EditorState;
  setState: (s: EditorState) => void;
  onSave: () => void;
  onClose: () => void;
  busy: boolean;
}) {
  const togglePrefill = (key: string) => {
    const has = state.prefillKeys.includes(key);
    setState({
      ...state,
      prefillKeys: has
        ? state.prefillKeys.filter((k) => k !== key)
        : [...state.prefillKeys, key],
    });
  };

  const updateQuestion = (i: number, patch: Partial<EditorState["customQuestions"][0]>) => {
    const next = [...state.customQuestions];
    next[i] = { ...next[i], ...patch };
    setState({ ...state, customQuestions: next });
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/30" onClick={onClose}>
      <div
        className="w-full max-w-lg h-full bg-white shadow-2xl overflow-y-auto p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-800">
            {state.id ? "Editar formulario" : "Nuevo formulario"}
          </h2>
          <button className="text-slate-400 hover:text-slate-700" onClick={onClose}>
            ✕
          </button>
        </div>

        <label className="block text-xs font-semibold text-slate-500 mb-1">Nombre interno</label>
        <input
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 w-full mb-4"
          value={state.name}
          onChange={(e) => setState({ ...state, name: e.target.value })}
          placeholder="Ej: Captación leads SaaS"
        />

        {/* Intro / context card */}
        <h3 className="text-sm font-semibold text-slate-700 mb-2">Introducción (opcional)</h3>
        <input
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 w-full mb-2"
          value={state.intro_headline}
          onChange={(e) => setState({ ...state, intro_headline: e.target.value })}
          placeholder="Titular de la tarjeta de bienvenida"
        />
        <textarea
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 w-full mb-4"
          rows={2}
          value={state.intro_description}
          onChange={(e) => setState({ ...state, intro_description: e.target.value })}
          placeholder="Descripción breve"
        />

        {/* Campos prefill */}
        <h3 className="text-sm font-semibold text-slate-700 mb-2">Campos del formulario</h3>
        <div className="grid grid-cols-2 gap-2 mb-4">
          {PREFILL_OPTIONS.map((p) => (
            <label
              key={p.key}
              className="flex items-center gap-2 text-sm text-slate-600 bg-slate-50 rounded-lg px-3 py-2 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={state.prefillKeys.includes(p.key)}
                onChange={() => togglePrefill(p.key)}
              />
              {p.label}
            </label>
          ))}
        </div>

        {/* Preguntas custom */}
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-slate-700">Preguntas personalizadas</h3>
          <button
            className="text-xs text-brand-600 font-medium"
            onClick={() =>
              setState({
                ...state,
                customQuestions: [
                  ...state.customQuestions,
                  { label: "", format: "text", options: [] },
                ],
              })
            }
          >
            ＋ Añadir
          </button>
        </div>
        {state.customQuestions.map((q, i) => (
          <div key={i} className="border border-slate-200 rounded-lg p-3 mb-2">
            <div className="flex gap-2 mb-2">
              <input
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 flex-1"
                value={q.label}
                onChange={(e) => updateQuestion(i, { label: e.target.value })}
                placeholder="Pregunta"
              />
              <select
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                value={q.format}
                onChange={(e) => updateQuestion(i, { format: e.target.value as FieldFormat })}
              >
                <option value="text">Texto</option>
                <option value="select">Opciones</option>
              </select>
              <button
                className="text-rose-500 px-2"
                onClick={() =>
                  setState({
                    ...state,
                    customQuestions: state.customQuestions.filter((_, j) => j !== i),
                  })
                }
              >
                ✕
              </button>
            </div>
            {q.format === "select" && (
              <input
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 w-full text-xs"
                value={q.options.join(", ")}
                onChange={(e) =>
                  updateQuestion(i, { options: e.target.value.split(",").map((o) => o.trim()) })
                }
                placeholder="Opciones separadas por comas"
              />
            )}
          </div>
        ))}

        {/* Privacidad */}
        <h3 className="text-sm font-semibold text-slate-700 mt-4 mb-2">
          Política de privacidad <span className="text-rose-500">*</span>
        </h3>
        <input
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 w-full mb-2"
          value={state.privacy_policy_url}
          onChange={(e) => setState({ ...state, privacy_policy_url: e.target.value })}
          placeholder="https://tudominio.com/privacidad"
        />
        <input
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 w-full mb-4"
          value={state.privacy_policy_link_text}
          onChange={(e) => setState({ ...state, privacy_policy_link_text: e.target.value })}
          placeholder="Texto del enlace"
        />

        {/* Gracias */}
        <h3 className="text-sm font-semibold text-slate-700 mb-2">Página de agradecimiento</h3>
        <input
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 w-full mb-2"
          value={state.thank_you_title}
          onChange={(e) => setState({ ...state, thank_you_title: e.target.value })}
          placeholder="Título"
        />
        <textarea
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 w-full mb-2"
          rows={2}
          value={state.thank_you_body}
          onChange={(e) => setState({ ...state, thank_you_body: e.target.value })}
          placeholder="Mensaje"
        />
        <input
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 w-full mb-2"
          value={state.thank_you_website_url}
          onChange={(e) => setState({ ...state, thank_you_website_url: e.target.value })}
          placeholder="URL del botón (web a visitar)"
        />
        <input
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 w-full mb-4"
          value={state.thank_you_button_text}
          onChange={(e) => setState({ ...state, thank_you_button_text: e.target.value })}
          placeholder="Texto del botón"
        />

        <div className="flex gap-2 pt-2 border-t border-slate-100">
          <button className="btn-brand px-4 py-2 text-sm flex-1" disabled={busy} onClick={onSave}>
            {busy ? "Guardando…" : "Guardar formulario"}
          </button>
          <button className="px-4 py-2 text-sm text-slate-500" onClick={onClose}>
            Cancelar
          </button>
        </div>
        <p className="text-[11px] text-slate-400 mt-2">
          Editar un formulario ya sincronizado lo desvincula de Meta: vuelve a sincronizar para
          crear la versión actualizada (los formularios de Meta son inmutables).
        </p>
      </div>
    </div>
  );
}
