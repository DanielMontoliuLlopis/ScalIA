import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { usePlansStore } from "../../store/plansStore";
import type { Plan } from "../../store/plansStore";
import type { AgentTask } from "../../store/tasksStore";

interface Interest {
  name: string;
  id: string;
  relevance: string;
}

interface AngleAd {
  angle?: string;
  hook?: string;
  image_url?: string | null;
  budget_share?: number | null;
  status?: string;
}

interface AdsOutput {
  budget_summary?: string;
  budget?: {
    monthly_eur?: number;
    daily_eur?: number;
    daily_cents?: number;
  };
  interests_mapped?: Interest[];
  angles_tested?: AngleAd[];
  campaign_json?: {
    ab_mode?: string;
    campaign?: {
      name?: string;
      objective?: string;
      daily_budget?: number;
    };
    ad_set?: {
      targeting?: {
        age_min?: number;
        age_max?: number;
        genders?: number[];
        geo_locations?: { countries?: string[] };
      };
    };
    ads?: Array<{
      variant?: string;
      name?: string;
      creative?: {
        object_story_spec?: {
          link_data?: {
            message?: string;
            name?: string;
            description?: string;
            image_url?: string;
          };
        };
        asset_feed_spec?: {
          titles?: Array<{ text: string }>;
          bodies?: Array<{ text: string }>;
          descriptions?: Array<{ text: string }>;
          images?: Array<{ hash?: string; image_url?: string }>;
        };
      };
      landing_url?: string;
      copy_angle?: string;
    }>;
  };
}

interface Props {
  plan: Plan;
  adsTask: AgentTask;
  nextStep: number;
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
      {children}
    </h3>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  hint,
  prefix,
  suffix,
}: {
  label: string;
  value: string | number;
  onChange: (v: string) => void;
  type?: string;
  hint?: string;
  prefix?: string;
  suffix?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {hint && <p className="text-xs text-gray-400 mb-1">{hint}</p>}
      <div className="flex items-center gap-1">
        {prefix && <span className="text-sm text-gray-500 shrink-0">{prefix}</span>}
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400"
        />
        {suffix && <span className="text-sm text-gray-500 shrink-0">{suffix}</span>}
      </div>
    </div>
  );
}

function TextArea({
  label,
  value,
  onChange,
  rows = 3,
  hint,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  rows?: number;
  hint?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {hint && <p className="text-xs text-gray-400 mb-1">{hint}</p>}
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-violet-400"
      />
    </div>
  );
}

const COUNTRY_OPTIONS = [
  { code: "ES", label: "España" },
  { code: "MX", label: "México" },
  { code: "AR", label: "Argentina" },
  { code: "CO", label: "Colombia" },
  { code: "US", label: "EE.UU." },
  { code: "GB", label: "Reino Unido" },
  { code: "DE", label: "Alemania" },
  { code: "FR", label: "Francia" },
];

interface MetaPublishResult {
  campaign_id: string;
  ad_set_id: string;
  ad_ids: string[];
  meta_ads_manager_url: string;
}

interface MessageMatch {
  hook: string;
  warnings: string[];
  policy_warnings: string[];
  policy_status: string | null;
}

interface AngleDraft {
  index: number;
  angle: string;
  hook: string;
  keep: boolean;
}

