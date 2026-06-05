import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { SectionBlock, InfoRow, Chip, InfoTip } from "./SectionBlock";
import { ImageLightbox } from "../ui/ImageLightbox";
import { RecommendationCards } from "./RecommendationCards";
import type { FunnelMetrics } from "./types";
import {
  OBJECTIVE_LABELS,
  OBJECTIVE_OPTIONS,
  OPTIMIZATION_LABELS,
  OPTIMIZATION_OPTIONS,
  BILLING_LABELS,
  BID_LABELS,
  BID_OPTIONS,
  CTA_OPTIONS,
  PLATFORM_ICONS,
  PLATFORM_OPTIONS,
  FACEBOOK_POSITIONS,
  INSTAGRAM_POSITIONS,
  PLACEMENT_LABELS,
  DEVICE_OPTIONS,
  COUNTRY_NAMES,
  COLOR_PALETTES,
  SPECIAL_AD_CATEGORIES,
  CUSTOM_EVENT_TYPES,
  DESTINATION_LABELS,
  PACING_LABELS,
  GENDER_LABELS,
  BUYING_TYPE_LABELS,
  ATTRIBUTION_EVENT_LABELS,
  BUYING_TYPE_OPTIONS,
  CAMPAIGN_BID_OPTIONS,
  BILLING_OPTIONS,
  DESTINATION_OPTIONS,
  PACING_OPTIONS,
  GENDER_OPTIONS,
  SPECIAL_AD_CATEGORY_OPTIONS,
  CUSTOM_EVENT_OPTIONS,
  ATTRIBUTION_EVENT_OPTIONS,
  ATTRIBUTION_WINDOW_OPTIONS,
  AUDIENCE_NETWORK_POSITIONS,
  MESSENGER_POSITIONS,
  FREQUENCY_EVENT_OPTIONS,
} from "./constants";
import type {
  Campaign,
  AdsOutput,
  MetaStatus,
  CampaignUpdate,
  RawAdSet,
  RawAdLinkData,
} from "./types";

interface PublishResult {
  campaign_id: string;
  ad_set_id: string;
  ad_ids: string[];
  meta_ads_manager_url: string;
}

function conversionRate(views: number, conversions: number) {
  if (!views) return "—";
  return `${((conversions / views) * 100).toFixed(1)}%`;
}

function formatDateTime(iso?: string): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("es-ES", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function eurFromCents(cents?: number): string {
  if (cents == null) return "—";
  return `€${(cents / 100).toFixed(2)}`;
}

function CheckboxGroup({
  options,
  selected,
  onChange,
  disabled,
}: {
  options: { value: string; label: string }[];
  selected: string[];
  onChange: (next: string[]) => void;
  disabled?: boolean;
}) {
  function toggle(v: string) {
    if (selected.includes(v)) onChange(selected.filter((x) => x !== v));
    else onChange([...selected, v]);
  }
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map((o) => {
        const on = selected.includes(o.value);
        return (
          <button
            type="button"
            key={o.value}
            disabled={disabled}
            onClick={() => toggle(o.value)}
            className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${on
              ? "bg-brand-600 text-white border-brand-600"
              : "bg-white text-gray-600 border-gray-200 hover:border-brand-300"
              } ${disabled ? "opacity-60 cursor-not-allowed" : ""}`}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

function CountriesEditor({
  value,
  onChange,
  disabled,
}: {
  value: string[];
  onChange: (next: string[]) => void;
  disabled?: boolean;
}) {
  const [input, setInput] = useState("");
  function add() {
    const code = input.trim().toUpperCase();
    if (!code || value.includes(code)) return;
    onChange([...value, code]);
    setInput("");
  }
  function remove(code: string) {
    onChange(value.filter((c) => c !== code));
  }
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1.5">
        {value.map((c) => (
          <span
            key={c}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs bg-violet-100 text-violet-700"
          >
            {COUNTRY_NAMES[c] ?? c}
            {!disabled && (
              <button
                type="button"
                onClick={() => remove(c)}
                className="ml-1 text-violet-400 hover:text-violet-700"
              >
                ✕
              </button>
            )}
          </span>
        ))}
      </div>
      {!disabled && (
        <div className="flex gap-1">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value.toUpperCase())}
            placeholder="ES, MX, US…"
            maxLength={2}
            className="w-20 px-2 py-1 text-xs border border-gray-200 rounded-lg focus:outline-none focus:border-brand-400"
          />
          <button
            type="button"
            onClick={add}
            className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-lg font-medium text-gray-700"
          >
            + Añadir país
          </button>
        </div>
      )}
    </div>
  );
}

interface EditAd {
  variant: string;
  headline: string;
  description: string;
  message: string;
  caption: string;
  link: string;
  cta: string;
  conversion_domain: string;
  url_tags: string;
  is_dco: boolean;
}

interface EditLanding {
  id: string;
  headline: string;
  subheadline: string;
  benefits: string[];
  cta_text: string;
  primary_color: string;
}

interface EditState {
  // Campaña
  campaign_name: string;
  objective: string;
  buying_type: string;
  campaign_budget_optimization: boolean;
  daily_budget_eur: number;
  lifetime_budget_eur: number;
  spend_cap_eur: number;
  campaign_bid_strategy: string;
  bid_cap_eur: number;
  campaign_start_time: string;
  campaign_stop_time: string;
  special_ad_categories: string[];
  special_ad_category_country: string[];
  // Ad set
  adset_name: string;
  optimization_goal: string;
  billing_event: string;
  bid_strategy: string;
  bid_amount_eur: number;
  adset_daily_budget_eur: number;
  adset_lifetime_budget_eur: number;
  adset_start_time: string;
  adset_end_time: string;
  destination_type: string;
  pacing_type: string[];
  is_dynamic_creative: boolean;
  advantage_audience: boolean;
  dsa_beneficiary: string;
  dsa_payor: string;
  // Pixel / eventos
  pixel_id: string;
  custom_event_type: string;
  page_id: string;
  application_id: string;
  offsite_conversion_event_id: string;
  // Reglas
  attribution_spec: Array<{ event_type: string; window_days: number }>;
  frequency_control_specs: Array<{ event: string; interval_days: number; max_frequency: number }>;
  // Targeting
  age_min: number;
  age_max: number;
  genders: number[];
  countries: string[];
  excluded_countries: string[];
  publisher_platforms: string[];
  facebook_positions: string[];
  instagram_positions: string[];
  audience_network_positions: string[];
  messenger_positions: string[];
  device_platforms: string[];
  // Segmentación detallada
  interests: Array<{ id: string; name?: string }>;
  behaviors: Array<{ id: string; name?: string }>;
  demographics: Array<{ id: string; name?: string }>;
  work_positions: Array<{ id: string; name?: string }>;
  custom_audiences: Array<{ id: string; name?: string }>;
  excluded_custom_audiences: Array<{ id: string; name?: string }>;
  // Creativos
  ads: EditAd[];
  landings: EditLanding[];
  // Ad sets adicionales (Fase 3) — se editan como JSON crudo completo
  additional_ad_sets: RawAdSet[];
}

function cloneJSON<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj)) as T;
}

function centsToEur(cents?: number): number {
  return cents != null ? cents / 100 : 0;
}

function isoToLocalInput(iso?: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function localInputToIso(local: string): string {
  if (!local) return "";
  const d = new Date(local);
  return isNaN(d.getTime()) ? "" : d.toISOString();
}

function initialEditState(campaign: Campaign): EditState {
  const ads = campaign.ads_output as AdsOutput | null;
  const cj = ads?.campaign_json;
  const c = cj?.campaign;
  const as = cj?.ad_set;
  const t = as?.targeting;
  const po = as?.promoted_object;
  return {
    campaign_name: c?.name ?? campaign.title,
    objective: c?.objective ?? "OUTCOME_LEADS",
    buying_type: c?.buying_type ?? "AUCTION",
    campaign_budget_optimization: c?.campaign_budget_optimization ?? false,
    daily_budget_eur: ads?.budget?.daily_eur ?? 10,
    lifetime_budget_eur: centsToEur(c?.lifetime_budget),
    spend_cap_eur: centsToEur(c?.spend_cap),
    campaign_bid_strategy: c?.bid_strategy ?? "LOWEST_COST_WITHOUT_CAP",
    bid_cap_eur: centsToEur(c?.bid_cap),
    campaign_start_time: isoToLocalInput(c?.start_time),
    campaign_stop_time: isoToLocalInput(c?.stop_time),
    special_ad_categories: c?.special_ad_categories ?? [],
    special_ad_category_country: c?.special_ad_category_country ?? [],
    adset_name: as?.name ?? "",
    optimization_goal: as?.optimization_goal ?? "LEAD_GENERATION",
    billing_event: as?.billing_event ?? "IMPRESSIONS",
    bid_strategy: as?.bid_strategy ?? "LOWEST_COST_WITHOUT_CAP",
    bid_amount_eur: centsToEur(as?.bid_amount),
    adset_daily_budget_eur: centsToEur(as?.daily_budget),
    adset_lifetime_budget_eur: centsToEur(as?.lifetime_budget),
    adset_start_time: isoToLocalInput(as?.start_time),
    adset_end_time: isoToLocalInput(as?.end_time),
    destination_type: as?.destination_type ?? "",
    pacing_type: as?.pacing_type ?? [],
    is_dynamic_creative: as?.is_dynamic_creative ?? false,
    advantage_audience: as?.targeting_automation?.advantage_audience === 1,
    dsa_beneficiary: as?.dsa_beneficiary ?? "",
    dsa_payor: as?.dsa_payor ?? "",
    pixel_id: po?.pixel_id ?? "",
    custom_event_type: po?.custom_event_type ?? "",
    page_id: po?.page_id ?? "",
    application_id: po?.application_id ?? "",
    offsite_conversion_event_id: po?.offsite_conversion_event_id ?? "",
    attribution_spec: (as?.attribution_spec ?? []).map((a) => ({
      event_type: a.event_type,
      window_days: a.window_days,
    })),
    frequency_control_specs: (as?.frequency_control_specs ?? []).map((f) => ({
      event: f.event,
      interval_days: f.interval_days,
      max_frequency: f.max_frequency,
    })),
    age_min: t?.age_min ?? 25,
    age_max: t?.age_max ?? 54,
    genders: t?.genders ?? [],
    countries: t?.geo_locations?.countries ?? ["ES"],
    excluded_countries: t?.excluded_geo_locations?.countries ?? [],
    publisher_platforms: t?.publisher_platforms ?? ["facebook", "instagram"],
    facebook_positions: t?.facebook_positions ?? ["feed", "story"],
    instagram_positions: t?.instagram_positions ?? ["stream", "story"],
    audience_network_positions: t?.audience_network_positions ?? [],
    messenger_positions: t?.messenger_positions ?? [],
    device_platforms: t?.device_platforms ?? ["mobile"],
    interests:
      t?.flexible_spec?.[0]?.interests?.map((x) => ({ id: x.id, name: x.name })) ??
      (ads?.interests_mapped ?? []).map((x) => ({ id: x.id, name: x.name })),
    behaviors: (t?.flexible_spec?.[0]?.behaviors ?? []).map((x) => ({ id: x.id, name: x.name })),
    demographics: (t?.flexible_spec?.[0]?.demographics ?? []).map((x) => ({ id: x.id, name: x.name })),
    work_positions: (t?.flexible_spec?.[0]?.work_positions ?? []).map((x) => ({ id: x.id, name: x.name })),
    custom_audiences: (t?.custom_audiences ?? []).map((x) => ({ id: x.id, name: x.name })),
    excluded_custom_audiences: (t?.exclusions?.custom_audiences ?? []).map((x) => ({ id: x.id, name: x.name })),
    ads:
      cj?.ads?.map((a) => {
        const ld = a.creative?.object_story_spec?.link_data;
        return {
          variant: a.variant,
          headline: ld?.name ?? "",
          description: ld?.description ?? "",
          message: ld?.message ?? "",
          caption: ld?.caption ?? "",
          link: ld?.link ?? "",
          cta: ld?.call_to_action?.type ?? "LEARN_MORE",
          conversion_domain: a.conversion_domain ?? "",
          url_tags: a.creative?.url_tags ?? "",
          is_dco: !!a.creative?.asset_feed_spec,
        };
      }) ?? [],
    landings: campaign.landings.map((l) => ({
      id: l.id,
      headline: l.headline ?? "",
      subheadline: l.subheadline ?? "",
      benefits: l.benefits ?? [],
      cta_text: l.cta_text ?? "",
      primary_color: l.primary_color,
    })),
    additional_ad_sets: cloneJSON(cj?.additional_ad_sets ?? []),
  };
}

function fmtMetric(n: number | null | undefined, prefix = "", suffix = "", decimals = 2): string {
  if (n == null) return "—";
  return `${prefix}${n.toLocaleString("es-ES", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}${suffix}`;
}

function FunnelMetricsSection({ planId }: { planId: string }) {
  const [metrics, setMetrics] = useState<FunnelMetrics | null>(null);

  useEffect(() => {
    api.get<FunnelMetrics>(`/campaigns/${planId}/metrics`).then(setMetrics).catch(() => { });
  }, [planId]);

  if (!metrics) return null;

  const funnelSteps = [
    { label: "Leads", value: metrics.total_leads, color: "bg-brand-500" },
    { label: "Contactados", value: metrics.contacted, color: "bg-blue-500" },
    { label: "Se presentaron", value: metrics.showed_up, color: "bg-amber-500" },
    { label: "Cerrados", value: metrics.closed, color: "bg-green-500" },
  ];
  const maxVal = Math.max(...funnelSteps.map((s) => s.value), 1);

  return (
    <SectionBlock title="📊 Métricas de funnel">
      {/* Funnel visual */}
      <div className="space-y-1.5 mb-4">
        {funnelSteps.map((step) => (
          <div key={step.label} className="flex items-center gap-2">
            <span className="w-24 text-[11px] text-gray-500 shrink-0">{step.label}</span>
            <div className="flex-1 h-5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${step.color} transition-all`}
                style={{ width: `${(step.value / maxVal) * 100}%` }}
              />
            </div>
            <span className="w-8 text-xs font-bold text-gray-700 text-right">{step.value}</span>
          </div>
        ))}
      </div>

      {/* KPIs financieros */}
      <div className="grid grid-cols-2 gap-2">
        {[
          { label: "Gasto total", value: fmtMetric(metrics.total_spent, "€") },
          { label: "Revenue atribuido", value: fmtMetric(metrics.revenue_attributed, "€") },
          { label: "CPL real", value: fmtMetric(metrics.cpl_real, "€") },
          { label: "Cost per show-up", value: fmtMetric(metrics.cost_per_show_up, "€") },
          { label: "Cost per close", value: fmtMetric(metrics.cost_per_close, "€") },
          { label: "ROAS", value: fmtMetric(metrics.roas, "", "x") },
          { label: "Ticket medio", value: fmtMetric(metrics.avg_closed_value, "€") },
          { label: "Perdidos", value: String(metrics.lost) },
        ].map((m) => (
          <div key={m.label} className="bg-gray-50 rounded-lg p-2.5">
            <p className="text-[10px] text-gray-400 uppercase tracking-wide">{m.label}</p>
            <p className="text-sm font-bold text-gray-800">{m.value}</p>
          </div>
        ))}
      </div>
    </SectionBlock>
  );
}

