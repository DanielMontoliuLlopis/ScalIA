export interface LandingSummary {
  id: string;
  variant: string;
  headline: string;
  subheadline: string | null;
  benefits: string[];
  cta_text: string | null;
  hero_image_url: string | null;
  primary_color: string;
  views: number;
  conversions: number;
}

export interface SequenceEvent {
  id: string;
  channel: "email" | "whatsapp";
  order: number;
  subject: string | null;
  preview: string | null;
  status: "scheduled" | "sent" | "failed" | "skipped";
  scheduled_at: string | null;
  sent_at: string | null;
}

export interface ChannelStatus {
  total: number;
  sent: number;
  failed: number;
  skipped: number;
  next_order: number | null;
  next_subject: string | null;
  next_at: string | null;
}

export interface RecommendedAction {
  type: string;
  priority: "alta" | "media" | "baja";
  icon: string;
  label: string;
  reason: string;
  color: "red" | "amber" | "gray";
}

export type LeadStatus = "new" | "contacted" | "showed_up" | "closed" | "lost";

export interface Lead {
  id: string;
  email: string;
  nombre: string | null;
  empresa: string | null;
  telefono: string | null;
  num_empleados: string | null;
  score: number | null;
  segment: "hot" | "warm" | "cold" | null;
  recommended_action: RecommendedAction | null;
  action_completed_at: string | null;
  action_note: string | null;
  scoring_breakdown: Record<string, number> | null;
  extra_data: Record<string, unknown>;
  sequence_status: {
    email: ChannelStatus;
    whatsapp: ChannelStatus;
  } | null;
  sequence_events: SequenceEvent[];
  lead_status: LeadStatus;
  closed_value: number | null;
  meeting_scheduled_at: string | null;
  showed_up_at: string | null;
  closed_at: string | null;
  created_at: string;
}

export interface FunnelMetrics {
  total_leads: number;
  contacted: number;
  showed_up: number;
  closed: number;
  lost: number;
  total_spent: number;
  revenue_attributed: number;
  cpl_real: number | null;
  cost_per_show_up: number | null;
  cost_per_close: number | null;
  roas: number | null;
  avg_closed_value: number | null;
}

export interface MetaStatus {
  has_meta_campaign: boolean;
  meta_status: string | null;
  is_locked: boolean;
  error: string | null;
}

export interface Campaign {
  plan_id: string;
  title: string;
  status: string;
  created_at: string;
  meta_campaign_id: string | null;
  total_views: number;
  total_conversions: number;
  total_leads: number;
  landings: LandingSummary[];
  ads_output: Record<string, unknown> | null;
  copy_output: Record<string, unknown> | null;
  email_output: Record<string, unknown> | null;
  parent_plan_id: string | null;
  is_offer_test: boolean;
  offer_test_label: string | null;
  ab_mode?: string;
}

// ── Estructura cruda de un ad set (para editar additional_ad_sets) ───────────
export interface RawTargeting {
  age_min?: number;
  age_max?: number;
  genders?: number[];
  geo_locations?: { countries?: string[]; location_types?: string[] };
  excluded_geo_locations?: { countries?: string[] };
  publisher_platforms?: string[];
  facebook_positions?: string[];
  instagram_positions?: string[];
  device_platforms?: string[];
  flexible_spec?: Array<{
    interests?: Array<{ id: string; name?: string }>;
    behaviors?: Array<{ id: string; name?: string }>;
    demographics?: Array<{ id: string; name?: string }>;
    work_positions?: Array<{ id: string; name?: string }>;
  }>;
  custom_audiences?: Array<{ id: string; name?: string }>;
  exclusions?: { custom_audiences?: Array<{ id: string; name?: string }> };
  targeting_automation?: { advantage_audience?: number };
}

export interface RawAdLinkData {
  name?: string;
  description?: string;
  message?: string;
  caption?: string;
  link?: string;
  call_to_action?: { type?: string };
}

export interface RawAd {
  name?: string;
  conversion_domain?: string;
  creative?: {
    url_tags?: string;
    object_story_spec?: { link_data?: RawAdLinkData };
  };
}