export function AdsApprovalPanel({ plan, adsTask, nextStep }: Props) {
  const { upsertPlan } = usePlansStore();
  const output = adsTask.output as AdsOutput | null;
  const [loading, setLoading] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [published, setPublished] = useState<MetaPublishResult | null>(null);
  const [publishError, setPublishError] = useState<string | null>(null);

  const isMultiAngle =
    output?.campaign_json?.ab_mode === "multi_angle" || plan.ab_mode === "multi_angle";
  const anglesTested = output?.angles_tested ?? [];

  // Form state
  const cj = output?.campaign_json;
  const [campaignName, setCampaignName] = useState(cj?.campaign?.name ?? "");
  const [dailyBudgetEur, setDailyBudgetEur] = useState(
    String(output?.budget?.daily_eur ?? "")
  );
  const [ageMin, setAgeMin] = useState(String(cj?.ad_set?.targeting?.age_min ?? 25));
  const [ageMax, setAgeMax] = useState(String(cj?.ad_set?.targeting?.age_max ?? 54));
  const [countries, setCountries] = useState<string[]>(
    cj?.ad_set?.targeting?.geo_locations?.countries ?? ["ES"]
  );
  // Género: [] = todos, [1] = hombres, [2] = mujeres
  const [genders, setGenders] = useState<number[]>(
    cj?.ad_set?.targeting?.genders ?? []
  );

  // Validación de hilo narrativo + políticas Meta
  const [match, setMatch] = useState<MessageMatch | null>(null);
  useEffect(() => {
    api
      .get<MessageMatch>(`/plans/${plan.id}/message-match`)
      .then(setMatch)
      .catch(() => setMatch(null));
  }, [plan.id]);

  // Multi-Angle: selección de ángulos + edición de hook
  const [angleDrafts, setAngleDrafts] = useState<AngleDraft[]>(
    anglesTested.map((a, i) => ({
      index: i,
      angle: a.angle ?? "",
      hook: a.hook ?? "",
      keep: true,
    }))
  );
  const keptCount = angleDrafts.filter((a) => a.keep).length;
  const [adAMessage, setAdAMessage] = useState(
    cj?.ads?.[0]?.creative?.object_story_spec?.link_data?.message ?? ""
  );
  const [adBMessage, setAdBMessage] = useState(
    cj?.ads?.[1]?.creative?.object_story_spec?.link_data?.message ?? ""
  );

  const toggleCountry = (code: string) => {
    setCountries((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  };

  const dailyBudgetCents = Math.ceil(parseFloat(dailyBudgetEur || "0") * 100);

  const handleConfirm = async () => {
    setLoading(true);
    try {
      const updated = await api.post<Plan>(`/plans/${plan.id}/resume-ads`, {
        next_step: nextStep,
        campaign_edits: {
          campaign_name: campaignName,
          daily_budget_cents: dailyBudgetCents,
          age_min: parseInt(ageMin),
          age_max: parseInt(ageMax),
          countries,
          genders,
          ...(isMultiAngle
            ? {
                angles: angleDrafts.map((a) => ({
                  index: a.index,
                  keep: a.keep,
                  hook: a.hook,
                })),
              }
            : {
                ad_a_message: adAMessage,
                ...(plan.ab_testing ? { ad_b_message: adBMessage } : {}),
              }),
        },
      });
      upsertPlan(updated);
    } finally {
      setLoading(false);
    }
  };

  const handlePublishMeta = async () => {
    setPublishError(null);
    setPublishing(true);
    try {
      const result = await api.post<MetaPublishResult>(`/plans/${plan.id}/publish-meta`, {});
      setPublished(result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error publicando en Meta";
      setPublishError(msg);
    } finally {
      setPublishing(false);
    }
  };

  if (!output) return null;

  return (
    <div className="mt-3 border-2 border-violet-300 bg-violet-50 rounded-xl p-4 space-y-5">
      {/* Header */}
      <div>
        <p className="text-sm font-semibold text-violet-900">Revisa y edita tu campaña Meta</p>
        <p className="text-xs text-violet-600 mt-0.5">
          {output.budget_summary}
        </p>
      </div>

      {/* Validación: hilo narrativo (message match) */}
      {match && match.warnings.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-3.5 space-y-1.5">
          <p className="text-xs font-semibold text-amber-800 flex items-center gap-1.5">
            <span>🧵</span> Coherencia del mensaje
          </p>
          {match.hook && (
            <p className="text-[11px] text-amber-600">
              Hook del anuncio: <span className="italic">"{match.hook}"</span>
            </p>
          )}
          <ul className="space-y-1">
            {match.warnings.map((w, i) => (
              <li key={i} className="text-xs text-amber-700 flex gap-1.5">
                <span className="shrink-0">⚠️</span>
                <span>{w}</span>
              </li>
            ))}
          </ul>
          <p className="text-[11px] text-amber-500 pt-0.5">
            No bloquea la publicación, pero un mensaje incoherente suele bajar la conversión.
          </p>
        </div>
      )}

      {/* Validación: políticas de Meta */}
      {match && match.policy_warnings.length > 0 && (
        <div
          className={`rounded-xl p-3.5 space-y-1.5 border ${
            match.policy_status === "rejected"
              ? "bg-red-50 border-red-200"
              : "bg-orange-50 border-orange-200"
          }`}
        >
          <p
            className={`text-xs font-semibold flex items-center gap-1.5 ${
              match.policy_status === "rejected" ? "text-red-800" : "text-orange-800"
            }`}
          >
            <span>🛡️</span> Políticas de Meta
            {match.policy_status === "approved_with_fixes" && (
              <span className="font-normal text-orange-500">(corregido por la IA)</span>
            )}
          </p>
          <ul className="space-y-1">
            {match.policy_warnings.map((w, i) => (
              <li
                key={i}
                className={`text-xs flex gap-1.5 ${
                  match.policy_status === "rejected" ? "text-red-700" : "text-orange-700"
                }`}
              >
                <span className="shrink-0">•</span>
                <span>{w}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Sección: Campaña */}
      <div className="bg-white/70 backdrop-blur-xl rounded-xl border border-white/50 shadow-glass p-4 space-y-4">
        <SectionTitle>Campaña</SectionTitle>
        <Field
          label="Nombre de la campaña"
          value={campaignName}
          onChange={setCampaignName}
        />
        <div className="grid grid-cols-2 gap-3">
          <Field
            label="Presupuesto diario"
            value={dailyBudgetEur}
            onChange={setDailyBudgetEur}
            type="number"
            prefix="€"
            hint={`≈ ${dailyBudgetCents} céntimos en API`}
          />
          <div className="flex flex-col justify-end">
            <p className="text-xs text-gray-400 mb-1">Objetivo</p>
            <div className="border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-500 bg-gray-50">
              {cj?.campaign?.objective === "LEAD_GENERATION" ? "Lead Generation" : "Conversiones"}
            </div>
          </div>
        </div>
      </div>

      {/* Sección: Audiencia */}
      <div className="bg-white/70 backdrop-blur-xl rounded-xl border border-white/50 shadow-glass p-4 space-y-4">
        <SectionTitle>Audiencia</SectionTitle>

        <div className="grid grid-cols-2 gap-3">
          <Field
            label="Edad mínima"
            value={ageMin}
            onChange={setAgeMin}
            type="number"
            suffix="años"
          />
          <Field
            label="Edad máxima"
            value={ageMax}
            onChange={setAgeMax}
            type="number"
            suffix="años"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Género</label>
          <div className="flex flex-wrap gap-2">
            {[
              { val: [] as number[], label: "Todos" },
              { val: [1], label: "Hombres" },
              { val: [2], label: "Mujeres" },
            ].map((g) => {
              const active =
                genders.length === g.val.length &&
                g.val.every((v) => genders.includes(v));
              return (
                <button
                  key={g.label}
                  onClick={() => setGenders(g.val)}
                  className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${
                    active
                      ? "bg-violet-600 text-white border-violet-600"
                      : "bg-white text-gray-600 border-gray-300 hover:border-violet-400"
                  }`}
                >
                  {g.label}
                </button>
              );
            })}
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Restringe solo si el producto es claramente de un género; "Todos" da mejor alcance.
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Países</label>
          <div className="flex flex-wrap gap-2">
            {COUNTRY_OPTIONS.map((c) => (
              <button
                key={c.code}
                onClick={() => toggleCountry(c.code)}
                className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${
                  countries.includes(c.code)
                    ? "bg-violet-600 text-white border-violet-600"
                    : "bg-white text-gray-600 border-gray-300 hover:border-violet-400"
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>
        </div>

        {/* Intereses sugeridos (solo lectura) */}
        {(output?.interests_mapped?.length ?? 0) > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Intereses de Meta <span className="text-gray-400 font-normal">(sugeridos por IA)</span>
            </label>
            <div className="flex flex-wrap gap-1.5">
              {output?.interests_mapped?.map((interest, i) => (
                <span
                  key={i}
                  className={`px-2.5 py-1 rounded-full text-xs border ${
                    interest.relevance === "alta"
                      ? "bg-violet-50 text-violet-700 border-violet-200"
                      : "bg-gray-50 text-gray-500 border-gray-200"
                  }`}
                >
                  {interest.name}
                  {interest.relevance === "alta" && (
                    <span className="ml-1 text-violet-400">★</span>
                  )}
                </span>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-1.5">Los marcados con ★ tienen alta relevancia según la investigación.</p>
          </div>
        )}
      </div>

      {/* Sección: Anuncios — Multi-Angle (1 ad set por ángulo) */}
      {isMultiAngle ? (
        <div className="bg-white/70 backdrop-blur-xl rounded-xl border border-white/50 shadow-glass p-4 space-y-4">
          <SectionTitle>Anuncios — Multi-Angle ({keptCount} de {anglesTested.length} ángulos)</SectionTitle>
          <p className="text-xs text-gray-400 -mt-2">
            Desmarca los ángulos que no quieras lanzar y edita su hook. El presupuesto se reparte
            equitativamente entre los {keptCount} seleccionados en la fase de exploración.
          </p>
          {keptCount === 0 && (
            <p className="text-xs text-red-600">Selecciona al menos un ángulo para publicar.</p>
          )}
          <div className="grid sm:grid-cols-2 gap-3">
            {anglesTested.map((a, i) => {
              const draft = angleDrafts[i];
              if (!draft) return null;
              const share = keptCount > 0 ? Math.round((1 / keptCount) * 100) : 0;
              return (
                <div
                  key={i}
                  className={`rounded-xl border-2 border-dashed p-3 space-y-2 transition-opacity ${
                    draft.keep ? "border-violet-200" : "border-gray-200 opacity-50"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={draft.keep}
                      onChange={(e) =>
                        setAngleDrafts((prev) =>
                          prev.map((d) =>
                            d.index === i ? { ...d, keep: e.target.checked } : d
                          )
                        )
                      }
                      className="w-4 h-4 accent-violet-600 shrink-0"
                    />
                    <span className="text-xs font-semibold text-violet-700 capitalize">
                      {(a.angle ?? "").replace(/_/g, " ")}
                    </span>
                    {draft.keep && (
                      <span className="ml-auto text-[11px] text-gray-400">{share}% budget</span>
                    )}
                  </div>
                  {a.image_url ? (
                    <img
                      src={a.image_url}
                      alt={a.angle}
                      className="w-full rounded-lg object-cover max-h-40"
                    />
                  ) : (
                    <div className="w-full h-24 rounded-lg bg-gray-100 flex items-center justify-center text-[11px] text-gray-400">
                      Sin imagen
                    </div>
                  )}
                  <textarea
                    value={draft.hook}
                    onChange={(e) =>
                      setAngleDrafts((prev) =>
                        prev.map((d) =>
                          d.index === i ? { ...d, hook: e.target.value } : d
                        )
                      )
                    }
                    disabled={!draft.keep}
                    rows={2}
                    placeholder="Hook del ángulo"
                    className="w-full border border-gray-300 rounded-lg px-2.5 py-1.5 text-xs resize-none focus:outline-none focus:ring-2 focus:ring-violet-400 disabled:bg-gray-50 disabled:text-gray-400"
                  />
                </div>
              );
            })}
          </div>
        </div>
      ) : (
      <div className="bg-white/70 backdrop-blur-xl rounded-xl border border-white/50 shadow-glass p-4 space-y-4">
        <SectionTitle>{plan.ab_testing ? "Anuncios — Split Test A/B" : "Anuncio"}</SectionTitle>

        {/* Variante A (siempre) */}
        <div className="rounded-xl border-2 border-dashed border-violet-200 p-3 space-y-3">
          <div className="flex items-center gap-2">
            {plan.ab_testing && (
              <span className="w-6 h-6 rounded-full bg-violet-600 text-white text-xs font-bold flex items-center justify-center shrink-0">A</span>
            )}
            <span className="text-sm font-medium text-gray-700">
              {cj?.ads?.[0]?.name ?? "Anuncio"} —{" "}
              <span className="text-xs text-gray-400">{cj?.ads?.[0]?.copy_angle ?? "emocional"}</span>
            </span>
          </div>
          {cj?.ads?.[0]?.creative?.object_story_spec?.link_data?.image_url && (
            <img
              src={cj.ads[0].creative!.object_story_spec!.link_data!.image_url}
              alt="Imagen del anuncio"
              className="w-full rounded-lg object-cover max-h-48"
            />
          )}
          {cj?.ads?.[0]?.creative?.object_story_spec?.link_data?.name && (
            <p className="text-xs text-gray-500">
              <span className="font-medium">Titular:</span>{" "}
              {cj.ads[0].creative!.object_story_spec!.link_data!.name}
            </p>
          )}
          {cj?.ads?.[0]?.creative?.asset_feed_spec ? (
            <div className="text-xs bg-amber-50 border border-amber-200 rounded-lg p-2.5 text-amber-700 leading-relaxed">
              ⚡ Creativo dinámico (DCO): Meta combinará{" "}
              {cj.ads[0].creative.asset_feed_spec.titles?.length ?? 0} titulares,{" "}
              {cj.ads[0].creative.asset_feed_spec.bodies?.length ?? 0} textos y{" "}
              {cj.ads[0].creative.asset_feed_spec.images?.length ?? 0} imágenes para optimizar.
            </div>
          ) : (
            <TextArea
              label="Texto del anuncio (copy)"
              value={adAMessage}
              onChange={setAdAMessage}
              rows={3}
              hint="Lo que verá el usuario en el feed de Facebook/Instagram"
            />
          )}
        </div>

        {/* Variante B (solo si ab_testing) */}
        {plan.ab_testing && cj?.ads?.[1] && (
          <div className="rounded-xl border-2 border-dashed border-sky-200 p-3 space-y-3">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-sky-500 text-white text-xs font-bold flex items-center justify-center shrink-0">B</span>
              <span className="text-sm font-medium text-gray-700">
                {cj.ads[1].name ?? "Variante B"} —{" "}
                <span className="text-xs text-gray-400">{cj.ads[1].copy_angle ?? "racional"}</span>
              </span>
            </div>
            {cj.ads[1].creative?.object_story_spec?.link_data?.image_url && (
              <img
                src={cj.ads[1].creative.object_story_spec.link_data.image_url}
                alt="Imagen variante B"
                className="w-full rounded-lg object-cover max-h-48"
              />
            )}
            {cj.ads[1].creative?.object_story_spec?.link_data?.name && (
              <p className="text-xs text-gray-500">
                <span className="font-medium">Titular:</span> {cj.ads[1].creative.object_story_spec.link_data.name}
              </p>
            )}
            <TextArea
              label="Texto del anuncio (copy)"
              value={adBMessage}
              onChange={setAdBMessage}
              rows={3}
              hint="Lo que verá el usuario en el feed de Facebook/Instagram"
            />
          </div>
        )}
      </div>
      )}

      {/* Advertencia estado PAUSED */}
      <div className="flex gap-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2.5 text-xs text-amber-700">
        <span className="text-base leading-none shrink-0">⏸</span>
        <span>
          La campaña se creará en Meta en estado <strong>PAUSED</strong>. Podrás activarla manualmente desde el Ads Manager cuando estés listo.
        </span>
      </div>

      {/* Resultado publicación */}
      {published && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4 space-y-2">
          <p className="text-sm font-semibold text-green-800">Campaña publicada en Meta</p>
          <p className="text-xs text-green-700">Campaign ID: <code>{published.campaign_id}</code></p>
          <p className="text-xs text-green-700">Ad Set ID: <code>{published.ad_set_id}</code></p>
          <p className="text-xs text-green-700">Ads: {published.ad_ids.join(", ")}</p>
          <a
            href={published.meta_ads_manager_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block mt-1 text-xs text-green-700 underline"
          >
            Ver en Ads Manager →
          </a>
        </div>
      )}

      {publishError && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2.5 text-xs text-red-700">
          {publishError}
        </div>
      )}

      {/* CTAs */}
      <div className="flex gap-2">
        <button
          onClick={handleConfirm}
          disabled={loading || countries.length === 0 || (isMultiAngle && keptCount === 0)}
          className="flex-1 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 text-gray-700 font-medium py-2.5 rounded-xl text-sm transition-colors"
        >
          {loading ? "Procesando…" : "Guardar ediciones →"}
        </button>
        <button
          onClick={handlePublishMeta}
          disabled={publishing || !!published || countries.length === 0}
          className="flex-1 bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white font-medium py-2.5 rounded-xl text-sm transition-colors"
        >
          {publishing ? "Publicando…" : published ? "✓ Publicado" : "Publicar en Meta →"}
        </button>
      </div>
    </div>
  );
}