export function TabCampaign({
  campaign,
  metaStatus,
  onUpdated,
}: {
  campaign: Campaign;
  metaStatus: MetaStatus | null;
  onUpdated: (next: Campaign) => void;
}) {
  const [publishing, setPublishing] = useState(false);
  const [publishResult, setPublishResult] = useState<PublishResult | null>(null);
  const [publishError, setPublishError] = useState<string | null>(null);

  const [editing, setEditing] = useState(false);
  const [showEmpty, setShowEmpty] = useState(false);
  const [draft, setDraft] = useState<EditState>(() => initialEditState(campaign));
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const ads = campaign.ads_output as AdsOutput | null;
  const cj = ads?.campaign_json;
  const c = cj?.campaign;
  const adset = cj?.ad_set;
  const targeting = adset?.targeting;

  const isLocked = metaStatus?.is_locked ?? false;

  // Placeholder para campos sin valor cuando el usuario activa "Mostrar campos vacíos"
  const emptyHint = (label: string) =>
    showEmpty ? (
      <Field label={label}>
        <span className="text-xs text-gray-300 italic">Sin configurar</span>
      </Field>
    ) : null;

  function startEdit() {
    setDraft(initialEditState(campaign));
    setEditing(true);
    setSaveError(null);
  }

  function cancelEdit() {
    setEditing(false);
    setSaveError(null);
  }

  async function save() {
    setSaving(true);
    setSaveError(null);
    try {
      const original = initialEditState(campaign);
      const payload: CampaignUpdate = {};
      const changedStr = (k: keyof EditState) => draft[k] !== original[k];
      const changedArr = (k: keyof EditState) =>
        JSON.stringify(draft[k]) !== JSON.stringify(original[k]);

      // ── Campaña ──
      if (changedStr("campaign_name")) payload.campaign_name = draft.campaign_name;
      if (changedStr("objective")) payload.objective = draft.objective;
      if (changedStr("buying_type")) payload.buying_type = draft.buying_type;
      if (changedStr("campaign_budget_optimization"))
        payload.campaign_budget_optimization = draft.campaign_budget_optimization;
      if (changedStr("daily_budget_eur")) payload.daily_budget_eur = draft.daily_budget_eur;
      if (changedStr("lifetime_budget_eur")) payload.lifetime_budget_eur = draft.lifetime_budget_eur;
      if (changedStr("spend_cap_eur")) payload.spend_cap_eur = draft.spend_cap_eur;
      if (changedStr("campaign_bid_strategy")) payload.campaign_bid_strategy = draft.campaign_bid_strategy;
      if (changedStr("bid_cap_eur")) payload.bid_cap_eur = draft.bid_cap_eur;
      if (changedStr("campaign_start_time"))
        payload.campaign_start_time = localInputToIso(draft.campaign_start_time);
      if (changedStr("campaign_stop_time"))
        payload.campaign_stop_time = localInputToIso(draft.campaign_stop_time);
      if (changedArr("special_ad_categories")) payload.special_ad_categories = draft.special_ad_categories;
      if (changedArr("special_ad_category_country"))
        payload.special_ad_category_country = draft.special_ad_category_country;

      // ── Ad set ──
      if (changedStr("adset_name")) payload.adset_name = draft.adset_name;
      if (changedStr("optimization_goal")) payload.optimization_goal = draft.optimization_goal;
      if (changedStr("billing_event")) payload.billing_event = draft.billing_event;
      if (changedStr("bid_strategy")) payload.bid_strategy = draft.bid_strategy;
      if (changedStr("bid_amount_eur")) payload.bid_amount_eur = draft.bid_amount_eur;
      if (changedStr("adset_daily_budget_eur")) payload.adset_daily_budget_eur = draft.adset_daily_budget_eur;
      if (changedStr("adset_lifetime_budget_eur"))
        payload.adset_lifetime_budget_eur = draft.adset_lifetime_budget_eur;
      if (changedStr("adset_start_time"))
        payload.adset_start_time = localInputToIso(draft.adset_start_time);
      if (changedStr("adset_end_time")) payload.adset_end_time = localInputToIso(draft.adset_end_time);
      if (changedStr("destination_type")) payload.destination_type = draft.destination_type;
      if (changedArr("pacing_type")) payload.pacing_type = draft.pacing_type;
      if (changedStr("is_dynamic_creative")) payload.is_dynamic_creative = draft.is_dynamic_creative;
      if (changedStr("advantage_audience")) payload.advantage_audience = draft.advantage_audience;
      if (changedStr("dsa_beneficiary")) payload.dsa_beneficiary = draft.dsa_beneficiary;
      if (changedStr("dsa_payor")) payload.dsa_payor = draft.dsa_payor;

      // ── Pixel / eventos ──
      if (changedStr("pixel_id")) payload.pixel_id = draft.pixel_id;
      if (changedStr("custom_event_type")) payload.custom_event_type = draft.custom_event_type;
      if (changedStr("page_id")) payload.page_id = draft.page_id;
      if (changedStr("application_id")) payload.application_id = draft.application_id;
      if (changedStr("offsite_conversion_event_id"))
        payload.offsite_conversion_event_id = draft.offsite_conversion_event_id;

      // ── Reglas ──
      if (changedArr("attribution_spec")) payload.attribution_spec = draft.attribution_spec;
      if (changedArr("frequency_control_specs"))
        payload.frequency_control_specs = draft.frequency_control_specs;

      // ── Targeting ──
      if (changedStr("age_min")) payload.age_min = draft.age_min;
      if (changedStr("age_max")) payload.age_max = draft.age_max;
      if (changedArr("genders")) payload.genders = draft.genders;
      if (changedArr("countries")) payload.countries = draft.countries;
      if (changedArr("excluded_countries")) payload.excluded_countries = draft.excluded_countries;
      if (changedArr("publisher_platforms")) payload.publisher_platforms = draft.publisher_platforms;
      if (changedArr("facebook_positions")) payload.facebook_positions = draft.facebook_positions;
      if (changedArr("instagram_positions")) payload.instagram_positions = draft.instagram_positions;
      if (changedArr("audience_network_positions"))
        payload.audience_network_positions = draft.audience_network_positions;
      if (changedArr("messenger_positions")) payload.messenger_positions = draft.messenger_positions;
      if (changedArr("device_platforms")) payload.device_platforms = draft.device_platforms;
      if (changedArr("interests")) payload.interests = draft.interests;
      if (changedArr("behaviors")) payload.behaviors = draft.behaviors;
      if (changedArr("demographics")) payload.demographics = draft.demographics;
      if (changedArr("work_positions")) payload.work_positions = draft.work_positions;
      if (changedArr("custom_audiences")) payload.custom_audiences = draft.custom_audiences;
      if (changedArr("excluded_custom_audiences"))
        payload.excluded_custom_audiences = draft.excluded_custom_audiences;

      // ── Ads ──
      const adsDiff = draft.ads.filter((da, i) => {
        if (da.is_dco) return false; // DCO se edita regenerando el copy, no por campos
        const oa = original.ads[i];
        if (!oa) return true;
        return (
          da.headline !== oa.headline ||
          da.description !== oa.description ||
          da.message !== oa.message ||
          da.caption !== oa.caption ||
          da.link !== oa.link ||
          da.cta !== oa.cta ||
          da.conversion_domain !== oa.conversion_domain ||
          da.url_tags !== oa.url_tags
        );
      });
      if (adsDiff.length) payload.ads = adsDiff;

      // ── Landings ──
      const landingsDiff = draft.landings.filter((dl) => {
        const ol = original.landings.find((l) => l.id === dl.id);
        if (!ol) return false;
        return (
          dl.headline !== ol.headline ||
          dl.subheadline !== ol.subheadline ||
          dl.cta_text !== ol.cta_text ||
          dl.primary_color !== ol.primary_color ||
          JSON.stringify(dl.benefits) !== JSON.stringify(ol.benefits)
        );
      });
      if (landingsDiff.length)
        payload.landings = landingsDiff.map((l) => ({
          id: l.id,
          headline: l.headline,
          subheadline: l.subheadline,
          benefits: l.benefits,
          cta_text: l.cta_text,
          primary_color: l.primary_color,
        }));

      // ── Ad sets adicionales (reemplazo completo si cambió algo) ──
      if (JSON.stringify(draft.additional_ad_sets) !== JSON.stringify(original.additional_ad_sets)) {
        payload.additional_ad_sets = draft.additional_ad_sets;
      }

      const updated = await api.patch<Campaign>(`/campaigns/${campaign.plan_id}`, payload);
      onUpdated(updated);
      setEditing(false);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Error al guardar";
      setSaveError(msg);
    } finally {
      setSaving(false);
    }
  }

  async function handlePublish() {
    setPublishing(true);
    setPublishError(null);
    try {
      const result = await api.post<PublishResult>(`/campaigns/${campaign.plan_id}/publish`, {});
      setPublishResult(result);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Error al publicar";
      setPublishError(msg);
    } finally {
      setPublishing(false);
    }
  }

  return (
    <div className="space-y-4">
      {/* Banner + Edit toolbar */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        {metaStatus?.has_meta_campaign ? (
          <div
            className={`flex-1 rounded-xl border px-3 py-2 flex items-center gap-2 text-xs ${isLocked
              ? "bg-red-50 border-red-200 text-red-700"
              : metaStatus.meta_status === "PAUSED"
                ? "bg-amber-50 border-amber-200 text-amber-800"
                : "bg-gray-50 border-gray-200 text-gray-600"
              }`}
          >
            <span>{isLocked ? "🔒" : metaStatus.meta_status === "PAUSED" ? "⏸" : "ℹ"}</span>
            <span>
              {isLocked
                ? "Campaña ACTIVA en Meta — pausa antes de editar."
                : metaStatus.meta_status
                  ? `Estado Meta: ${metaStatus.meta_status}`
                  : "Sin estado disponible"}
            </span>
            {metaStatus.error && <span className="ml-auto text-[10px] opacity-70">{metaStatus.error}</span>}
          </div>
        ) : (
          <div className="flex-1" />
        )}

        {!editing ? (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowEmpty((v) => !v)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors border ${showEmpty
                ? "bg-brand-50 text-brand-700 border-brand-200"
                : "bg-white text-gray-500 border-gray-200 hover:bg-gray-50"
                }`}
              title="Muestra también los campos sin valor configurado"
            >
              {showEmpty ? "Ocultar campos vacíos" : "Mostrar campos vacíos"}
            </button>
            <button
              disabled={isLocked}
              onClick={startEdit}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${isLocked
                ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                : "bg-brand-600 text-white hover:bg-brand-700"
                }`}
            >
              ✏️ Editar campaña
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            {saveError && <span className="text-xs text-red-600">{saveError}</span>}
            <button
              onClick={cancelEdit}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700"
            >
              Cancelar
            </button>
            <button
              disabled={saving}
              onClick={save}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-brand-600 hover:bg-brand-700 text-white disabled:opacity-60"
            >
              {saving ? "Guardando…" : "Guardar cambios"}
            </button>
          </div>
        )}
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-2">
        {[
          { label: "Visitas", value: campaign.total_views.toLocaleString(), icon: "👁" },
          { label: "Leads", value: campaign.total_leads.toLocaleString(), icon: "🎯" },
          { label: "Conversiones", value: campaign.total_conversions.toLocaleString(), icon: "✅" },
          {
            label: "Conv. rate",
            value: conversionRate(campaign.total_views, campaign.total_conversions),
            icon: "📈",
          },
        ].map((m) => (
          <div key={m.label} className="bg-gray-50 rounded-xl p-3 text-center">
            <p className="text-base mb-0.5">{m.icon}</p>
            <p className="text-base font-bold text-gray-900">{m.value}</p>
            <p className="text-xs text-gray-400">{m.label}</p>
          </div>
        ))}
      </div>

      {/* Funnel metrics */}
      <FunnelMetricsSection planId={campaign.plan_id} />

      {/* Optimización IA del modelo Meta */}
      {!editing && ads && (ads.optimization_rationale || (ads.optimization_applied?.length ?? 0) > 0) && (
        <SectionBlock
          title="🧠 Optimización IA del modelo"
          info="Ajustes técnicos que la IA calculó como óptimos para esta campaña (puja, pacing, atribución, edad, género, frequency cap, fechas…) sobre la base generada. Puedes sobrescribirlos editando la campaña."
        >
          {ads.optimization_rationale && (
            <p className="text-xs text-gray-600 bg-brand-50 border border-brand-100 rounded-lg px-3 py-2 mb-2 leading-relaxed">
              {ads.optimization_rationale}
            </p>
          )}
          {ads.optimization_applied && ads.optimization_applied.length > 0 && (
            <ul className="space-y-1">
              {ads.optimization_applied.map((note, i) => (
                <li key={i} className="flex items-start gap-1.5 text-xs text-gray-700">
                  <span className="text-brand-500 shrink-0">✓</span>
                  <span>{note}</span>
                </li>
              ))}
            </ul>
          )}
        </SectionBlock>
      )}

      {/* Datos reales de la cuenta Meta (Fase 2) */}
      {!editing && ads?.account_data && (() => {
        const est = ads.account_data.audience_estimate;
        const bm = ads.account_data.benchmarks;
        const hasAudience = est?.audience_lower != null;
        const hasBench = bm && (bm.cpm != null || bm.cpc != null || bm.ctr != null);
        if (!hasAudience && !hasBench) return null;
        const fmtNum = (n: number) => n.toLocaleString("es-ES");
        return (
          <SectionBlock
            title="📡 Datos reales de tu cuenta Meta"
            info="Tamaño de audiencia estimado por Meta para este targeting y métricas medias de tu cuenta (últimos 90 días). La IA los usa para calibrar puja, presupuesto y audiencia."
          >
            {hasAudience && (
              <div className="mb-3 bg-sky-50 border border-sky-100 rounded-lg px-3 py-2">
                <p className="text-[10px] text-sky-500 uppercase tracking-wide">Audiencia estimada</p>
                <p className="text-sm font-bold text-sky-800">
                  {fmtNum(est!.audience_lower!)}
                  {est!.audience_upper ? ` – ${fmtNum(est!.audience_upper)}` : ""} personas
                </p>
              </div>
            )}
            {hasBench && (
              <div className="grid grid-cols-3 gap-2">
                {[
                  { label: "CPM medio", value: bm!.cpm != null ? `€${bm!.cpm.toFixed(2)}` : "—" },
                  { label: "CPC medio", value: bm!.cpc != null ? `€${bm!.cpc.toFixed(2)}` : "—" },
                  { label: "CTR medio", value: bm!.ctr != null ? `${bm!.ctr.toFixed(2)}%` : "—" },
                ].map((m) => (
                  <div key={m.label} className="bg-gray-50 rounded-lg p-2 text-center">
                    <p className="text-sm font-bold text-gray-800">{m.value}</p>
                    <p className="text-[10px] text-gray-400">{m.label}</p>
                  </div>
                ))}
              </div>
            )}
          </SectionBlock>
        );
      })()}

      {/* Ad sets adicionales (Fase 3: test de audiencia + retargeting) */}
      {editing && draft.additional_ad_sets.length > 0 && (
        <SectionBlock
          title="🧩 Ad sets adicionales — edición"
          info="Edita cada conjunto adicional igual que el principal: targeting, entrega, pixel, anuncios. Puedes eliminarlos. Se guardan al pulsar «Guardar cambios»."
        >
          <div className="space-y-3">
            {draft.additional_ad_sets.map((aset, i) => (
              <AdSetEditor
                key={i}
                adset={aset}
                onChange={(next) => {
                  const arr = [...draft.additional_ad_sets];
                  arr[i] = next;
                  setDraft({ ...draft, additional_ad_sets: arr });
                }}
                onDelete={() =>
                  setDraft({
                    ...draft,
                    additional_ad_sets: draft.additional_ad_sets.filter((_, j) => j !== i),
                  })
                }
              />
            ))}
          </div>
        </SectionBlock>
      )}

      {!editing && (ads?.campaign_json?.additional_ad_sets?.length ?? 0) > 0 && (
        <SectionBlock
          title="🧩 Ad sets adicionales"
          info="Además del ad set principal (con intereses), la IA crea conjuntos paralelos para que Meta compare audiencias: una audiencia amplia y, si tienes audiencias personalizadas, retargeting. Con CBO el presupuesto se reparte solo."
        >
          <div className="space-y-2">
            {ads!.campaign_json!.additional_ad_sets!.map((aset, i) => {
              const t = aset.targeting;
              const countries = t?.geo_locations?.countries?.join(", ");
              const ca = t?.custom_audiences;
              const hasInterests = (t?.flexible_spec?.[0]?.interests?.length ?? 0) > 0;
              let audience = "Audiencia amplia (sin intereses)";
              if (ca && ca.length > 0) {
                audience = "Retargeting: " + ca.map((a) => a.name || a.id).join(", ");
              } else if (hasInterests) {
                audience = "Con intereses";
              }
              return (
                <div key={i} className="rounded-lg border border-gray-200 p-2.5">
                  <p className="text-sm font-semibold text-gray-800">{aset.name}</p>
                  <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 mt-1 text-[11px] text-gray-500">
                    <span className="text-violet-600 font-medium">{audience}</span>
                    {t?.age_min != null && (
                      <span>· {t.age_min}–{t.age_max} años</span>
                    )}
                    {countries && <span>· {countries}</span>}
                    <span>· {aset.ads?.length ?? 0} anuncio(s)</span>
                  </div>
                </div>
              );
            })}
          </div>
        </SectionBlock>
      )}

      {/* ── LAYOUT 2 columnas: Campaign+AdSet+Budget+Targeting (col 1) | Ads+Landings+Publish (col 2) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* ─── COLUMNA IZQ ─── */}
        <div className="space-y-4">

          {/* CAMPAÑA */}
          {c && (
            <SectionBlock title="📣 Campaña Meta">
              {editing ? (
                <div className="space-y-3">
                  <Field label="Nombre">
                    <TextInput
                      value={draft.campaign_name}
                      onChange={(v) => setDraft({ ...draft, campaign_name: v })}
                    />
                  </Field>
                  <Field label="Objetivo">
                    <SelectInput
                      value={draft.objective}
                      onChange={(v) => setDraft({ ...draft, objective: v })}
                      options={OBJECTIVE_OPTIONS}
                    />
                  </Field>
                  <Field
                    label="Modo de compra"
                    info="Subasta: lo normal, pujas dinámicas. Reservada: alcance y frecuencia fijos comprados por adelantado (solo grandes campañas)."
                  >
                    <SelectInput
                      value={draft.buying_type}
                      onChange={(v) => setDraft({ ...draft, buying_type: v })}
                      options={BUYING_TYPE_OPTIONS}
                    />
                  </Field>
                  <Field
                    label="Optimización de presupuesto (CBO)"
                    info="Si está activo, Meta reparte el presupuesto automáticamente entre los conjuntos de anuncios según rendimiento. Si no, fijas el presupuesto por conjunto."
                  >
                    <Toggle
                      checked={draft.campaign_budget_optimization}
                      onChange={(v) => setDraft({ ...draft, campaign_budget_optimization: v })}
                      label="Presupuesto a nivel campaña"
                    />
                  </Field>
                  <Field
                    label="Presupuesto diario (€)"
                    info="Gasto medio por día. Meta puede gastar hasta un 25% más algunos días y compensar en otros."
                  >
                    <NumberInput
                      value={draft.daily_budget_eur}
                      step={0.5}
                      min={1}
                      onChange={(v) => setDraft({ ...draft, daily_budget_eur: v })}
                      suffix={`≈ €${(draft.daily_budget_eur * 30).toFixed(0)}/mes`}
                    />
                  </Field>
                  <Field
                    label="Presupuesto total / vida (€) — 0 = sin límite"
                    info="Gasto máximo para toda la vida de la campaña; Meta lo distribuye en el tiempo. Usa esto o el diario, no ambos. 0 = usar diario."
                  >
                    <NumberInput
                      value={draft.lifetime_budget_eur}
                      step={1}
                      min={0}
                      onChange={(v) => setDraft({ ...draft, lifetime_budget_eur: v })}
                    />
                  </Field>
                  <Field
                    label="Tope de gasto (€) — 0 = sin tope"
                    info="Límite duro acumulado que la campaña nunca superará, independientemente del presupuesto diario o de vida."
                  >
                    <NumberInput
                      value={draft.spend_cap_eur}
                      step={1}
                      min={0}
                      onChange={(v) => setDraft({ ...draft, spend_cap_eur: v })}
                    />
                  </Field>
                  <Field
                    label="Estrategia de puja (campaña)"
                    info="Cómo puja Meta en la subasta: coste mínimo (gastar todo al menor coste), con tope de puja, coste objetivo estable o ROAS mínimo garantizado."
                  >
                    <SelectInput
                      value={draft.campaign_bid_strategy}
                      onChange={(v) => setDraft({ ...draft, campaign_bid_strategy: v })}
                      options={CAMPAIGN_BID_OPTIONS}
                    />
                  </Field>
                  <Field
                    label="Tope de puja (€) — 0 = sin tope"
                    info="Cantidad máxima que pagas por cada resultado en la subasta. Solo aplica con estrategias 'con tope de puja' o 'coste objetivo'."
                  >
                    <NumberInput
                      value={draft.bid_cap_eur}
                      step={0.5}
                      min={0}
                      onChange={(v) => setDraft({ ...draft, bid_cap_eur: v })}
                    />
                  </Field>
                  <div className="grid grid-cols-2 gap-2">
                    <Field label="Inicio">
                      <DateInput
                        value={draft.campaign_start_time}
                        onChange={(v) => setDraft({ ...draft, campaign_start_time: v })}
                      />
                    </Field>
                    <Field label="Fin">
                      <DateInput
                        value={draft.campaign_stop_time}
                        onChange={(v) => setDraft({ ...draft, campaign_stop_time: v })}
                      />
                    </Field>
                  </div>
                  <Field
                    label="Categorías especiales de anuncio"
                    info="Obligatorio por ley si anuncias empleo, vivienda, crédito, política o finanzas. Limita el targeting (edad, género, código postal) para evitar discriminación."
                  >
                    <CheckboxGroup
                      options={SPECIAL_AD_CATEGORY_OPTIONS}
                      selected={draft.special_ad_categories}
                      onChange={(v) => setDraft({ ...draft, special_ad_categories: v })}
                    />
                  </Field>
                  {draft.special_ad_categories.length > 0 && (
                    <Field label="Países categoría especial">
                      <CountriesEditor
                        value={draft.special_ad_category_country}
                        onChange={(v) => setDraft({ ...draft, special_ad_category_country: v })}
                      />
                    </Field>
                  )}
                </div>
              ) : (
                <>
                  <InfoRow label="Nombre" value={c.name} />
                  <InfoRow label="Objetivo" value={OBJECTIVE_LABELS[c.objective] ?? c.objective} />
                  <InfoRow
                    label="Estado inicial"
                    value={
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700 text-xs font-medium">
                        ⏸ {c.status}
                      </span>
                    }
                  />
                  <InfoRow label="Modo compra" value={BUYING_TYPE_LABELS[c.buying_type ?? "AUCTION"]} />
                  <InfoRow
                    label="Optimización presupuesto"
                    value={
                      c.campaign_budget_optimization
                        ? "✅ CBO — Optimización a nivel campaña"
                        : "❌ Presupuesto por ad set"
                    }
                  />
                  <InfoRow label="Presupuesto diario" value={eurFromCents(c.daily_budget)} />
                  {c.lifetime_budget && (
                    <InfoRow label="Presupuesto vida" value={eurFromCents(c.lifetime_budget)} />
                  )}
                  {c.spend_cap && (
                    <InfoRow label="Tope de gasto" value={eurFromCents(c.spend_cap)} />
                  )}
                  {c.bid_strategy && (
                    <InfoRow label="Estrategia puja" value={BID_LABELS[c.bid_strategy] ?? c.bid_strategy} />
                  )}
                  {c.bid_cap && <InfoRow label="Tope de puja" value={eurFromCents(c.bid_cap)} />}
                  {c.start_time && <InfoRow label="Inicio" value={formatDateTime(c.start_time)} mono />}
                  {c.stop_time && <InfoRow label="Fin" value={formatDateTime(c.stop_time)} mono />}
                  <InfoRow
                    label="Categorías especiales"
                    value={
                      c.special_ad_categories?.length ? (
                        <div className="flex flex-wrap gap-1 justify-end">
                          {c.special_ad_categories.map((cat) => (
                            <Chip key={cat} label={SPECIAL_AD_CATEGORIES[cat] ?? cat} />
                          ))}
                        </div>
                      ) : (
                        <span className="text-gray-400">Ninguna</span>
                      )
                    }
                  />
                  {c.special_ad_category_country && c.special_ad_category_country.length > 0 && (
                    <InfoRow
                      label="Países cat. especial"
                      value={c.special_ad_category_country.join(", ")}
                      mono
                    />
                  )}
                </>
              )}
            </SectionBlock>
          )}

          {/* PRESUPUESTO */}
          {!editing && ads?.budget && (
            <SectionBlock title="💰 Presupuesto">
              <div className="grid grid-cols-3 gap-2 mb-3">
                {[
                  { label: "Mensual", value: `€${ads.budget.monthly_eur}` },
                  { label: "Diario", value: `€${ads.budget.daily_eur.toFixed(2)}` },
                  { label: "API (céntimos)", value: `${ads.budget.daily_cents}¢` },
                ].map((b) => (
                  <div key={b.label} className="bg-violet-50 rounded-lg p-2 text-center">
                    <p className="text-sm font-bold text-violet-800">{b.value}</p>
                    <p className="text-[11px] text-violet-500">{b.label}</p>
                  </div>
                ))}
              </div>
              <div className="flex items-start gap-2 text-xs text-violet-700 bg-violet-50 border border-violet-100 rounded-lg px-3 py-2">
                <span>💡</span>
                <span>{ads.budget_summary}</span>
              </div>
            </SectionBlock>
          )}

          {/* AD SET */}
          {adset && (
            <SectionBlock title="⚙️ Ad Set — Entrega y optimización">
              {editing ? (
                <div className="space-y-3">
                  <Field label="Nombre del ad set">
                    <TextInput
                      value={draft.adset_name}
                      onChange={(v) => setDraft({ ...draft, adset_name: v })}
                    />
                  </Field>
                  <Field
                    label="Optimización (optimization_goal)"
                    info="Qué acción intenta maximizar Meta al entregar el anuncio: leads, conversiones, clics, vistas de landing, alcance… Define a quién muestra el anuncio."
                  >
                    <SelectInput
                      value={draft.optimization_goal}
                      onChange={(v) => setDraft({ ...draft, optimization_goal: v })}
                      options={OPTIMIZATION_OPTIONS}
                    />
                  </Field>
                  <Field
                    label="Facturación (billing_event)"
                    info="Por qué evento te cobra Meta: CPM (cada 1000 impresiones), CPC (cada clic) o ThruPlay (vídeo reproducido)."
                  >
                    <SelectInput
                      value={draft.billing_event}
                      onChange={(v) => setDraft({ ...draft, billing_event: v })}
                      options={BILLING_OPTIONS}
                    />
                  </Field>
                  <Field
                    label="Estrategia de puja (ad set)"
                    info="Igual que en campaña pero a nivel de conjunto. Solo se usa si la campaña no controla la puja de forma global."
                  >
                    <SelectInput
                      value={draft.bid_strategy}
                      onChange={(v) => setDraft({ ...draft, bid_strategy: v })}
                      options={BID_OPTIONS}
                    />
                  </Field>
                  <Field
                    label="Importe de puja (€) — 0 = automático"
                    info="Puja manual por resultado en la subasta. 0 deja que Meta puje automáticamente para gastar todo el presupuesto."
                  >
                    <NumberInput
                      value={draft.bid_amount_eur}
                      step={0.5}
                      min={0}
                      onChange={(v) => setDraft({ ...draft, bid_amount_eur: v })}
                    />
                  </Field>
                  <div className="grid grid-cols-2 gap-2">
                    <Field
                      label="Presupuesto diario ad set (€)"
                      info="Presupuesto a nivel de este conjunto de anuncios. Solo se usa si la campaña NO tiene CBO activado."
                    >
                      <NumberInput
                        value={draft.adset_daily_budget_eur}
                        step={0.5}
                        min={0}
                        onChange={(v) => setDraft({ ...draft, adset_daily_budget_eur: v })}
                      />
                    </Field>
                    <Field
                      label="Presupuesto vida ad set (€)"
                      info="Presupuesto total del conjunto para todo su periodo. Requiere fecha de fin. Solo sin CBO."
                    >
                      <NumberInput
                        value={draft.adset_lifetime_budget_eur}
                        step={1}
                        min={0}
                        onChange={(v) => setDraft({ ...draft, adset_lifetime_budget_eur: v })}
                      />
                    </Field>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <Field label="Inicio ad set">
                      <DateInput
                        value={draft.adset_start_time}
                        onChange={(v) => setDraft({ ...draft, adset_start_time: v })}
                      />
                    </Field>
                    <Field label="Fin ad set">
                      <DateInput
                        value={draft.adset_end_time}
                        onChange={(v) => setDraft({ ...draft, adset_end_time: v })}
                      />
                    </Field>
                  </div>
                  <Field
                    label="Destino del clic"
                    info="A dónde lleva el anuncio al hacer clic: sitio web, app, Messenger, WhatsApp, formulario nativo (On Ad) o llamada."
                  >
                    <SelectInput
                      value={draft.destination_type}
                      onChange={(v) => setDraft({ ...draft, destination_type: v })}
                      options={DESTINATION_OPTIONS}
                      allowEmpty
                      emptyLabel="— Por defecto —"
                    />
                  </Field>
                  <Field
                    label="Ritmo de entrega (pacing)"
                    info="Estándar: reparte el gasto de forma uniforme durante el día. Acelerado: gasta lo antes posible (útil para eventos con poco tiempo)."
                  >
                    <CheckboxGroup
                      options={PACING_OPTIONS}
                      selected={draft.pacing_type}
                      onChange={(v) => setDraft({ ...draft, pacing_type: v })}
                    />
                  </Field>
                  <Field
                    label="Automatizaciones"
                    info="Dynamic Creative combina automáticamente tus imágenes y textos para encontrar la mejor variante. Advantage+ Audience amplía tu audiencia más allá de la que definiste si encuentra mejores resultados."
                  >
                    <div className="flex flex-wrap gap-1.5">
                      <Toggle
                        checked={draft.is_dynamic_creative}
                        onChange={(v) => setDraft({ ...draft, is_dynamic_creative: v })}
                        label="Dynamic Creative (DCO)"
                      />
                      <Toggle
                        checked={draft.advantage_audience}
                        onChange={(v) => setDraft({ ...draft, advantage_audience: v })}
                        label="Advantage+ Audience"
                      />
                    </div>
                  </Field>
                  <div className="grid grid-cols-2 gap-2">
                    <Field
                      label="DSA Beneficiario"
                      info="Transparencia de anuncios UE (ley DSA): nombre de la empresa que se beneficia del anuncio. Obligatorio para anunciar en Europa."
                    >
                      <TextInput
                        value={draft.dsa_beneficiary}
                        onChange={(v) => setDraft({ ...draft, dsa_beneficiary: v })}
                      />
                    </Field>
                    <Field
                      label="DSA Pagador"
                      info="Ley DSA (UE): nombre de quien paga el anuncio. Suele coincidir con el beneficiario."
                    >
                      <TextInput
                        value={draft.dsa_payor}
                        onChange={(v) => setDraft({ ...draft, dsa_payor: v })}
                      />
                    </Field>
                  </div>
                </div>
              ) : (
                <>
                  <InfoRow label="Nombre" value={adset.name} />
                  <InfoRow
                    label="Optimization goal"
                    value={OPTIMIZATION_LABELS[adset.optimization_goal] ?? adset.optimization_goal}
                  />
                  <InfoRow
                    label="Billing event"
                    value={BILLING_LABELS[adset.billing_event] ?? adset.billing_event}
                  />
                  <InfoRow
                    label="Bid strategy"
                    value={BID_LABELS[adset.bid_strategy] ?? adset.bid_strategy}
                  />
                  {adset.bid_amount && (
                    <InfoRow label="Bid amount" value={eurFromCents(adset.bid_amount)} />
                  )}
                  {adset.daily_budget && (
                    <InfoRow label="Daily budget (ad set)" value={eurFromCents(adset.daily_budget)} />
                  )}
                  {adset.lifetime_budget && (
                    <InfoRow label="Lifetime budget" value={eurFromCents(adset.lifetime_budget)} />
                  )}
                  {adset.destination_type && (
                    <InfoRow
                      label="Destino del clic"
                      value={DESTINATION_LABELS[adset.destination_type] ?? adset.destination_type}
                    />
                  )}
                  {adset.pacing_type && (
                    <InfoRow
                      label="Ritmo de entrega"
                      value={
                        <div className="flex flex-wrap gap-1 justify-end">
                          {adset.pacing_type.map((p) => (
                            <Chip key={p} label={PACING_LABELS[p] ?? p} />
                          ))}
                        </div>
                      }
                    />
                  )}
                  {adset.is_dynamic_creative !== undefined && (
                    <InfoRow
                      label="Dynamic Creative"
                      value={adset.is_dynamic_creative ? "✅ Activado (DCO)" : "❌ Desactivado"}
                    />
                  )}
                  {adset.targeting_automation?.advantage_audience !== undefined && (
                    <InfoRow
                      label="Advantage+ Audience"
                      value={
                        adset.targeting_automation.advantage_audience === 1
                          ? "✅ Expansión automática activa"
                          : "❌ Desactivada"
                      }
                    />
                  )}
                  {adset.start_time && <InfoRow label="Inicio" value={formatDateTime(adset.start_time)} mono />}
                  {adset.end_time && <InfoRow label="Fin" value={formatDateTime(adset.end_time)} mono />}
                  {adset.dsa_beneficiary && (
                    <InfoRow label="DSA Beneficiario" value={adset.dsa_beneficiary} />
                  )}
                  {adset.dsa_payor && <InfoRow label="DSA Pagador" value={adset.dsa_payor} />}
                </>
              )}
            </SectionBlock>
          )}

          {/* PROMOTED OBJECT — Pixel / Eventos */}
          {(editing || showEmpty || adset?.promoted_object) && (
            <SectionBlock
              title="🎯 Pixel y eventos de conversión"
              info="Conecta tu campaña con el píxel de Meta para medir y optimizar conversiones reales en tu web (no solo clics)."
            >
              {editing ? (
                <div className="space-y-3">
                  <Field
                    label="Pixel ID"
                    info="Identificador del píxel de Meta instalado en tu web. Es el que registra las conversiones que ocurren tras el clic."
                  >
                    <TextInput
                      value={draft.pixel_id}
                      onChange={(v) => setDraft({ ...draft, pixel_id: v })}
                      placeholder="123456789012345"
                      mono
                    />
                  </Field>
                  <Field
                    label="Evento de conversión"
                    info="Acción que cuenta como conversión (Lead, Compra, Registro…). Debe estar registrada por tu píxel para que Meta optimice hacia ella."
                  >
                    <SelectInput
                      value={draft.custom_event_type}
                      onChange={(v) => setDraft({ ...draft, custom_event_type: v })}
                      options={CUSTOM_EVENT_OPTIONS}
                      allowEmpty
                    />
                  </Field>
                  <Field
                    label="Evento personalizado (offsite_conversion_event_id)"
                    info="ID de una conversión personalizada definida en tu Administrador de eventos, en vez de un evento estándar. Déjalo vacío si usas un evento estándar."
                  >
                    <TextInput
                      value={draft.offsite_conversion_event_id}
                      onChange={(v) => setDraft({ ...draft, offsite_conversion_event_id: v })}
                      placeholder="ID evento personalizado"
                      mono
                    />
                  </Field>
                  <div className="grid grid-cols-2 gap-2">
                    <Field
                      label="Page ID"
                      info="ID de la página de Facebook desde la que se publica el anuncio."
                    >
                      <TextInput
                        value={draft.page_id}
                        onChange={(v) => setDraft({ ...draft, page_id: v })}
                        mono
                      />
                    </Field>
                    <Field
                      label="App ID"
                      info="ID de la app que se promociona (solo campañas de instalación o eventos in-app)."
                    >
                      <TextInput
                        value={draft.application_id}
                        onChange={(v) => setDraft({ ...draft, application_id: v })}
                        mono
                      />
                    </Field>
                  </div>
                </div>
              ) : (
                <>
                  {adset?.promoted_object?.pixel_id && (
                    <InfoRow label="Pixel ID" value={adset.promoted_object.pixel_id} mono />
                  )}
                  {adset?.promoted_object?.custom_event_type && (
                    <InfoRow
                      label="Evento de conversión"
                      value={
                        CUSTOM_EVENT_TYPES[adset.promoted_object.custom_event_type] ??
                        adset.promoted_object.custom_event_type
                      }
                    />
                  )}
                  {adset?.promoted_object?.page_id && (
                    <InfoRow label="Page ID" value={adset.promoted_object.page_id} mono />
                  )}
                  {adset?.promoted_object?.application_id && (
                    <InfoRow label="App ID" value={adset.promoted_object.application_id} mono />
                  )}
                  {adset?.promoted_object?.offsite_conversion_event_id && (
                    <InfoRow
                      label="Evento personalizado"
                      value={adset.promoted_object.offsite_conversion_event_id}
                      mono
                    />
                  )}
                  {!adset?.promoted_object && (
                    <p className="text-xs text-gray-300 italic">Sin configurar</p>
                  )}
                </>
              )}
            </SectionBlock>
          )}

          {/* ATTRIBUTION */}
          {(editing || showEmpty || (adset?.attribution_spec && adset.attribution_spec.length > 0)) && (
            <SectionBlock
              title="📊 Ventana de atribución"
              info="Cuánto tiempo tras ver o hacer clic en el anuncio se le atribuye una conversión. Ej: 'clic 7 días' = cuenta compras hasta 7 días después de hacer clic."
            >
              {editing ? (
                <AttributionEditor
                  specs={draft.attribution_spec}
                  onChange={(v) => setDraft({ ...draft, attribution_spec: v })}
                />
              ) : adset?.attribution_spec && adset.attribution_spec.length > 0 ? (
                adset.attribution_spec.map((a, i) => (
                  <InfoRow
                    key={i}
                    label={ATTRIBUTION_EVENT_LABELS[a.event_type] ?? a.event_type}
                    value={`${a.window_days} día${a.window_days !== 1 ? "s" : ""}`}
                  />
                ))
              ) : (
                <p className="text-xs text-gray-300 italic">Sin configurar</p>
              )}
            </SectionBlock>
          )}

          {/* FREQUENCY CAP */}
          {(editing || showEmpty || (adset?.frequency_control_specs && adset.frequency_control_specs.length > 0)) && (
            <SectionBlock
              title="🔁 Frequency Cap"
              info="Límite de veces que una misma persona ve el anuncio en un periodo. Evita saturar a la audiencia. Ej: máx 2 impresiones cada 7 días."
            >
              {editing ? (
                <FrequencyEditor
                  specs={draft.frequency_control_specs}
                  onChange={(v) => setDraft({ ...draft, frequency_control_specs: v })}
                />
              ) : adset?.frequency_control_specs && adset.frequency_control_specs.length > 0 ? (
                adset.frequency_control_specs.map((f, i) => (
                  <InfoRow
                    key={i}
                    label={f.event}
                    value={`Max ${f.max_frequency} cada ${f.interval_days}d`}
                  />
                ))
              ) : (
                <p className="text-xs text-gray-300 italic">Sin configurar</p>
              )}
            </SectionBlock>
          )}

        </div>

        {/* ─── COLUMNA DER ─── */}
        <div className="space-y-4">

          {/* TARGETING */}
          {targeting && (
            <SectionBlock title="👥 Targeting — Audiencia">
              {/* Edad */}
              <Field label="Rango de edad">
                {editing ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      min="13"
                      max="65"
                      value={draft.age_min}
                      onChange={(e) => setDraft({ ...draft, age_min: Number(e.target.value) })}
                      className="w-16 px-2 py-1 text-xs border border-gray-200 rounded"
                    />
                    <span className="text-xs text-gray-400">a</span>
                    <input
                      type="number"
                      min="13"
                      max="65"
                      value={draft.age_max}
                      onChange={(e) => setDraft({ ...draft, age_max: Number(e.target.value) })}
                      className="w-16 px-2 py-1 text-xs border border-gray-200 rounded"
                    />
                    <span className="text-xs text-gray-400">años</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-3">
                    <div className="flex-1 bg-gray-100 rounded-full h-2 relative">
                      <div
                        className="absolute h-2 rounded-full bg-violet-500"
                        style={{
                          left: `${((targeting.age_min - 13) / (65 - 13)) * 100}%`,
                          right: `${100 - ((targeting.age_max - 13) / (65 - 13)) * 100}%`,
                        }}
                      />
                    </div>
                    <span className="text-xs font-semibold text-gray-700 shrink-0">
                      {targeting.age_min} – {targeting.age_max} años
                    </span>
                  </div>
                )}
              </Field>

              {/* Géneros */}
              {editing ? (
                <Field label="Géneros (vacío = todos)">
                  <CheckboxGroup
                    options={GENDER_OPTIONS}
                    selected={draft.genders.map(String)}
                    onChange={(v) => setDraft({ ...draft, genders: v.map(Number) })}
                  />
                </Field>
              ) : (
                targeting.genders &&
                targeting.genders.length > 0 && (
                  <Field label="Géneros">
                    <div className="flex gap-2">
                      {targeting.genders.map((g) => (
                        <Chip key={g} label={GENDER_LABELS[g] ?? `Género ${g}`} />
                      ))}
                    </div>
                  </Field>
                )
              )}

              {/* Idiomas */}
              {!editing &&
                (targeting.languages && targeting.languages.length > 0 ? (
                  <Field label="Idiomas">
                    <div className="flex flex-wrap gap-1">
                      {targeting.languages.map((l) => (
                        <Chip key={l} label={`ID ${l}`} />
                      ))}
                    </div>
                  </Field>
                ) : (
                  emptyHint("Idiomas")
                ))}

              {/* Países */}
              <Field label="Países">
                {editing ? (
                  <CountriesEditor
                    value={draft.countries}
                    onChange={(v) => setDraft({ ...draft, countries: v })}
                  />
                ) : (
                  <div className="flex flex-wrap gap-1.5">
                    {(targeting.geo_locations?.countries ?? []).map((c) => (
                      <Chip key={c} label={COUNTRY_NAMES[c] ?? c} highlight />
                    ))}
                  </div>
                )}
              </Field>

              {/* Geo extra: regions, cities, zips */}
              {!editing &&
                (targeting.geo_locations?.regions && targeting.geo_locations.regions.length > 0 ? (
                  <Field label="Regiones">
                    <div className="flex flex-wrap gap-1">
                      {targeting.geo_locations.regions.map((r, i) => (
                        <Chip key={i} label={`Region ${r.key}`} />
                      ))}
                    </div>
                  </Field>
                ) : (
                  emptyHint("Regiones")
                ))}
              {!editing &&
                (targeting.geo_locations?.cities && targeting.geo_locations.cities.length > 0 ? (
                  <Field label="Ciudades">
                    <div className="flex flex-wrap gap-1">
                      {targeting.geo_locations.cities.map((city, i) => (
                        <Chip
                          key={i}
                          label={`${city.key}${city.radius ? ` · ${city.radius}${city.distance_unit?.[0] ?? "km"}` : ""
                            }`}
                        />
                      ))}
                    </div>
                  </Field>
                ) : (
                  emptyHint("Ciudades")
                ))}
              {editing ? (
                <Field label="Excluir países">
                  <CountriesEditor
                    value={draft.excluded_countries}
                    onChange={(v) => setDraft({ ...draft, excluded_countries: v })}
                  />
                </Field>
              ) : targeting.excluded_geo_locations?.countries &&
                targeting.excluded_geo_locations.countries.length > 0 ? (
                <Field label="Excluir países">
                  <div className="flex flex-wrap gap-1">
                    {targeting.excluded_geo_locations.countries.map((c) => (
                      <span
                        key={c}
                        className="px-2 py-0.5 text-xs rounded-full bg-red-50 text-red-600 border border-red-200"
                      >
                        ❌ {COUNTRY_NAMES[c] ?? c}
                      </span>
                    ))}
                  </div>
                </Field>
              ) : (
                emptyHint("Excluir países")
              )}
              {!editing &&
                (targeting.geo_locations?.location_types &&
                  targeting.geo_locations.location_types.length > 0 ? (
                  <Field label="Tipo de localización">
                    <div className="flex gap-1">
                      {targeting.geo_locations.location_types.map((t) => (
                        <Chip key={t} label={t} />
                      ))}
                    </div>
                  </Field>
                ) : (
                  emptyHint("Tipo de localización")
                ))}

              {/* Plataformas */}
              <Field label="Plataformas">
                {editing ? (
                  <CheckboxGroup
                    options={PLATFORM_OPTIONS}
                    selected={draft.publisher_platforms}
                    onChange={(v) => setDraft({ ...draft, publisher_platforms: v })}
                  />
                ) : (
                  <div className="flex gap-2 flex-wrap">
                    {(targeting.publisher_platforms ?? []).map((p) => (
                      <span
                        key={p}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-50 border border-gray-200 text-xs font-medium text-gray-700"
                      >
                        {PLATFORM_ICONS[p] ?? "📱"} {p.charAt(0).toUpperCase() + p.slice(1)}
                      </span>
                    ))}
                  </div>
                )}
              </Field>

              {/* Posiciones FB + IG */}
              <div className="grid grid-cols-2 gap-3">
                <Field label="📘 Facebook">
                  {editing ? (
                    <CheckboxGroup
                      options={FACEBOOK_POSITIONS}
                      selected={draft.facebook_positions}
                      onChange={(v) => setDraft({ ...draft, facebook_positions: v })}
                    />
                  ) : (
                    <div className="flex flex-wrap gap-1">
                      {(targeting.facebook_positions ?? []).map((p) => (
                        <Chip key={p} label={PLACEMENT_LABELS[p] ?? p} />
                      ))}
                    </div>
                  )}
                </Field>
                <Field label="📸 Instagram">
                  {editing ? (
                    <CheckboxGroup
                      options={INSTAGRAM_POSITIONS}
                      selected={draft.instagram_positions}
                      onChange={(v) => setDraft({ ...draft, instagram_positions: v })}
                    />
                  ) : (
                    <div className="flex flex-wrap gap-1">
                      {(targeting.instagram_positions ?? []).map((p) => (
                        <Chip key={p} label={PLACEMENT_LABELS[p] ?? p} />
                      ))}
                    </div>
                  )}
                </Field>
              </div>

              {/* Audience network / messenger positions */}
              {editing ? (
                <div className="grid grid-cols-2 gap-3">
                  <Field label="🌐 Audience Network">
                    <CheckboxGroup
                      options={AUDIENCE_NETWORK_POSITIONS}
                      selected={draft.audience_network_positions}
                      onChange={(v) => setDraft({ ...draft, audience_network_positions: v })}
                    />
                  </Field>
                  <Field label="💬 Messenger">
                    <CheckboxGroup
                      options={MESSENGER_POSITIONS}
                      selected={draft.messenger_positions}
                      onChange={(v) => setDraft({ ...draft, messenger_positions: v })}
                    />
                  </Field>
                </div>
              ) : (
                <>
                  {targeting.audience_network_positions &&
                    targeting.audience_network_positions.length > 0 && (
                      <Field label="🌐 Audience Network">
                        <div className="flex flex-wrap gap-1">
                          {targeting.audience_network_positions.map((p) => (
                            <Chip key={p} label={p} />
                          ))}
                        </div>
                      </Field>
                    )}
                  {targeting.messenger_positions &&
                    targeting.messenger_positions.length > 0 && (
                      <Field label="💬 Messenger">
                        <div className="flex flex-wrap gap-1">
                          {targeting.messenger_positions.map((p) => (
                            <Chip key={p} label={p} />
                          ))}
                        </div>
                      </Field>
                    )}
                </>
              )}

              {/* Dispositivos */}
              <Field label="Dispositivos">
                {editing ? (
                  <CheckboxGroup
                    options={DEVICE_OPTIONS}
                    selected={draft.device_platforms}
                    onChange={(v) => setDraft({ ...draft, device_platforms: v })}
                  />
                ) : (
                  <div className="flex gap-2 flex-wrap">
                    {(targeting.device_platforms ?? []).map((d) => (
                      <Chip key={d} label={d === "mobile" ? "📱 Móvil" : d === "desktop" ? "🖥 Desktop" : d} />
                    ))}
                  </div>
                )}
              </Field>

              {!editing &&
                (targeting.user_device && targeting.user_device.length > 0 ? (
                  <Field label="Modelos">
                    <div className="flex flex-wrap gap-1">
                      {targeting.user_device.map((d) => (
                        <Chip key={d} label={d} />
                      ))}
                    </div>
                  </Field>
                ) : (
                  emptyHint("Modelos")
                ))}
              {!editing &&
                (targeting.user_os && targeting.user_os.length > 0 ? (
                  <Field label="Sistemas operativos">
                    <div className="flex flex-wrap gap-1">
                      {targeting.user_os.map((d) => (
                        <Chip key={d} label={d} />
                      ))}
                    </div>
                  </Field>
                ) : (
                  emptyHint("Sistemas operativos")
                ))}

              {/* Intereses */}
              {editing ? (
                <Field
                  label="Intereses"
                  info="Aficiones y temas que le interesan a la audiencia (ej: 'Marketing digital'). Cada interés tiene un ID numérico de Meta; añade el ID y un nombre para identificarlo."
                >
                  <IdNameEditor
                    items={draft.interests}
                    onChange={(v) => setDraft({ ...draft, interests: v })}
                  />
                </Field>
              ) : (
                ads?.interests_mapped &&
                ads.interests_mapped.length > 0 && (
                  <Field label={`Intereses (${ads.interests_mapped.length})`}>
                    <div className="flex flex-wrap gap-1.5">
                      {ads.interests_mapped.map((interest, i) => (
                        <div
                          key={i}
                          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border ${interest.relevance === "alta"
                            ? "bg-violet-50 text-violet-700 border-violet-200"
                            : "bg-gray-50 text-gray-500 border-gray-200"
                            }`}
                        >
                          <span>{interest.name}</span>
                          {interest.relevance === "alta" && <span className="text-violet-400">★</span>}
                          <span className="font-mono text-gray-300 text-[10px]">{interest.id}</span>
                        </div>
                      ))}
                    </div>
                  </Field>
                )
              )}

              {/* Behaviors / Demographics / Work positions */}
              {editing ? (
                <>
                  <Field
                    label="Comportamientos"
                    info="Segmentos por actividad: compras recientes, uso de dispositivo, viajeros frecuentes… Identificados por ID de Meta."
                  >
                    <IdNameEditor
                      items={draft.behaviors}
                      onChange={(v) => setDraft({ ...draft, behaviors: v })}
                    />
                  </Field>
                  <Field
                    label="Demografía"
                    info="Segmentos por situación: nivel educativo, estado civil, situación laboral, etc. Identificados por ID de Meta."
                  >
                    <IdNameEditor
                      items={draft.demographics}
                      onChange={(v) => setDraft({ ...draft, demographics: v })}
                    />
                  </Field>
                  <Field
                    label="Cargos / Puestos"
                    info="Puestos de trabajo declarados por los usuarios (ej: 'Director de Marketing'). Útil para B2B. Por ID de Meta."
                  >
                    <IdNameEditor
                      items={draft.work_positions}
                      onChange={(v) => setDraft({ ...draft, work_positions: v })}
                    />
                  </Field>
                </>
              ) : (
                <>
                  {targeting.flexible_spec?.[0]?.behaviors && (
                    <Field label="Comportamientos">
                      <div className="flex flex-wrap gap-1">
                        {targeting.flexible_spec[0].behaviors.map((b, i) => (
                          <Chip key={i} label={b.name ?? b.id} />
                        ))}
                      </div>
                    </Field>
                  )}
                  {targeting.flexible_spec?.[0]?.demographics && (
                    <Field label="Demografía">
                      <div className="flex flex-wrap gap-1">
                        {targeting.flexible_spec[0].demographics.map((d, i) => (
                          <Chip key={i} label={d.name ?? d.id} />
                        ))}
                      </div>
                    </Field>
                  )}
                  {targeting.flexible_spec?.[0]?.work_positions && (
                    <Field label="Cargos / Puestos">
                      <div className="flex flex-wrap gap-1">
                        {targeting.flexible_spec[0].work_positions.map((w, i) => (
                          <Chip key={i} label={w.name ?? w.id} />
                        ))}
                      </div>
                    </Field>
                  )}
                </>
              )}

              {/* Custom audiences */}
              {editing ? (
                <>
                  <Field
                    label="Audiencias personalizadas"
                    info="Listas tuyas ya creadas en Meta: visitantes web (píxel), lista de clientes, interacción, lookalikes… Se añaden por su ID."
                  >
                    <IdNameEditor
                      items={draft.custom_audiences}
                      onChange={(v) => setDraft({ ...draft, custom_audiences: v })}
                    />
                  </Field>
                  <Field
                    label="Excluir audiencias"
                    info="Audiencias personalizadas que NO verán el anuncio (ej: excluir clientes actuales para captar solo nuevos)."
                  >
                    <IdNameEditor
                      items={draft.excluded_custom_audiences}
                      onChange={(v) => setDraft({ ...draft, excluded_custom_audiences: v })}
                      exclude
                    />
                  </Field>
                </>
              ) : (
                <>
                  {targeting.custom_audiences && targeting.custom_audiences.length > 0 && (
                    <Field label="Audiencias personalizadas">
                      <div className="flex flex-wrap gap-1">
                        {targeting.custom_audiences.map((a, i) => (
                          <Chip key={i} label={a.name ?? a.id} />
                        ))}
                      </div>
                    </Field>
                  )}
                  {targeting.exclusions?.custom_audiences && (
                    <Field label="Excluir audiencias">
                      <div className="flex flex-wrap gap-1">
                        {targeting.exclusions.custom_audiences.map((a, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 text-xs rounded-full bg-red-50 text-red-600 border border-red-200"
                          >
                            ❌ {a.name ?? a.id}
                          </span>
                        ))}
                      </div>
                    </Field>
                  )}
                </>
              )}

              {/* Interest keywords usados */}
              {!editing && ads?.interest_keywords && ads.interest_keywords.length > 0 ? (
                <Field label="Keywords de búsqueda Internet">
                  <div className="flex flex-wrap gap-1">
                    {ads.interest_keywords.map((kw, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 text-[10px] font-mono rounded bg-amber-50 text-amber-700 border border-amber-200"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                </Field>
              ) : !editing ? (
                emptyHint("Keywords de búsqueda Internet")
              ) : null}
            </SectionBlock>
          )}

          {/* ANUNCIOS A/B — al final de columna derecha */}
          {cj?.ads && cj.ads.length > 0 && (
            <SectionBlock title="🎨 Anuncios — Split Test A/B">
              <div className="space-y-4">
                {cj.ads.map((ad, i) => {
                  const ld = ad.creative?.object_story_spec?.link_data;
                  const isA = i === 0;
                  const draftAd = draft.ads[i];
                  return (
                    <div
                      key={i}
                      className={`rounded-xl border-2 overflow-hidden ${isA ? "border-violet-200" : "border-sky-200"
                        }`}
                    >
                      {ld?.image_url && (
                        <img src={ld.image_url} alt={`Variante ${ad.variant}`} className="w-full h-40 object-cover" />
                      )}

                      <div className="p-3 space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span
                              className={`w-6 h-6 rounded-full ${isA ? "bg-violet-600" : "bg-sky-500"
                                } text-white text-xs font-bold flex items-center justify-center`}
                            >
                              {ad.variant}
                            </span>
                            <span className="text-sm font-semibold text-gray-800">{ad.name}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span
                              className={`text-xs px-2 py-0.5 rounded-full font-medium ${ad.copy_score >= 8
                                ? "bg-green-100 text-green-700"
                                : ad.copy_score >= 6
                                  ? "bg-yellow-100 text-yellow-700"
                                  : "bg-gray-100 text-gray-500"
                                }`}
                            >
                              {ad.copy_score}/10
                            </span>
                            <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">
                              {ad.copy_angle}
                            </span>
                          </div>
                        </div>

                        {editing && draftAd && draftAd.is_dco ? (
                          <div className="text-xs bg-amber-50 border border-amber-200 rounded-lg p-2.5 text-amber-700 leading-relaxed">
                            ⚡ Creativo dinámico (DCO): Meta combina automáticamente varios
                            titulares, textos e imágenes para hallar la mejor mezcla. Las variantes
                            se ajustan regenerando el copy, no campo a campo.
                          </div>
                        ) : editing && draftAd ? (
                          <div className="space-y-2">
                            <Field label="Titular (name)">
                              <input
                                value={draftAd.headline}
                                onChange={(e) => {
                                  const next = [...draft.ads];
                                  next[i] = { ...draftAd, headline: e.target.value };
                                  setDraft({ ...draft, ads: next });
                                }}
                                className="w-full px-2.5 py-1.5 text-sm border border-gray-200 rounded-lg"
                              />
                            </Field>
                            <Field label="Descripción">
                              <input
                                value={draftAd.description}
                                onChange={(e) => {
                                  const next = [...draft.ads];
                                  next[i] = { ...draftAd, description: e.target.value };
                                  setDraft({ ...draft, ads: next });
                                }}
                                className="w-full px-2.5 py-1.5 text-sm border border-gray-200 rounded-lg"
                              />
                            </Field>
                            <Field label="Texto principal (message)">
                              <textarea
                                value={draftAd.message}
                                onChange={(e) => {
                                  const next = [...draft.ads];
                                  next[i] = { ...draftAd, message: e.target.value };
                                  setDraft({ ...draft, ads: next });
                                }}
                                rows={3}
                                className="w-full px-2.5 py-1.5 text-sm border border-gray-200 rounded-lg resize-y"
                              />
                            </Field>
                            <Field label="CTA">
                              <select
                                value={draftAd.cta}
                                onChange={(e) => {
                                  const next = [...draft.ads];
                                  next[i] = { ...draftAd, cta: e.target.value };
                                  setDraft({ ...draft, ads: next });
                                }}
                                className="px-2.5 py-1.5 text-sm border border-gray-200 rounded-lg bg-white"
                              >
                                {CTA_OPTIONS.map((cta) => (
                                  <option key={cta} value={cta}>
                                    {cta.replace(/_/g, " ")}
                                  </option>
                                ))}
                              </select>
                            </Field>
                            <Field label="Link de destino">
                              <input
                                value={draftAd.link}
                                onChange={(e) => {
                                  const next = [...draft.ads];
                                  next[i] = { ...draftAd, link: e.target.value };
                                  setDraft({ ...draft, ads: next });
                                }}
                                className="w-full px-2.5 py-1.5 text-xs font-mono border border-gray-200 rounded-lg"
                              />
                            </Field>
                            <Field label="Caption (URL visible)">
                              <input
                                value={draftAd.caption}
                                onChange={(e) => {
                                  const next = [...draft.ads];
                                  next[i] = { ...draftAd, caption: e.target.value };
                                  setDraft({ ...draft, ads: next });
                                }}
                                className="w-full px-2.5 py-1.5 text-xs font-mono border border-gray-200 rounded-lg"
                              />
                            </Field>
                            <div className="grid grid-cols-2 gap-2">
                              <Field
                                label="Conversion domain"
                                info="Dominio donde ocurre la conversión (ej: tudominio.com). Meta lo exige para atribuir conversiones con las reglas de privacidad de iOS."
                              >
                                <input
                                  value={draftAd.conversion_domain}
                                  onChange={(e) => {
                                    const next = [...draft.ads];
                                    next[i] = { ...draftAd, conversion_domain: e.target.value };
                                    setDraft({ ...draft, ads: next });
                                  }}
                                  className="w-full px-2.5 py-1.5 text-xs font-mono border border-gray-200 rounded-lg"
                                />
                              </Field>
                              <Field
                                label="URL tags (UTM)"
                                info="Parámetros que se añaden a la URL para rastrear el tráfico en Analytics. Ej: utm_source=facebook&utm_medium=cpc."
                              >
                                <input
                                  value={draftAd.url_tags}
                                  onChange={(e) => {
                                    const next = [...draft.ads];
                                    next[i] = { ...draftAd, url_tags: e.target.value };
                                    setDraft({ ...draft, ads: next });
                                  }}
                                  className="w-full px-2.5 py-1.5 text-xs font-mono border border-gray-200 rounded-lg"
                                />
                              </Field>
                            </div>
                          </div>
                        ) : (
                          <div className="space-y-2">
                            {ld?.name && (
                              <KeyVal label="Titular" value={ld.name} bold />
                            )}
                            {ld?.description && <KeyVal label="Descripción" value={ld.description} />}
                            {ld?.message && (
                              <div>
                                <p className="text-[10px] text-gray-400 uppercase tracking-wide">
                                  Texto principal
                                </p>
                                <p className="text-xs text-gray-700 bg-gray-50 rounded-lg p-2 leading-relaxed">
                                  {ld.message}
                                </p>
                              </div>
                            )}
                            {ld?.caption && <KeyVal label="Caption (URL visible)" value={ld.caption} mono />}
                            {ld?.link && <KeyVal label="Link" value={ld.link} mono />}
                            {ld?.image_hash && (
                              <KeyVal label="Image hash" value={ld.image_hash.slice(0, 24) + "…"} mono />
                            )}
                          </div>
                        )}

                        {/* Detalles técnicos del ad */}
                        <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gray-100 text-[11px]">
                          <KeyVal
                            label="CTA"
                            value={
                              editing && draftAd
                                ? draftAd.cta.replace(/_/g, " ")
                                : ld?.call_to_action?.type?.replace(/_/g, " ") ?? "—"
                            }
                          />
                          <KeyVal label="Page ID" value={ad.creative?.object_story_spec?.page_id ?? "—"} mono />
                          {ad.creative?.object_story_spec?.instagram_user_id && (
                            <KeyVal
                              label="IG User ID"
                              value={ad.creative.object_story_spec.instagram_user_id}
                              mono
                            />
                          )}
                          {ad.conversion_domain && (
                            <KeyVal label="Conv. domain" value={ad.conversion_domain} mono />
                          )}
                          {ad.creative?.url_tags && (
                            <div className="col-span-2">
                              <KeyVal label="URL tags (UTM)" value={ad.creative.url_tags} mono />
                            </div>
                          )}
                          {ad.creative?.name && (
                            <KeyVal label="Creative name" value={ad.creative.name} mono />
                          )}
                          {ad.priority != null && (
                            <KeyVal label="Priority" value={String(ad.priority)} />
                          )}
                        </div>

                        {/* Tracking specs */}
                        {ad.tracking_specs && ad.tracking_specs.length > 0 && (
                          <div className="text-[11px]">
                            <p className="text-[10px] text-gray-400 uppercase mb-1">Tracking specs</p>
                            <pre className="text-[10px] bg-gray-50 border border-gray-100 rounded p-2 overflow-x-auto font-mono text-gray-600">
                              {JSON.stringify(ad.tracking_specs, null, 2)}
                            </pre>
                          </div>
                        )}

                        {/* Asset feed (DCO) */}
                        {ad.creative?.asset_feed_spec && (() => {
                          const afs = ad.creative.asset_feed_spec;
                          const imgs = (afs.images || []).map((i) => i.hash || i.image_url || "").filter(Boolean);
                          return (
                            <div className="bg-amber-50 border border-amber-200 rounded-lg p-2.5 space-y-2">
                              <p className="font-semibold text-amber-800 flex items-center gap-1.5">
                                ⚡ Creativo dinámico (DCO)
                              </p>
                              {imgs.length > 0 && (
                                <div>
                                  <p className="text-[10px] text-amber-600 font-medium uppercase tracking-wide mb-1.5">
                                    Imágenes — haz clic para ampliar
                                  </p>
                                  <ImageLightbox images={imgs} title="Campaña DCO" />
                                </div>
                              )}
                              <p className="text-[11px] text-amber-700">
                                {afs.titles?.length ?? 0} titulares, {afs.bodies?.length ?? 0} textos,{" "}
                                {imgs.length} imágenes
                              </p>
                            </div>
                          );
                        })()}

                        <div className="flex items-center justify-end pt-1 border-t border-gray-100">
                          <a
                            href={ad.landing_url}
                            target="_blank"
                            rel="noreferrer"
                            className={`text-xs font-medium hover:underline ${isA ? "text-violet-600" : "text-sky-600"
                              }`}
                          >
                            Ver landing →
                          </a>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </SectionBlock>
          )}

          {/* LANDING PAGES */}
          {campaign.landings.length > 0 && (
            <SectionBlock title="📄 Landing Pages">
              <div className="grid grid-cols-2 gap-3">
                {campaign.landings.map((l, i) => {
                  const draftL = draft.landings.find((d) => d.id === l.id);
                  return (
                    <div key={l.id} className="rounded-xl border border-gray-200 overflow-hidden">
                      {l.hero_image_url ? (
                        <img
                          src={l.hero_image_url}
                          alt={`Variante ${l.variant.toUpperCase()}`}
                          className="w-full h-24 object-cover"
                        />
                      ) : (
                        <div
                          className="w-full h-24 flex items-center justify-center"
                          style={{ backgroundColor: l.primary_color + "22" }}
                        >
                          <span className="text-3xl font-black opacity-20" style={{ color: l.primary_color }}>
                            {l.variant.toUpperCase()}
                          </span>
                        </div>
                      )}
                      <div className="p-2.5 space-y-1.5">
                        {editing && draftL ? (
                          <>
                            <p className="text-[10px] text-gray-400">Headline</p>
                            <textarea
                              value={draftL.headline}
                              onChange={(e) => {
                                const next = [...draft.landings];
                                next[i] = { ...draftL, headline: e.target.value };
                                setDraft({ ...draft, landings: next });
                              }}
                              rows={2}
                              className="w-full px-2 py-1 text-xs font-semibold border border-gray-200 rounded resize-y"
                            />
                            <p className="text-[10px] text-gray-400">Subheadline</p>
                            <textarea
                              value={draftL.subheadline}
                              onChange={(e) => {
                                const next = [...draft.landings];
                                next[i] = { ...draftL, subheadline: e.target.value };
                                setDraft({ ...draft, landings: next });
                              }}
                              rows={2}
                              className="w-full px-2 py-1 text-xs border border-gray-200 rounded resize-y"
                            />
                            <p className="text-[10px] text-gray-400">CTA</p>
                            <input
                              value={draftL.cta_text}
                              onChange={(e) => {
                                const next = [...draft.landings];
                                next[i] = { ...draftL, cta_text: e.target.value };
                                setDraft({ ...draft, landings: next });
                              }}
                              className="w-full px-2 py-1 text-xs border border-gray-200 rounded"
                            />
                            <div>
                              <p className="text-[10px] text-gray-400 mb-1">Beneficios</p>
                              <BenefitsEditor
                                benefits={draftL.benefits}
                                onChange={(v) => {
                                  const next = [...draft.landings];
                                  next[i] = { ...draftL, benefits: v };
                                  setDraft({ ...draft, landings: next });
                                }}
                              />
                            </div>
                            <div>
                              <p className="text-[10px] text-gray-400 mb-1">Color</p>
                              <div className="flex flex-wrap gap-1">
                                {COLOR_PALETTES.map((p) => (
                                  <button
                                    key={p.name}
                                    type="button"
                                    title={p.name}
                                    onClick={() => {
                                      const next = [...draft.landings];
                                      next[i] = { ...draftL, primary_color: p.primary };
                                      setDraft({ ...draft, landings: next });
                                    }}
                                    className={`w-5 h-5 rounded-full border-2 ${draftL.primary_color === p.primary
                                      ? "border-gray-700"
                                      : "border-white"
                                      }`}
                                    style={{ backgroundColor: p.primary }}
                                  />
                                ))}
                              </div>
                            </div>
                          </>
                        ) : (
                          <p className="text-xs font-semibold text-gray-800 line-clamp-2">{l.headline}</p>
                        )}

                        <div className="grid grid-cols-2 gap-1">
                          <div className="bg-gray-50 rounded p-1 text-center">
                            <p className="text-xs font-bold text-gray-800">{l.views}</p>
                            <p className="text-[10px] text-gray-400">vistas</p>
                          </div>
                          <div className="bg-gray-50 rounded p-1 text-center">
                            <p className="text-xs font-bold text-gray-800">{l.conversions}</p>
                            <p className="text-[10px] text-gray-400">conv.</p>
                          </div>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="inline-flex items-center gap-1 text-[10px] text-gray-400">
                            <span
                              className="w-2.5 h-2.5 rounded-full border border-gray-300 inline-block"
                              style={{
                                backgroundColor: editing && draftL ? draftL.primary_color : l.primary_color,
                              }}
                            />
                            {l.variant.toUpperCase()}
                          </span>
                          <a
                            href={`/landing/${l.id}`}
                            target="_blank"
                            rel="noreferrer"
                            className="text-[10px] text-brand-600 hover:underline"
                          >
                            Abrir →
                          </a>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </SectionBlock>
          )}

          {/* META ENDPOINTS */}
          {!editing && ads?.meta_api_endpoints && (
            <SectionBlock title="🔌 Meta Graph API">
              {ads.requires_meta_keys && (
                <div className="flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-700 mb-2">
                  <span>⚠️</span>
                  <span>
                    Configura <strong>Meta Access Token</strong> y <strong>Ad Account ID</strong> en Ajustes.
                  </span>
                </div>
              )}
              <div className="space-y-1.5">
                {Object.entries(ads.meta_api_endpoints).map(([key, endpoint]) => (
                  <div key={key} className="flex items-center gap-2">
                    <span className="text-[10px] bg-brand-100 text-brand-700 font-mono px-1.5 py-0.5 rounded shrink-0">
                      {key.replace(/_/g, " ")}
                    </span>
                    <code className="text-[10px] font-mono text-gray-600 bg-gray-50 border border-gray-200 rounded px-2 py-1 flex-1 truncate">
                      {endpoint}
                    </code>
                  </div>
                ))}
              </div>
            </SectionBlock>
          )}

          {/* PUBLICAR */}
          {!editing && cj && (
            <div className="rounded-xl border border-gray-200 p-4 space-y-3">
              {publishResult ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-green-700 font-semibold text-sm">
                    <span>✅</span> Publicada en Meta (PAUSED)
                  </div>
                  <div className="space-y-1 text-xs text-gray-500 font-mono">
                    <p>Campaign: <span className="text-gray-800">{publishResult.campaign_id}</span></p>
                    <p>Ad Set: <span className="text-gray-800">{publishResult.ad_set_id}</span></p>
                    <p>Ads: <span className="text-gray-800">{publishResult.ad_ids.join(", ")}</span></p>
                  </div>
                  <a
                    href={publishResult.meta_ads_manager_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs font-medium text-brand-600 hover:underline"
                  >
                    Abrir en Ads Manager →
                  </a>
                </div>
              ) : campaign.meta_campaign_id ? (
                <div className="space-y-1 text-xs">
                  <p className="font-semibold text-gray-700">📡 Esta campaña ya está en Meta</p>
                  <p className="text-gray-500 font-mono">{campaign.meta_campaign_id}</p>
                </div>
              ) : (
                <>
                  {publishError && (
                    <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-xs text-red-700">
                      <span>❌</span>
                      <span>{publishError}</span>
                    </div>
                  )}
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-gray-800">Publicar en Meta Ads</p>
                      <p className="text-xs text-gray-400 mt-0.5">Se crea PAUSED. Tú activas.</p>
                    </div>
                    <button
                      onClick={handlePublish}
                      disabled={publishing}
                      className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-medium rounded-xl"
                    >
                      {publishing ? "Publicando…" : "Publicar"}
                    </button>
                  </div>
                </>
              )}
            </div>
          )}

        </div>
      </div>

      {/* RECOMENDACIONES */}
      <div className="rounded-xl border border-gray-200 p-4">
        <RecommendationCards planId={String(campaign.plan_id)} />
      </div>
    </div>
  );
}

function Field({
  label,
  info,
  children,
}: {
  label: string;
  info?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1 mb-3 last:mb-0">
      <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wide flex items-center">
        {label}
        {info && <InfoTip text={info} />}
      </p>
      <div>{children}</div>
    </div>
  );
}

const inputCls =
  "w-full px-2.5 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-brand-400";

function TextInput({
  value,
  onChange,
  placeholder,
  mono,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  mono?: boolean;
}) {
  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className={`${inputCls} ${mono ? "font-mono text-xs" : ""}`}
    />
  );
}

function NumberInput({
  value,
  onChange,
  step = 1,
  min,
  suffix,
}: {
  value: number;
  onChange: (v: number) => void;
  step?: number;
  min?: number;
  suffix?: string;
}) {
  return (
    <span className="inline-flex items-center gap-2">
      <input
        type="number"
        step={step}
        min={min}
        value={value || ""}
        onChange={(e) => onChange(e.target.value === "" ? 0 : Number(e.target.value))}
        className="w-32 px-2.5 py-1.5 text-sm border border-gray-200 rounded-lg"
      />
      {suffix && <span className="text-xs text-gray-400">{suffix}</span>}
    </span>
  );
}

function SelectInput({
  value,
  onChange,
  options,
  allowEmpty,
  emptyLabel = "— Ninguno —",
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  allowEmpty?: boolean;
  emptyLabel?: string;
}) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} className={`${inputCls} bg-white`}>
      {allowEmpty && <option value="">{emptyLabel}</option>}
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}

function Toggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${checked
        ? "bg-brand-600 text-white border-brand-600"
        : "bg-white text-gray-600 border-gray-200 hover:border-brand-300"
        }`}
    >
      <span>{checked ? "✅" : "⬜"}</span>
      {label}
    </button>
  );
}

function DateInput({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <input
      type="datetime-local"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={inputCls}
    />
  );
}

function AttributionEditor({
  specs,
  onChange,
}: {
  specs: Array<{ event_type: string; window_days: number }>;
  onChange: (next: Array<{ event_type: string; window_days: number }>) => void;
}) {
  return (
    <div className="space-y-2">
      {specs.map((s, i) => (
        <div key={i} className="flex items-center gap-2">
          <select
            value={s.event_type}
            onChange={(e) => {
              const next = [...specs];
              next[i] = { ...s, event_type: e.target.value };
              onChange(next);
            }}
            className="px-2 py-1 text-xs border border-gray-200 rounded-lg bg-white"
          >
            {ATTRIBUTION_EVENT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <select
            value={s.window_days}
            onChange={(e) => {
              const next = [...specs];
              next[i] = { ...s, window_days: Number(e.target.value) };
              onChange(next);
            }}
            className="px-2 py-1 text-xs border border-gray-200 rounded-lg bg-white"
          >
            {ATTRIBUTION_WINDOW_OPTIONS.map((d) => (
              <option key={d} value={d}>
                {d} día{d !== 1 ? "s" : ""}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => onChange(specs.filter((_, j) => j !== i))}
            className="text-red-400 hover:text-red-600 text-xs"
          >
            ✕
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={() => onChange([...specs, { event_type: "CLICK_THROUGH", window_days: 7 }])}
        className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-lg font-medium text-gray-700"
      >
        + Añadir ventana
      </button>
    </div>
  );
}

function FrequencyEditor({
  specs,
  onChange,
}: {
  specs: Array<{ event: string; interval_days: number; max_frequency: number }>;
  onChange: (next: Array<{ event: string; interval_days: number; max_frequency: number }>) => void;
}) {
  return (
    <div className="space-y-2">
      {specs.map((s, i) => (
        <div key={i} className="flex items-center gap-1.5 flex-wrap">
          <select
            value={s.event}
            onChange={(e) => {
              const next = [...specs];
              next[i] = { ...s, event: e.target.value };
              onChange(next);
            }}
            className="px-2 py-1 text-xs border border-gray-200 rounded-lg bg-white"
          >
            {FREQUENCY_EVENT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <span className="text-xs text-gray-400">máx</span>
          <input
            type="number"
            min={1}
            value={s.max_frequency || ""}
            onChange={(e) => {
              const next = [...specs];
              next[i] = { ...s, max_frequency: Number(e.target.value) };
              onChange(next);
            }}
            className="w-14 px-2 py-1 text-xs border border-gray-200 rounded-lg"
          />
          <span className="text-xs text-gray-400">cada</span>
          <input
            type="number"
            min={1}
            value={s.interval_days || ""}
            onChange={(e) => {
              const next = [...specs];
              next[i] = { ...s, interval_days: Number(e.target.value) };
              onChange(next);
            }}
            className="w-14 px-2 py-1 text-xs border border-gray-200 rounded-lg"
          />
          <span className="text-xs text-gray-400">días</span>
          <button
            type="button"
            onClick={() => onChange(specs.filter((_, j) => j !== i))}
            className="text-red-400 hover:text-red-600 text-xs"
          >
            ✕
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={() => onChange([...specs, { event: "IMPRESSIONS", interval_days: 7, max_frequency: 2 }])}
        className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-lg font-medium text-gray-700"
      >
        + Añadir regla
      </button>
    </div>
  );
}

function BenefitsEditor({
  benefits,
  onChange,
}: {
  benefits: string[];
  onChange: (next: string[]) => void;
}) {
  return (
    <div className="space-y-1.5">
      {benefits.map((b, i) => (
        <div key={i} className="flex items-center gap-1.5">
          <input
            value={b}
            onChange={(e) => {
              const next = [...benefits];
              next[i] = e.target.value;
              onChange(next);
            }}
            className="flex-1 px-2 py-1 text-xs border border-gray-200 rounded-lg"
          />
          <button
            type="button"
            onClick={() => onChange(benefits.filter((_, j) => j !== i))}
            className="text-red-400 hover:text-red-600 text-xs"
          >
            ✕
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={() => onChange([...benefits, ""])}
        className="px-2 py-1 text-[11px] bg-gray-100 hover:bg-gray-200 rounded-lg font-medium text-gray-700"
      >
        + Añadir beneficio
      </button>
    </div>
  );
}

function IdNameEditor({
  items,
  onChange,
  exclude,
}: {
  items: Array<{ id: string; name?: string }>;
  onChange: (next: Array<{ id: string; name?: string }>) => void;
  exclude?: boolean;
}) {
  const [id, setId] = useState("");
  const [name, setName] = useState("");
  function add() {
    const cleanId = id.trim();
    if (!cleanId || items.some((x) => x.id === cleanId)) return;
    onChange([...items, { id: cleanId, name: name.trim() || undefined }]);
    setId("");
    setName("");
  }
  const chipCls = exclude
    ? "bg-red-50 text-red-600 border-red-200"
    : "bg-violet-50 text-violet-700 border-violet-200";
  return (
    <div className="space-y-2">
      {items.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {items.map((x) => (
            <span
              key={x.id}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border ${chipCls}`}
            >
              {exclude && "❌ "}
              {x.name ?? x.id}
              <span className="font-mono text-[10px] opacity-50">{x.id}</span>
              <button
                type="button"
                onClick={() => onChange(items.filter((y) => y.id !== x.id))}
                className="opacity-50 hover:opacity-100"
              >
                ✕
              </button>
            </span>
          ))}
        </div>
      )}
      <div className="flex gap-1">
        <input
          value={id}
          onChange={(e) => setId(e.target.value)}
          placeholder="ID Meta"
          className="w-28 px-2 py-1 text-xs font-mono border border-gray-200 rounded-lg"
        />
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Nombre (opcional)"
          className="flex-1 px-2 py-1 text-xs border border-gray-200 rounded-lg"
        />
        <button
          type="button"
          onClick={add}
          className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-lg font-medium text-gray-700 shrink-0"
        >
          + Añadir
        </button>
      </div>
    </div>
  );
}

function AdSetEditor({
  adset,
  onChange,
  onDelete,
}: {
  adset: RawAdSet;
  onChange: (next: RawAdSet) => void;
  onDelete: () => void;
}) {
  const patch = (mut: (d: RawAdSet) => void) => {
    const next = cloneJSON(adset);
    if (!next.targeting) next.targeting = {};
    mut(next);
    onChange(next);
  };
  const t = adset.targeting ?? {};
  const flex0 = t.flexible_spec?.[0] ?? {};
  const po = adset.promoted_object ?? {};

  type FlexKey = "interests" | "behaviors" | "demographics" | "work_positions";
  const setFlex = (key: FlexKey, v: Array<{ id: string; name?: string }>) =>
    patch((d) => {
      const tg = d.targeting!;
      const fs = tg.flexible_spec && tg.flexible_spec.length ? tg.flexible_spec : [{}];
      if (v.length) fs[0] = { ...fs[0], [key]: v };
      else if (fs[0]) delete fs[0][key];
      if (fs[0] && Object.keys(fs[0]).length > 0) tg.flexible_spec = fs;
      else delete tg.flexible_spec;
    });

  return (
    <div className="rounded-xl border-2 border-violet-200 p-3 space-y-3">
      <div className="flex items-center gap-2">
        <input
          value={adset.name}
          onChange={(e) => patch((d) => { d.name = e.target.value; })}
          className="flex-1 px-2.5 py-1.5 text-sm font-semibold border border-gray-200 rounded-lg"
        />
        <button
          type="button"
          onClick={onDelete}
          className="px-2.5 py-1.5 text-xs font-medium rounded-lg bg-red-50 text-red-600 hover:bg-red-100 border border-red-200 shrink-0"
        >
          🗑 Eliminar
        </button>
      </div>

      {/* Entrega */}
      <div className="grid grid-cols-2 gap-2">
        <Field label="Optimización">
          <SelectInput
            value={adset.optimization_goal ?? "LEAD_GENERATION"}
            onChange={(v) => patch((d) => { d.optimization_goal = v; })}
            options={OPTIMIZATION_OPTIONS}
          />
        </Field>
        <Field label="Facturación">
          <SelectInput
            value={adset.billing_event ?? "IMPRESSIONS"}
            onChange={(v) => patch((d) => { d.billing_event = v; })}
            options={BILLING_OPTIONS}
          />
        </Field>
        <Field label="Estrategia de puja">
          <SelectInput
            value={adset.bid_strategy ?? "LOWEST_COST_WITHOUT_CAP"}
            onChange={(v) => patch((d) => { d.bid_strategy = v; })}
            options={BID_OPTIONS}
          />
        </Field>
        <Field label="Importe puja (€) — 0 auto">
          <NumberInput
            value={centsToEur(adset.bid_amount)}
            step={0.5}
            min={0}
            onChange={(v) => patch((d) => { if (v > 0) d.bid_amount = Math.round(v * 100); else delete d.bid_amount; })}
          />
        </Field>
        <Field label="Destino del clic">
          <SelectInput
            value={adset.destination_type ?? ""}
            onChange={(v) => patch((d) => { if (v) d.destination_type = v; else delete d.destination_type; })}
            options={DESTINATION_OPTIONS}
            allowEmpty
            emptyLabel="— Por defecto —"
          />
        </Field>
        <Field label="Ritmo (pacing)">
          <CheckboxGroup
            options={PACING_OPTIONS}
            selected={adset.pacing_type ?? []}
            onChange={(v) => patch((d) => { if (v.length) d.pacing_type = v; else delete d.pacing_type; })}
          />
        </Field>
      </div>

      {/* DSA */}
      <div className="grid grid-cols-2 gap-2">
        <Field label="DSA Beneficiario">
          <TextInput value={adset.dsa_beneficiary ?? ""} onChange={(v) => patch((d) => { d.dsa_beneficiary = v; })} />
        </Field>
        <Field label="DSA Pagador">
          <TextInput value={adset.dsa_payor ?? ""} onChange={(v) => patch((d) => { d.dsa_payor = v; })} />
        </Field>
      </div>

      {/* Pixel / eventos */}
      <div className="grid grid-cols-2 gap-2">
        <Field label="Pixel ID">
          <TextInput
            value={po.pixel_id ?? ""}
            mono
            onChange={(v) => patch((d) => {
              d.promoted_object = { ...(d.promoted_object ?? {}) };
              if (v) d.promoted_object.pixel_id = v; else delete d.promoted_object.pixel_id;
            })}
          />
        </Field>
        <Field label="Evento conversión">
          <SelectInput
            value={po.custom_event_type ?? ""}
            allowEmpty
            options={CUSTOM_EVENT_OPTIONS}
            onChange={(v) => patch((d) => {
              d.promoted_object = { ...(d.promoted_object ?? {}) };
              if (v) d.promoted_object.custom_event_type = v; else delete d.promoted_object.custom_event_type;
            })}
          />
        </Field>
      </div>

      {/* Targeting */}
      <div className="grid grid-cols-2 gap-2">
        <Field label="Edad mín">
          <NumberInput value={t.age_min ?? 18} min={13} onChange={(v) => patch((d) => { d.targeting!.age_min = v; })} />
        </Field>
        <Field label="Edad máx">
          <NumberInput value={t.age_max ?? 65} min={13} onChange={(v) => patch((d) => { d.targeting!.age_max = v; })} />
        </Field>
      </div>
      <Field label="Géneros (vacío = todos)">
        <CheckboxGroup
          options={GENDER_OPTIONS}
          selected={(t.genders ?? []).map(String)}
          onChange={(v) => patch((d) => {
            const g = v.map(Number);
            if (g.length && g.length < 2) d.targeting!.genders = g; else delete d.targeting!.genders;
          })}
        />
      </Field>
      <Field label="Países">
        <CountriesEditor
          value={t.geo_locations?.countries ?? []}
          onChange={(v) => patch((d) => { d.targeting!.geo_locations = { ...(d.targeting!.geo_locations ?? {}), countries: v }; })}
        />
      </Field>
      <Field label="Excluir países">
        <CountriesEditor
          value={t.excluded_geo_locations?.countries ?? []}
          onChange={(v) => patch((d) => { if (v.length) d.targeting!.excluded_geo_locations = { countries: v }; else delete d.targeting!.excluded_geo_locations; })}
        />
      </Field>
      <div className="grid grid-cols-2 gap-2">
        <Field label="📘 Facebook">
          <CheckboxGroup
            options={FACEBOOK_POSITIONS}
            selected={t.facebook_positions ?? []}
            onChange={(v) => patch((d) => {
              if (v.length) {
                d.targeting!.facebook_positions = v;
                d.targeting!.publisher_platforms = Array.from(new Set([...(d.targeting!.publisher_platforms ?? []), "facebook"]));
              } else delete d.targeting!.facebook_positions;
            })}
          />
        </Field>
        <Field label="📸 Instagram">
          <CheckboxGroup
            options={INSTAGRAM_POSITIONS}
            selected={t.instagram_positions ?? []}
            onChange={(v) => patch((d) => {
              if (v.length) {
                d.targeting!.instagram_positions = v;
                d.targeting!.publisher_platforms = Array.from(new Set([...(d.targeting!.publisher_platforms ?? []), "instagram"]));
              } else delete d.targeting!.instagram_positions;
            })}
          />
        </Field>
      </div>
      <Field label="Dispositivos">
        <CheckboxGroup
          options={DEVICE_OPTIONS}
          selected={t.device_platforms ?? []}
          onChange={(v) => patch((d) => { if (v.length) d.targeting!.device_platforms = v; else delete d.targeting!.device_platforms; })}
        />
      </Field>
      <Field label="Intereses">
        <IdNameEditor items={flex0.interests ?? []} onChange={(v) => setFlex("interests", v)} />
      </Field>
      <Field label="Comportamientos">
        <IdNameEditor items={flex0.behaviors ?? []} onChange={(v) => setFlex("behaviors", v)} />
      </Field>
      <Field label="Demografía">
        <IdNameEditor items={flex0.demographics ?? []} onChange={(v) => setFlex("demographics", v)} />
      </Field>
      <Field label="Cargos / Puestos">
        <IdNameEditor items={flex0.work_positions ?? []} onChange={(v) => setFlex("work_positions", v)} />
      </Field>
      <Field label="Audiencias personalizadas">
        <IdNameEditor
          items={t.custom_audiences ?? []}
          onChange={(v) => patch((d) => { if (v.length) d.targeting!.custom_audiences = v; else delete d.targeting!.custom_audiences; })}
        />
      </Field>
      <Field label="Excluir audiencias">
        <IdNameEditor
          exclude
          items={t.exclusions?.custom_audiences ?? []}
          onChange={(v) => patch((d) => { if (v.length) d.targeting!.exclusions = { custom_audiences: v }; else delete d.targeting!.exclusions; })}
        />
      </Field>

      {/* Reglas */}
      <Field label="Ventana de atribución">
        <AttributionEditor
          specs={adset.attribution_spec ?? []}
          onChange={(v) => patch((d) => { if (v.length) d.attribution_spec = v; else delete d.attribution_spec; })}
        />
      </Field>
      <Field label="Frequency cap">
        <FrequencyEditor
          specs={adset.frequency_control_specs ?? []}
          onChange={(v) => patch((d) => { if (v.length) d.frequency_control_specs = v; else delete d.frequency_control_specs; })}
        />
      </Field>

      {/* Anuncios del ad set */}
      {(adset.ads ?? []).map((ad, ai) => {
        const ld: RawAdLinkData = ad.creative?.object_story_spec?.link_data ?? {};
        const setLd = (mut: (l: RawAdLinkData) => void) =>
          patch((d) => {
            const a = d.ads![ai];
            a.creative = a.creative ?? {};
            a.creative.object_story_spec = a.creative.object_story_spec ?? {};
            a.creative.object_story_spec.link_data = a.creative.object_story_spec.link_data ?? {};
            mut(a.creative.object_story_spec.link_data);
          });
        return (
          <div key={ai} className="rounded-lg border border-gray-200 p-2.5 space-y-2">
            <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wide">Anuncio {ai + 1}</p>
            <Field label="Titular">
              <TextInput value={ld.name ?? ""} onChange={(v) => setLd((l) => { l.name = v; })} />
            </Field>
            <Field label="Descripción">
              <TextInput value={ld.description ?? ""} onChange={(v) => setLd((l) => { l.description = v; })} />
            </Field>
            <Field label="Texto principal">
              <textarea
                value={ld.message ?? ""}
                onChange={(e) => setLd((l) => { l.message = e.target.value; })}
                rows={3}
                className="w-full px-2.5 py-1.5 text-sm border border-gray-200 rounded-lg resize-y"
              />
            </Field>
            <div className="grid grid-cols-2 gap-2">
              <Field label="CTA">
                <SelectInput
                  value={ld.call_to_action?.type ?? "LEARN_MORE"}
                  options={CTA_OPTIONS.map((c) => ({ value: c, label: c.replace(/_/g, " ") }))}
                  onChange={(v) => setLd((l) => { l.call_to_action = { ...(l.call_to_action ?? {}), type: v }; })}
                />
              </Field>
              <Field label="Link">
                <TextInput mono value={ld.link ?? ""} onChange={(v) => setLd((l) => { l.link = v; })} />
              </Field>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Field label="Conversion domain">
                <TextInput
                  mono
                  value={ad.conversion_domain ?? ""}
                  onChange={(v) => patch((d) => { if (v) d.ads![ai].conversion_domain = v; else delete d.ads![ai].conversion_domain; })}
                />
              </Field>
              <Field label="URL tags">
                <TextInput
                  mono
                  value={ad.creative?.url_tags ?? ""}
                  onChange={(v) => patch((d) => {
                    const a = d.ads![ai];
                    a.creative = a.creative ?? {};
                    if (v) a.creative.url_tags = v; else delete a.creative.url_tags;
                  })}
                />
              </Field>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function KeyVal({
  label,
  value,
  mono = false,
  bold = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
  bold?: boolean;
}) {
  return (
    <div>
      <p className="text-[10px] text-gray-400 uppercase tracking-wide">{label}</p>
      <p
        className={`text-xs text-gray-700 ${mono ? "font-mono" : ""} ${bold ? "font-semibold text-gray-800" : ""
          } break-words`}
      >
        {value}
      </p>
    </div>
  );
}