export interface RawAdSet {
  name: string;
  optimization_goal?: string;
  billing_event?: string;
  bid_strategy?: string;
  bid_amount?: number; // céntimos
  status?: string;
  destination_type?: string;
  attribution_spec?: Array<{ event_type: string; window_days: number }>;
  pacing_type?: string[];
  frequency_control_specs?: Array<{ event: string; interval_days: number; max_frequency: number }>;
  dsa_beneficiary?: string;
  dsa_payor?: string;
  promoted_object?: {
    pixel_id?: string;
    custom_event_type?: string;
    page_id?: string;
    application_id?: string;
    offsite_conversion_event_id?: string;
  };
  targeting?: RawTargeting;
  ads?: RawAd[];
}

export interface AdsOutput {
  budget_summary?: string;
  budget?: { monthly_eur: number; daily_eur: number; daily_cents: number };
  interests_mapped?: Array<{ name: string; id: string; relevance: string }>;
  meta_api_endpoints?: Record<string, string>;
  requires_meta_keys?: boolean;
  interest_keywords?: string[];
  optimization_applied?: string[];
  optimization_rationale?: string;
  account_data?: {
    audience_estimate?: {
      estimate_ready?: boolean;
      audience_lower?: number | null;
      audience_upper?: number | null;
    };
    benchmarks?: {
      cpm?: number | null;
      cpc?: number | null;
      ctr?: number | null;
      spend_90d?: number;
      cost_per_action?: Record<string, number>;
    };
  };
  campaign_json?: {
    additional_ad_sets?: RawAdSet[];
    campaign?: {
      name: string;
      objective: string;
      status: string;
      special_ad_categories: string[];
      special_ad_category_country?: string[];
      buying_type?: string;
      budget_optimization?: string;
      campaign_budget_optimization?: boolean;
      daily_budget?: number;
      lifetime_budget?: number;
      bid_strategy?: string;
      bid_cap?: number;
      spend_cap?: number;
      start_time?: string;
      stop_time?: string;
    };
    ad_set?: {
      name: string;
      optimization_goal: string;
      billing_event: string;
      bid_strategy: string;
      bid_amount?: number;
      status: string;
      daily_budget?: number;
      lifetime_budget?: number;
      start_time?: string;
      end_time?: string;
      destination_type?: string;
      pacing_type?: string[];
      is_dynamic_creative?: boolean;
      dsa_beneficiary?: string;
      dsa_payor?: string;
      use_new_app_click?: boolean;
      promoted_object?: {
        pixel_id?: string;
        custom_event_type?: string;
        page_id?: string;
        application_id?: string;
        object_store_url?: string;
        offsite_conversion_event_id?: string;
      };
      attribution_spec?: Array<{ event_type: string; window_days: number }>;
      frequency_control_specs?: Array<{ event: string; interval_days: number; max_frequency: number }>;
      targeting_automation?: { advantage_audience?: number };
      targeting?: {
        age_min: number;
        age_max: number;
        genders?: number[];
        languages?: number[];
        geo_locations?: {
          countries?: string[];
          regions?: Array<{ key: string }>;
          cities?: Array<{ key: string; radius?: number; distance_unit?: string }>;
          zips?: Array<{ key: string }>;
          location_types?: string[];
        };
        excluded_geo_locations?: { countries?: string[] };
        interests?: Array<{ id: string; name?: string }>;
        flexible_spec?: Array<{
          interests?: Array<{ id: string; name?: string }>;
          behaviors?: Array<{ id: string; name?: string }>;
          demographics?: Array<{ id: string; name?: string }>;
          work_positions?: Array<{ id: string; name?: string }>;
        }>;
        exclusions?: {
          custom_audiences?: Array<{ id: string; name?: string }>;
        };
        custom_audiences?: Array<{ id: string; name?: string }>;
        publisher_platforms?: string[];
        facebook_positions?: string[];
        instagram_positions?: string[];
        audience_network_positions?: string[];
        messenger_positions?: string[];
        device_platforms?: string[];
        user_device?: string[];
        user_os?: string[];
      };
    };
    ads?: Array<{
      variant: string;
      name: string;
      status: string;
      copy_score: number;
      copy_angle: string;
      landing_url: string;
      tracking_specs?: Array<Record<string, unknown>>;
      conversion_domain?: string;
      ad_schedule_end_time?: string;
      priority?: number;
      creative?: {
        name: string;
        url_tags?: string;
        instagram_permalink_url?: string;
        effective_object_story_id?: string;
        object_story_spec?: {
          page_id: string;
          instagram_user_id?: string;
          link_data?: {
            image_url?: string;
            image_hash?: string;
            message: string;
            link: string;
            name: string;
            description: string;
            caption?: string;
            call_to_action?: { type: string; value?: { link?: string; lead_gen_form_id?: string } };
          };
          video_data?: {
            video_id?: string;
            title?: string;
            message?: string;
            description?: string;
            image_url?: string;
            image_hash?: string;
          };
        };
        asset_feed_spec?: {
          images?: Array<{ hash?: string; image_url?: string }>;
          videos?: Array<{ video_id: string; thumbnail_hash?: string }>;
          bodies?: Array<{ text: string }>;
          titles?: Array<{ text: string }>;
          descriptions?: Array<{ text: string }>;
          link_urls?: Array<{ website_url: string; display_url?: string }>;
          call_to_action_types?: string[];
          ad_formats?: string[];
        };
      };
    }>;
  };
}

export interface CampaignUpdate {
  // Campaña
  campaign_name?: string;
  objective?: string;
  buying_type?: string;
  campaign_budget_optimization?: boolean;
  daily_budget_eur?: number;
  lifetime_budget_eur?: number;
  spend_cap_eur?: number;
  campaign_bid_strategy?: string;
  bid_cap_eur?: number;
  campaign_start_time?: string;
  campaign_stop_time?: string;
  special_ad_categories?: string[];
  special_ad_category_country?: string[];
  // Ad set
  adset_name?: string;
  optimization_goal?: string;
  billing_event?: string;
  bid_strategy?: string;
  bid_amount_eur?: number;
  adset_daily_budget_eur?: number;
  adset_lifetime_budget_eur?: number;
  adset_start_time?: string;
  adset_end_time?: string;
  destination_type?: string;
  pacing_type?: string[];
  is_dynamic_creative?: boolean;
  advantage_audience?: boolean;
  dsa_beneficiary?: string;
  dsa_payor?: string;
  // Pixel / eventos
  pixel_id?: string;
  custom_event_type?: string;
  page_id?: string;
  application_id?: string;
  offsite_conversion_event_id?: string;
  // Reglas
  attribution_spec?: Array<{ event_type: string; window_days: number }>;
  frequency_control_specs?: Array<{ event: string; interval_days: number; max_frequency: number }>;
  // Targeting
  age_min?: number;
  age_max?: number;
  genders?: number[];
  countries?: string[];
  excluded_countries?: string[];
  publisher_platforms?: string[];
  facebook_positions?: string[];
  instagram_positions?: string[];
  audience_network_positions?: string[];
  messenger_positions?: string[];
  device_platforms?: string[];
  // Segmentación detallada
  interests?: Array<{ id: string; name?: string }>;
  behaviors?: Array<{ id: string; name?: string }>;
  demographics?: Array<{ id: string; name?: string }>;
  work_positions?: Array<{ id: string; name?: string }>;
  custom_audiences?: Array<{ id: string; name?: string }>;
  excluded_custom_audiences?: Array<{ id: string; name?: string }>;
  // Creativos
  ads?: Array<{
    variant: string;
    headline?: string;
    description?: string;
    message?: string;
    caption?: string;
    link?: string;
    cta?: string;
    conversion_domain?: string;
    url_tags?: string;
  }>;
  landings?: Array<{
    id: string;
    headline?: string;
    subheadline?: string;
    benefits?: string[];
    cta_text?: string;
    primary_color?: string;
  }>;
  additional_ad_sets?: RawAdSet[];
}
