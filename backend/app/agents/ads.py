import json
import math
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

from app.agents.base import BaseAgent
from app.tools.meta_ads import (
    DEFAULT_ATTRIBUTION_SPEC,
    META_API_VERSION,
    MetaAdsError,
    get_account_benchmarks,
    get_custom_audiences,
    get_delivery_estimate,
    publish_campaign,
)

SYSTEM_PROMPT = """Eres un experto en Meta Ads con profundo conocimiento de la Meta Graph API v23.0.
Tu trabajo es generar el JSON completo y válido de una campaña Meta lista para publicar.

Estructura siempre: 1 campaign → 1 ad set → 2 ads (variante A y B para split test).
Los dos ads van dentro del mismo ad set para reparto equitativo de presupuesto.

Estado siempre PAUSED — nunca se publica sin aprobación explícita del usuario."""


# NOTA: el antiguo META_INTEREST_MAP local se eliminó (P1) — contenía IDs de Meta
# duplicados/placeholder (casi todo apuntaba al mismo ID), lo que producía un
# targeting de intereses incorrecto. Ahora los intereses se resuelven SIEMPRE
# contra la Targeting Search API real de Meta (IDs verificados). Si no hay token o
# la búsqueda no devuelve nada, la campaña va con audiencia amplia + Advantage+
# Audience (que Meta optimiza solo) y se añade un warning.

# Objetivo + optimization_goal + billing_event + CTA según funnel/goal
FUNNEL_CONFIG: dict[str, dict] = {
    "instant_form": {
        "objective": "OUTCOME_LEADS",
        "optimization_goal": "LEAD_GENERATION",
        "billing_event": "IMPRESSIONS",
        "destination_type": "ON_AD",
        "cta": "SIGN_UP",
    },
    "landing_direct_sale": {
        "objective": "OUTCOME_SALES",
        "optimization_goal": "OFFSITE_CONVERSIONS",
        "billing_event": "IMPRESSIONS",
        "destination_type": "WEBSITE",
        "custom_event_type": "PURCHASE",
        "cta": "SHOP_NOW",
    },
    "landing_lm_schedule_meeting": {
        "objective": "OUTCOME_LEADS",
        "optimization_goal": "LEAD_GENERATION",
        "billing_event": "IMPRESSIONS",
        "destination_type": "WEBSITE",
        "custom_event_type": "LEAD",
        "cta": "SIGN_UP",
    },
    "landing_lm_free_trial": {
        "objective": "OUTCOME_LEADS",
        "optimization_goal": "LEAD_GENERATION",
        "billing_event": "IMPRESSIONS",
        "destination_type": "WEBSITE",
        "custom_event_type": "START_TRIAL",
        "cta": "SIGN_UP",
    },
    "landing_lm_demo_request": {
        "objective": "OUTCOME_LEADS",
        "optimization_goal": "LEAD_GENERATION",
        "billing_event": "IMPRESSIONS",
        "destination_type": "WEBSITE",
        "custom_event_type": "LEAD",
        "cta": "GET_QUOTE",
    },
    "landing_lm_download": {
        "objective": "OUTCOME_LEADS",
        "optimization_goal": "LEAD_GENERATION",
        "billing_event": "IMPRESSIONS",
        "destination_type": "WEBSITE",
        "custom_event_type": "COMPLETE_REGISTRATION",
        "cta": "DOWNLOAD",
    },
    "landing_lm_community": {
        "objective": "OUTCOME_ENGAGEMENT",
        "optimization_goal": "LINK_CLICKS",
        "billing_event": "IMPRESSIONS",
        "destination_type": "WEBSITE",
        "cta": "LEARN_MORE",
    },
    "landing_lm_pricing_page": {
        "objective": "OUTCOME_SALES",
        "optimization_goal": "OFFSITE_CONVERSIONS",
        "billing_event": "IMPRESSIONS",
        "destination_type": "WEBSITE",
        "custom_event_type": "VIEW_CONTENT",
        "cta": "LEARN_MORE",
    },
    "landing_lm_thank_you_only": {
        "objective": "OUTCOME_AWARENESS",
        "optimization_goal": "REACH",
        "billing_event": "IMPRESSIONS",
        "destination_type": "WEBSITE",
        "cta": "LEARN_MORE",
    },
}


def _resolve_funnel_config(funnel_type: str, post_conversion_goal: str) -> dict:
    if funnel_type == "instant_form":
        return FUNNEL_CONFIG["instant_form"]
    if funnel_type == "landing_direct":
        return FUNNEL_CONFIG["landing_direct_sale"]
    # landing_lm o landing_lm_direct → depende del goal
    key = f"landing_lm_{post_conversion_goal}"
    return FUNNEL_CONFIG.get(key, FUNNEL_CONFIG["landing_lm_thank_you_only"])


# ── Optimización: enums permitidos (whitelist anti-alucinación) ──────────────
_OPT_BID_STRATEGIES = {"LOWEST_COST_WITHOUT_CAP", "LOWEST_COST_WITH_BID_CAP", "COST_CAP"}
_OPT_BID_CAP_STRATEGIES = {"LOWEST_COST_WITH_BID_CAP", "COST_CAP"}
_OPT_PACING = {"standard", "no_pacing"}
_OPT_FREQ_EVENTS = {"IMPRESSIONS", "VIDEO_VIEWS", "REACH"}
_OPT_ATTR_EVENTS = {"CLICK_THROUGH", "VIEW_THROUGH", "ENGAGED_VIDEO_VIEW"}
_OPT_ATTR_WINDOWS = {1, 7, 28}
_OPT_SPECIAL_CATS = {
    "EMPLOYMENT", "HOUSING", "CREDIT",
    "ISSUES_ELECTIONS_POLITICS", "ONLINE_GAMBLING_AND_GAMING",
    "FINANCIAL_PRODUCTS_SERVICES",
}
# Categorías que Meta restringe duramente (sin género, edad 18-65, sin targeting detallado)
_OPT_RESTRICTIVE_CATS = {"EMPLOYMENT", "HOUSING", "CREDIT"}

# Objetivos donde el frequency cap AYUDA (awareness/reach); en leads/ventas perjudica.
_FREQ_CAP_FRIENDLY_GOALS = {"REACH", "IMPRESSIONS", "AD_RECALL_LIFT", "THRUPLAY"}


OPTIMIZER_PROMPT = """Eres un estratega senior de Meta Ads (Graph API v23.0).
Recibes el contexto de UNA campaña y devuelves SOLO los parámetros técnicos ÓPTIMOS de \
targeting y entrega (no escribes copy ni eliges intereses — eso ya está resuelto).

Devuelve EXCLUSIVAMENTE un objeto JSON. Omite los campos que no apliquen. Usa solo los \
valores permitidos:

{
  "age_min": entero 13-65,
  "age_max": entero 13-65,
  "genders": [] | [1] | [2] | [1,2],
  "bid_strategy": "LOWEST_COST_WITHOUT_CAP" | "LOWEST_COST_WITH_BID_CAP" | "COST_CAP",
  "bid_amount_eur": número (coste objetivo por resultado; SOLO con estrategia con cap),
  "pacing_type": ["standard"] | ["no_pacing"],
  "frequency_control_specs": [{"event":"IMPRESSIONS","interval_days":int,"max_frequency":int}],
  "attribution_spec": [{"event_type":"CLICK_THROUGH","window_days":1|7|28},{"event_type":"VIEW_THROUGH","window_days":1|7}],
  "special_ad_categories": [],
  "is_dynamic_creative": true|false,
  "deadline_days": entero 1-90,
  "rationale": "1-2 frases con las decisiones clave"
}

Reglas de experto:
- LEAD_GENERATION / OFFSITE_CONVERSIONS: NO uses frequency cap (perjudica la fase de aprendizaje). pacing "standard". attribution 7d click + 1d view.
- REACH / IMPRESSIONS (awareness): SÍ frequency cap (p.ej. máx 2 cada 7 días). attribution 1d click.
- bid_strategy: por defecto LOWEST_COST_WITHOUT_CAP. Usa COST_CAP con bid_amount_eur realista solo si el producto es caro y el coste por resultado es crítico.
- genders: solo restringe si el producto es claramente de un género; si no, deja [].
- age: ajústalo al ICP real, no repitas el rango por defecto sin pensarlo.
- special_ad_categories: SOLO si el negocio es de empleo, vivienda, crédito, finanzas o política. Si no, [].
- deadline_days: solo si la oferta tiene urgencia con fecha; si no, omítelo.
- presupuesto bajo (<€10/día): audiencia algo más amplia para salir de la fase de aprendizaje.
- Si te doy DATOS REALES DE LA CUENTA, úsalos: con audiencia estimada pequeña (<100k) amplía edad/géneros; con audiencia enorme (>3M) y presupuesto bajo, mantén amplio (Advantage+ rinde bien). Calibra bid_amount_eur con el CPA/CPM reales, no inventes cifras."""


INTEREST_PROMPT = """Eres un experto en segmentación de Meta Ads. Tu única tarea es \
proponer términos de INTERÉS tal y como existen en la Targeting Search API de Meta \
(adinterest): nombres de temas, marcas, profesiones, aficiones o categorías — NO frases, \
NO adjetivos sueltos, NO eslóganes.

Reglas:
- Cada término es un sustantivo o nombre propio breve (1-3 palabras) que Meta reconocería \
como interés real (ej: "Marketing digital", "Yoga", "Shopify", "Emprendimiento", "Nutrición").
- Piensa en qué temas, marcas de la competencia, publicaciones, software o aficiones seguiría \
el cliente ideal en Facebook/Instagram.
- NADA de frases de dolor ("no tengo tiempo"), ni descripciones ("hombres de 30 años").
- Devuelve los términos en el idioma del negocio.

Devuelve EXCLUSIVAMENTE un objeto JSON: {"interests": ["term1", "term2", ...]} con 8-12 términos."""


class AdsAgent(BaseAgent):
    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("model", "gpt-4o-mini")
        super().__init__(**kwargs)
        self.system_prompt = SYSTEM_PROMPT

    # ------------------------------------------------------------------
    # Presupuesto
    # ------------------------------------------------------------------

    def _extract_budget(self, step: dict) -> dict:
        monthly = 200.0

        if step.get("monthly_budget") is not None:
            monthly = float(step["monthly_budget"])
        else:
            budget_str = step.get("budget", "") or step.get("description", "")
            match = re.search(r"(\d+(?:\.\d+)?)\s*(?:€|eur|euros?)", budget_str, re.IGNORECASE)
            if match:
                monthly = float(match.group(1))

        daily = round(monthly / 30, 2)
        daily_cents = math.ceil(daily * 100)
        # Mínimo Meta: 100 céntimos (1€/día)
        daily_cents = max(daily_cents, 100)

        return {
            "monthly_eur": monthly,
            "daily_eur": daily,
            "daily_cents": daily_cents,
            "summary": f"€{monthly}/mes ÷ 30 días = €{daily:.2f}/día ({daily_cents} céntimos)",
        }

    # ------------------------------------------------------------------
    # Intereses
    # ------------------------------------------------------------------

    async def _search_meta_interest(self, keyword: str, access_token: str) -> dict | None:
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                r = await client.get(
                    f"https://graph.facebook.com/{META_API_VERSION}/search",
                    params={
                        "type": "adinterest",
                        "q": keyword,
                        "locale": "es_ES",
                        "access_token": access_token,
                        "limit": 3,
                    },
                )
                items = r.json().get("data", [])
                if items:
                    top = items[0]
                    return {"id": str(top["id"]), "name": top["name"]}
        except Exception:
            pass
        return None

    def _extract_interest_keywords(self, research: dict) -> list[str]:
        """Extrae keywords concisos del research aptos para buscar en Meta Ads."""
        keywords: list[str] = []

        # ICP: demográficos y psicográficos tienen términos más relevantes que pain_points
        icp = research.get("icp", {})
        for field in ("demographics", "psychographics", "interests"):
            text = icp.get(field, "")
            if text:
                # Extraer palabras clave de 2-4 palabras del texto libre
                words = [w.strip(".,;()") for w in text.split() if len(w) > 4]
                keywords.extend(words[:4])

        # audience_language: expresiones que usa la audiencia — muy útiles para intereses
        for expr in research.get("audience_language", [])[:5]:
            if expr and len(expr) < 40:
                keywords.append(expr)

        # copy_angles: los hook_examples contienen términos del nicho
        for angle in research.get("copy_angles", [])[:4]:
            hook = angle.get("hook_example", "")
            if hook and len(hook) < 50:
                keywords.append(hook[:40])

        # business_description si existe
        biz = research.get("business_description", "") or research.get("business_type", "")
        if biz:
            keywords.insert(0, biz[:40])

        # Eliminar duplicados manteniendo orden
        seen: set[str] = set()
        unique: list[str] = []
        for k in keywords:
            k = k.strip()
            if k and k.lower() not in seen:
                seen.add(k.lower())
                unique.append(k)

        return unique[:12]

    async def _generate_interest_keywords(self, step: dict, research: dict) -> list[str]:
        """Genera términos tipo-interés (nombres de temas/marcas/aficiones) con el LLM,
        aptos para la Targeting Search API de Meta. El extractor determinista anterior
        producía adjetivos sueltos y frases largas que Meta no reconoce como intereses,
        por lo que la búsqueda volvía vacía y el ad set quedaba sin segmentación.
        """
        icp = research.get("icp", {}) if isinstance(research.get("icp"), dict) else {}
        competitors = [
            c.get("name", "") for c in research.get("competitors", []) if isinstance(c, dict)
        ]
        context_lines = [
            f"Tipo de negocio: {step.get('business_type', 'n/d')}",
            f"Descripción: {(step.get('business_description') or '')[:300]}",
            f"Producto/transformación: {(step.get('transformacion') or '')[:150]}",
            f"ICP psicográfico: {str(icp.get('psychographics', ''))[:300]}",
            f"Comportamientos ICP: {icp.get('behaviors', [])}",
            f"Competidores: {[c for c in competitors if c][:6]}",
            f"Insight clave: {str(research.get('key_insight', ''))[:200]}",
        ]
        try:
            resp = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=400,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": INTEREST_PROMPT},
                    {"role": "user", "content": "Negocio:\n" + "\n".join(context_lines)},
                ],
            )
            data = json.loads(resp.choices[0].message.content or "{}")
        except Exception:
            return []

        out: list[str] = []
        seen: set[str] = set()
        for term in data.get("interests", []):
            if not isinstance(term, str):
                continue
            term = term.strip()
            if term and 2 <= len(term) <= 40 and term.lower() not in seen:
                seen.add(term.lower())
                out.append(term)
        return out[:12]

    async def _map_interests(self, keywords: list[str], access_token: str | None) -> list[dict]:
        """Resuelve intereses SOLO contra la Targeting Search API real de Meta (IDs
        verificados). Sin token o sin resultados → [] (audiencia amplia + Advantage+).

        Ya no hay fallback a un mapa local: producía IDs incorrectos. La búsqueda
        definitiva se repite además en publish_campaign con el token de publicación.
        """
        if not access_token:
            return []

        seen_ids: set[str] = set()
        interests: list[dict] = []

        for kw in keywords:
            result = await self._search_meta_interest(kw, access_token)
            if result and result["id"] not in seen_ids:
                seen_ids.add(result["id"])
                interests.append(result)
            if len(interests) >= 8:
                break

        return interests[:10]

    # ------------------------------------------------------------------
    # Builder principal
    # ------------------------------------------------------------------

    @staticmethod
    def _build_names(step: dict, funnel_type: str, post_conversion_goal: str) -> dict[str, str]:
        """Genera nombres legibles para campaign, ad set y ads."""
        company: str = (
            step.get("company_name")
            or step.get("business_description", "")[:35]
            or "Mi Negocio"
        ).strip()

        funnel_labels = {
            "instant_form": "Formulario instantáneo",
            "landing_direct": "Venta directa",
            "landing_lm": "Lead magnet",
            "landing_lm_direct": "Lead magnet + Venta",
        }
        goal_labels = {
            "schedule_meeting": "Llamada",
            "free_trial": "Trial gratis",
            "demo_request": "Demo",
            "download": "Descarga",
            "thank_you_only": "Validación",
            "community": "Comunidad",
            "pricing_page": "Pricing",
        }

        funnel_label = funnel_labels.get(funnel_type, funnel_type.replace("_", " ").title())
        goal_label = goal_labels.get(post_conversion_goal, post_conversion_goal.replace("_", " ").title())
        month_label = date.today().strftime("%b %Y")

        campaign_name = f"{company} — {funnel_label} · {goal_label} — {month_label}"
        ad_set_name = f"{company} — Audiencia principal"
        ad_name_a = f"{company} — {funnel_label} A"
        ad_name_b = f"{company} — {funnel_label} B"

        return {
            "campaign": campaign_name,
            "ad_set": ad_set_name,
            "ad_a": ad_name_a,
            "ad_b": ad_name_b,
            "short": company[:40],
        }

    @staticmethod
    def _build_dco_creative(
        names: dict, dco_assets: dict, page_id: str, instagram_user_id: str | None,
        url: str, cta_type: str, domain: str, utm_tags: str,
    ) -> dict:
        """Creativo con asset_feed_spec: Meta combina titulares/textos/imágenes."""
        titles = [{"text": t[:40]} for t in dco_assets.get("titles", []) if t][:5]
        bodies = [{"text": b[:500]} for b in dco_assets.get("bodies", []) if b][:5]
        descs = [{"text": d[:60]} for d in dco_assets.get("descriptions", []) if d][:5]
        # Las imágenes se resuelven a image_hash en publish (upload por URL)
        images = [{"image_url": u} for u in dco_assets.get("images", []) if u][:10]

        asset_feed: dict[str, Any] = {
            "ad_formats": ["SINGLE_IMAGE"],
            "call_to_action_types": [cta_type],
            "link_urls": [{"website_url": url, "display_url": domain}],
        }
        if images:
            asset_feed["images"] = images
        if titles:
            asset_feed["titles"] = titles
        if bodies:
            asset_feed["bodies"] = bodies
        if descs:
            asset_feed["descriptions"] = descs

        story_spec: dict[str, Any] = {"page_id": page_id}
        if instagram_user_id:
            story_spec["instagram_user_id"] = instagram_user_id

        return {
            "name": f"Creative DCO — {names['short']}",
            "object_story_spec": story_spec,
            "asset_feed_spec": asset_feed,
            "url_tags": utm_tags,
        }

    async def _build_campaign_json(
        self,
        step: dict,
        research: dict,
        copy: dict,
        landing: dict,
        budget: dict,
        interests: list[dict],
        ad_account_id: str,
        funnel_cfg: dict,
    ) -> dict:
        funnel_type: str = step.get("funnel_type", "landing_lm")
        post_conversion_goal: str = step.get("post_conversion_goal", "thank_you_only")
        ab_testing: bool = bool(step.get("ab_testing", False))

        names = self._build_names(step, funnel_type, post_conversion_goal)
        raw_name = names["short"]

        pixel_id: str = step.get("meta_pixel_id") or "{{META_PIXEL_ID}}"
        page_id: str = step.get("meta_page_id") or "{{META_PAGE_ID}}"
        instagram_user_id: str | None = step.get("instagram_user_id")
        company_name: str = step.get("company_name", "Mi Empresa")
        domain: str = step.get("domain", "miapp.com")
        lead_gen_form_id: str | None = step.get("lead_gen_form_id")

        copies = copy.get("copies", [])
        copy_a = copies[0] if copies else {}
        copy_b = copies[1] if len(copies) > 1 else copy_a

        # Offer Engine: urgencia suffix para primary_text
        urgencia: str = step.get("urgencia", "sin_urgencia") or "sin_urgencia"
        _urgencia_suffix: dict[str, str] = {
            "fecha_limite": " — Plazas limitadas, cierra pronto.",
            "plazas_limitadas": " — Solo quedan pocas plazas disponibles.",
            "bonus_temporal": " — Bonus especial por tiempo limitado.",
        }
        urgencia_text = _urgencia_suffix.get(urgencia, "")

        creative_type: str = copy.get("creative_type") or step.get("creative_type") or "image_ai"
        is_video = creative_type in {"video_upload", "reel_upload"}
        is_meta_post = creative_type == "meta_post"
        is_reel = creative_type == "reel_upload"

        # DCO (Fase 4): un único anuncio con asset_feed_spec (Meta combina titulares/
        # textos/imágenes). Solo para imagen IA sin A/B manual y fuera de instant_form.
        dco_assets: dict = copy.get("dco_assets") or {}
        want_dco = (
            not ab_testing
            and not is_video
            and not is_meta_post
            and funnel_type != "instant_form"
            and bool(dco_assets.get("titles") or dco_assets.get("images"))
            and bool(step.get("dco", True))
        )

        landing_ids = landing.get("landing_ids", {})
        base_url = step.get("frontend_url", "https://app.growthOS.io")
        url_a = f"{base_url}/landing/{landing_ids.get('a', 'LANDING_A_ID')}"
        url_b = f"{base_url}/landing/{landing_ids.get('b', 'LANDING_B_ID')}"

        variant_a = landing.get("variant_a", {})
        variant_b = landing.get("variant_b", {})

        image_hash_a = copy_a.get("image_hash", "{{IMAGE_HASH_A}}")
        image_hash_b = copy_b.get("image_hash", image_hash_a)
        image_url_a = copy_a.get("image_url", "")
        image_url_b = copy_b.get("image_url", image_url_a)
        meta_post_id_a = copy_a.get("meta_post_id")
        meta_post_id_b = copy_b.get("meta_post_id")
        thumbnail_a = copy_a.get("thumbnail_url") or image_url_a
        thumbnail_b = copy_b.get("thumbnail_url") or image_url_b

        # ── Campaign ────────────────────────────────────────────────────
        campaign: dict[str, Any] = {
            "name": names["campaign"],
            "objective": funnel_cfg["objective"],
            "status": "PAUSED",
            "special_ad_categories": [],
            "buying_type": "AUCTION",
            "campaign_budget_optimization": True,
            "daily_budget": budget["daily_cents"],
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        }

        # ── Targeting ───────────────────────────────────────────────────
        geo = research.get("target_geo", {"countries": ["ES"]})
        countries = geo if isinstance(geo, list) else geo.get("countries", ["ES"])
        age_min: int = research.get("age_min", 25)
        age_max: int = research.get("age_max", 54)

        flexible_spec: list[dict] = []
        if interests:
            flexible_spec.append({"interests": [{"id": i["id"], "name": i["name"]} for i in interests]})

        targeting: dict[str, Any] = {
            "geo_locations": {
                "countries": countries,
                "location_types": ["home", "recent"],
            },
            "age_min": age_min,
            "age_max": age_max,
            # Advantage+ Audience ON por defecto — Meta expande la audiencia para mejor rendimiento
            "targeting_automation": {"advantage_audience": 1},
        }
        if flexible_spec:
            targeting["flexible_spec"] = flexible_spec

        # ── Placements (P5) ──────────────────────────────────────────────
        # Por defecto: Advantage+ placements (omitimos publisher_platforms/positions
        # → Meta usa TODAS las ubicaciones y optimiza, suele rendir mejor).
        # Excepciones que SÍ exigen placements manuales:
        #   - Reel: el formato vertical solo encaja en Reels.
        #   - manual_placements=True: el usuario quiere control explícito.
        manual_placements = bool(step.get("manual_placements"))
        if is_reel:
            targeting["publisher_platforms"] = ["facebook", "instagram"]
            targeting["facebook_positions"] = ["facebook_reels"]
            targeting["instagram_positions"] = ["reels"]
        elif manual_placements:
            targeting["publisher_platforms"] = ["facebook", "instagram"]
            targeting["facebook_positions"] = ["feed", "story", "facebook_reels"]
            targeting["instagram_positions"] = ["stream", "story", "reels"]
            targeting["device_platforms"] = ["mobile", "desktop"]
        # else: Advantage+ placements (no fijamos ubicaciones)

        # ── promoted_object ─────────────────────────────────────────────
        promoted_object: dict | None = None
        custom_event = funnel_cfg.get("custom_event_type")
        if funnel_type != "instant_form" and custom_event:
            promoted_object = {
                "pixel_id": pixel_id,
                "custom_event_type": custom_event,
            }
        elif funnel_type == "instant_form":
            promoted_object = {"page_id": page_id}

        # ── Ad Set ──────────────────────────────────────────────────────
        ad_set: dict[str, Any] = {
            "name": names["ad_set"],
            "optimization_goal": funnel_cfg["optimization_goal"],
            "billing_event": funnel_cfg["billing_event"],
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "status": "PAUSED",
            "destination_type": funnel_cfg["destination_type"],
            "targeting": targeting,
            # Attribution recomendada Meta v23
            "attribution_spec": DEFAULT_ATTRIBUTION_SPEC,
            # DSA obligatorio UE
            "dsa_beneficiary": company_name,
            "dsa_payor": company_name,
        }
        if promoted_object:
            ad_set["promoted_object"] = promoted_object

        # ── UTM tags ────────────────────────────────────────────────────
        utm_tags = (
            f"utm_source=facebook&utm_medium=paid_social"
            f"&utm_campaign={{{{campaign.name}}}}&utm_content={{{{ad.name}}}}"
        )

        # ── Creatives ───────────────────────────────────────────────────
        cta_type = funnel_cfg["cta"]

        def _build_creative(
            variant: str,
            cp: dict,
            lp: dict,
            url: str,
            img_hash: str,
            img_url: str,
            video_url: str | None,
            video_thumbnail: str | None,
            post_id: str | None,
        ) -> dict:
            headline = (lp.get("headline") or cp.get("hook", ""))[:40]
            subheadline = (lp.get("subheadline") or "")[:30]
            primary_text = (f"{cp.get('hook', '')} {cp.get('body', '')}".strip() + urgencia_text)[:500]

            # Opción 1: contenido ya publicado en Meta → object_story_id
            if is_meta_post and post_id:
                return {
                    "name": f"Creative {variant} — {names['short']}",
                    "object_story_id": post_id,
                    "url_tags": utm_tags if funnel_type != "instant_form" else None,
                }

            story_spec: dict[str, Any] = {"page_id": page_id}
            if instagram_user_id:
                story_spec["instagram_user_id"] = instagram_user_id

            cta_value_lead: dict[str, Any] = {}
            if funnel_type == "instant_form":
                cta_value_lead["lead_gen_form_id"] = lead_gen_form_id or "{{LEAD_GEN_FORM_ID}}"

            # Opción 2: video (incluye Reels) → video_data
            if is_video and video_url:
                video_data: dict[str, Any] = {
                    "video_id": "{{VIDEO_ID}}",  # Meta exige subirlo a /act_/advideos primero
                    "video_url_for_upload": video_url,
                    "title": headline,
                    "message": primary_text,
                    "image_url": video_thumbnail,
                    "call_to_action": {
                        "type": cta_type,
                        "value": cta_value_lead if funnel_type == "instant_form" else {"link": url},
                    },
                }
                if funnel_type != "instant_form":
                    video_data["link_description"] = subheadline
                story_spec["video_data"] = {k: v for k, v in video_data.items() if v is not None}
                return {
                    "name": f"Creative {variant} — {names['short']}",
                    "object_story_spec": story_spec,
                    "url_tags": utm_tags if funnel_type != "instant_form" else None,
                }

            # Opción 3: imagen (subida o IA) → link_data
            link_data: dict[str, Any]
            if funnel_type == "instant_form":
                link_data = {
                    "message": primary_text,
                    "name": headline,
                    "description": subheadline,
                    "image_hash": img_hash,
                    "image_url": img_url or None,
                    "call_to_action": {"type": cta_type, "value": cta_value_lead},
                }
            else:
                link_data = {
                    "message": primary_text,
                    "link": url,
                    "name": headline,
                    "description": subheadline,
                    "caption": domain,
                    "image_hash": img_hash,
                    "image_url": img_url or None,
                    "call_to_action": {"type": cta_type, "value": {"link": url}},
                }

            story_spec["link_data"] = {k: v for k, v in link_data.items() if v is not None}

            return {
                "name": f"Creative {variant} — {names['short']}",
                "object_story_spec": story_spec,
                "url_tags": utm_tags if funnel_type != "instant_form" else None,
            }

        creative_a = _build_creative(
            "A", copy_a, variant_a, url_a, image_hash_a, image_url_a,
            image_url_a if is_video else None, thumbnail_a, meta_post_id_a,
        )
        creative_a = {k: v for k, v in creative_a.items() if v is not None}
        if ab_testing:
            creative_b = _build_creative(
                "B", copy_b, variant_b, url_b, image_hash_b, image_url_b,
                image_url_b if is_video else None, thumbnail_b, meta_post_id_b,
            )
            creative_b = {k: v for k, v in creative_b.items() if v is not None}

        # ── Tracking specs (solo si hay pixel real) ─────────────────────
        tracking_specs: list[dict] = []
        if funnel_type != "instant_form" and pixel_id != "{{META_PIXEL_ID}}":
            tracking_specs = [
                {
                    "action.type": ["offsite_conversion"],
                    "fb_pixel": [pixel_id],
                }
            ]

        def _build_ad(variant: str, creative: dict, url: str) -> dict:
            ad: dict[str, Any] = {
                "name": f"{raw_name} — Variante {variant}",
                "status": "PAUSED",
                "creative": creative,
            }
            if tracking_specs:
                ad["tracking_specs"] = tracking_specs
            if funnel_type != "instant_form" and domain:
                ad["conversion_domain"] = domain
            return ad

        if want_dco:
            creative_dco = self._build_dco_creative(
                names, dco_assets, page_id, instagram_user_id, url_a, cta_type, domain, utm_tags,
            )
            # DCO: un solo anuncio por ad set + flag is_dynamic_creative
            ad_set["is_dynamic_creative"] = True
            ads = [
                {
                    **_build_ad("DCO", creative_dco, url_a),
                    "name": f"{raw_name} — Anuncio dinámico (DCO)",
                    "_meta": {
                        "variant": "DCO",
                        "landing_url": url_a,
                        "copy_angle": copy_a.get("angle", ""),
                        "image_url": image_url_a,
                    },
                }
            ]
            return {
                "api_version": META_API_VERSION,
                "ad_account_id": ad_account_id,
                "creation_order": ["campaign", "ad_set", "adcreatives", "ads"],
                "campaign": campaign,
                "ad_set": ad_set,
                "ads": ads,
                "interest_keywords": self._extract_interest_keywords(research),
            }

        ads = [
            {
                **_build_ad("A", creative_a, url_a),
                "name": names["ad_a"] if ab_testing else f"{raw_name} — Anuncio",
                "_meta": {
                    "variant": "A",
                    "landing_url": url_a,
                    "copy_angle": copy_a.get("angle", ""),
                    "image_url": image_url_a,
                },
            },
        ]
        if ab_testing:
            ads.append({
                **_build_ad("B", creative_b, url_b),
                "name": names["ad_b"],
                "_meta": {
                    "variant": "B",
                    "landing_url": url_b,
                    "copy_angle": copy_b.get("angle", ""),
                    "image_url": image_url_b,
                },
            })

        return {
            "api_version": META_API_VERSION,
            "ad_account_id": ad_account_id,
            "creation_order": ["campaign", "ad_set", "adcreatives", "ads"],
            "campaign": campaign,
            "ad_set": ad_set,
            "ads": ads,
            # Keywords para buscar intereses frescos en Meta API al publicar
            "interest_keywords": self._extract_interest_keywords(research),
        }

    # ------------------------------------------------------------------
    # Validaciones pre-publicación
    # ------------------------------------------------------------------

    # Optimization goals que requieren píxel sí o sí
    _PIXEL_REQUIRED_GOALS = {"OFFSITE_CONVERSIONS", "VALUE"}

    def _validate_before_publish(self, step: dict, campaign_json: dict) -> tuple[list[str], list[str]]:
        """Devuelve (errors, warnings).

        errors: bloquean publicación (Meta API rechazaría).
        warnings: dejan publicar pero campaña funcionará peor.
        """
        errors: list[str] = []
        warnings: list[str] = []
        funnel_type = step.get("funnel_type", "landing_lm")

        # ── ad_account_id (obligatorio siempre) ────────────────────────
        ad_account = campaign_json.get("ad_account_id", "")
        if not ad_account or "XXXX" in str(ad_account):
            errors.append("Falta meta_ad_account_id en Settings del usuario.")

        # ── page_id (obligatorio siempre — creative lo exige) ──────────
        for ad in campaign_json.get("ads", []):
            story_spec = ad.get("creative", {}).get("object_story_spec", {})
            page_id = str(story_spec.get("page_id", ""))
            if page_id.startswith("{{") or not page_id:
                errors.append("Falta meta_page_id en Settings del usuario.")
                break

        # ── lead_gen_form_id (obligatorio si instant_form) ─────────────
        if funnel_type == "instant_form":
            for ad in campaign_json.get("ads", []):
                link_data = ad.get("creative", {}).get("object_story_spec", {}).get("link_data", {})
                cta = link_data.get("call_to_action", {}).get("value", {})
                form_id = str(cta.get("lead_gen_form_id", ""))
                if form_id.startswith("{{") or not form_id:
                    errors.append("Falta lead_gen_form_id — crear formulario en Meta Page primero.")
                    break

        # ── pixel_id (solo obligatorio si optimization_goal lo exige) ──
        ad_set = campaign_json.get("ad_set", {})
        opt_goal = ad_set.get("optimization_goal", "")
        promoted = ad_set.get("promoted_object", {}) or {}
        pixel = str(promoted.get("pixel_id", ""))
        pixel_missing = pixel.startswith("{{") or not pixel

        if pixel_missing and opt_goal in self._PIXEL_REQUIRED_GOALS:
            errors.append(
                f"Falta meta_pixel_id — obligatorio con optimization_goal={opt_goal}."
            )
        elif pixel_missing and funnel_type != "instant_form" and opt_goal == "LEAD_GENERATION":
            # Pixel opcional aquí pero recomendado para retargeting + tracking
            warnings.append(
                "Sin meta_pixel_id no podrás trackear conversiones ni hacer retargeting."
            )

        return errors, warnings

    # ------------------------------------------------------------------
    # Optimización del modelo con LLM (rellena lo que el builder deja simple)
    # ------------------------------------------------------------------

    @staticmethod
    def _default_attribution(opt_goal: str) -> list[dict]:
        """Ventana de atribución sensata por objetivo, sin LLM."""
        if opt_goal in ("REACH", "IMPRESSIONS"):
            return [{"event_type": "CLICK_THROUGH", "window_days": 1}]
        # Conversiones / leads → estándar Meta 7d click + 1d view
        return [
            {"event_type": "CLICK_THROUGH", "window_days": 7},
            {"event_type": "VIEW_THROUGH", "window_days": 1},
        ]

    # Conversiones/semana mínimas para salir de la fase de aprendizaje de Meta
    _LEARNING_WEEKLY_EVENTS = 50
    # CPA asumido por optimization_goal (€) — heurístico conservador para el aviso
    _ASSUMED_CPA: dict[str, float] = {
        "OFFSITE_CONVERSIONS": 25.0,
        "VALUE": 30.0,
        "LEAD_GENERATION": 8.0,
        "QUALITY_LEAD": 12.0,
        "LANDING_PAGE_VIEWS": 1.2,
        "LINK_CLICKS": 0.5,
    }

    def _budget_learning_check(
        self, budget: dict, funnel_cfg: dict, account_data: dict | None = None
    ) -> list[str]:
        """Avisa si el presupuesto es demasiado bajo para que el ad set salga de la
        fase de aprendizaje con el optimization_goal elegido (P6).

        Usa el CPA REAL de la cuenta si está disponible; si no, un heurístico."""
        opt_goal = funnel_cfg["optimization_goal"]
        heuristic = self._ASSUMED_CPA.get(opt_goal)
        if heuristic is None:
            return []  # awareness/reach no dependen de conversiones para aprender

        real = self._real_cpa(funnel_cfg, account_data)
        cpa = real or heuristic
        source = "real de tu cuenta" if real else "estimado"

        weekly_budget = budget["daily_eur"] * 7
        expected = weekly_budget / cpa
        if expected >= self._LEARNING_WEEKLY_EVENTS:
            return []

        needed_daily = round((self._LEARNING_WEEKLY_EVENTS * cpa) / 7, 2)
        msg = (
            f"Presupuesto ajustado para optimizar a {opt_goal}: ~{expected:.0f} eventos/semana "
            f"estimados (CPA {source} €{cpa:.2f}); Meta necesita ~{self._LEARNING_WEEKLY_EVENTS} "
            f"para salir de la fase de aprendizaje. Para lograrlo harían falta ~€{needed_daily}/día."
        )
        if opt_goal in ("OFFSITE_CONVERSIONS", "VALUE", "LEAD_GENERATION", "QUALITY_LEAD"):
            msg += " Con este presupuesto, optimizar a LANDING_PAGE_VIEWS aprende más rápido."
        return [msg]

    # Action types de Meta relevantes por optimization_goal (para leer CPA real)
    _GOAL_ACTION_KEYS: dict[str, list[str]] = {
        "LEAD_GENERATION": ["lead", "onsite_conversion.lead_grouped", "leadgen.other"],
        "OFFSITE_CONVERSIONS": ["purchase", "offsite_conversion.fb_pixel_purchase", "omni_purchase"],
        "VALUE": ["purchase", "offsite_conversion.fb_pixel_purchase", "omni_purchase"],
        "LANDING_PAGE_VIEWS": ["landing_page_view"],
        "LINK_CLICKS": ["link_click"],
    }

    def _real_cpa(self, funnel_cfg: dict, account_data: dict | None) -> float | None:
        """CPA real de la cuenta para el objetivo, si existe en los benchmarks."""
        bm = (account_data or {}).get("benchmarks", {}) or {}
        cpa_map = bm.get("cost_per_action", {}) or {}
        if not cpa_map:
            return None
        goal = funnel_cfg["optimization_goal"]
        for key in self._GOAL_ACTION_KEYS.get(goal, []):
            if cpa_map.get(key, 0) > 0:
                return cpa_map[key]
        # Búsqueda difusa por token
        token = (
            "lead" if goal == "LEAD_GENERATION"
            else "purchase" if goal in ("OFFSITE_CONVERSIONS", "VALUE")
            else None
        )
        if token:
            for k, v in cpa_map.items():
                if token in k and v > 0:
                    return v
        return None

    def _account_data_prompt_lines(self, account_data: dict | None) -> list[str]:
        """Convierte los datos de cuenta en líneas legibles para el prompt del LLM."""
        if not account_data:
            return []
        lines: list[str] = []
        est = account_data.get("audience_estimate", {}) or {}
        lo, hi = est.get("audience_lower"), est.get("audience_upper")
        if lo is not None:
            size = f"{lo:,}" + (f"–{hi:,}" if hi else "") + " personas"
            lines.append(f"- Tamaño de audiencia estimado: {size}")
        bm = account_data.get("benchmarks", {}) or {}
        if bm.get("cpm"):
            lines.append(f"- CPM medio de la cuenta (90d): €{bm['cpm']:.2f}")
        if bm.get("cpc"):
            lines.append(f"- CPC medio de la cuenta (90d): €{bm['cpc']:.2f}")
        if bm.get("ctr"):
            lines.append(f"- CTR medio de la cuenta (90d): {bm['ctr']:.2f}%")
        cpa_map = bm.get("cost_per_action", {}) or {}
        if cpa_map:
            top = sorted(cpa_map.items(), key=lambda x: x[1])[:4]
            lines.append("- Coste por acción histórico: " + ", ".join(f"{k}=€{v:.2f}" for k, v in top))
        return lines

    async def _optimize_campaign(
        self, step: dict, research: dict, funnel_cfg: dict, budget: dict,
        account_data: dict | None = None,
    ) -> dict:
        """Pide al LLM los parámetros técnicos óptimos. Devuelve dict ya VALIDADO
        (solo claves/valores permitidos). Si algo falla, devuelve {} y se usan
        los defaults deterministas."""
        icp = research.get("icp", {}) if isinstance(research.get("icp"), dict) else {}
        geo = research.get("target_geo", {"countries": ["ES"]})
        countries = geo if isinstance(geo, list) else geo.get("countries", ["ES"])

        context_lines = [
            f"Tipo de negocio: {step.get('business_type', 'n/d')}",
            f"Descripción: {step.get('business_description', '')[:200]}",
            f"Funnel: {step.get('funnel_type', 'landing_lm')}",
            f"Objetivo de conversión: {step.get('post_conversion_goal', 'thank_you_only')}",
            f"Objetivo Meta: {funnel_cfg['objective']}",
            f"Optimization goal: {funnel_cfg['optimization_goal']}",
            f"Presupuesto: €{budget['monthly_eur']}/mes (€{budget['daily_eur']}/día)",
            f"Urgencia oferta: {step.get('urgencia', 'sin_urgencia')}",
            f"Precio producto: {step.get('precio_base', 'n/d')}",
            f"Transformación: {step.get('transformacion', '')[:120]}",
            f"Garantía: {step.get('garantia', 'n/d')}",
            f"ICP demográfico: {str(icp.get('demographics', ''))[:200]}",
            f"ICP psicográfico: {str(icp.get('psychographics', ''))[:200]}",
            f"Países: {countries}",
            f"Edad sugerida actual: {research.get('age_min', 25)}-{research.get('age_max', 54)}",
        ]

        # Datos reales de la cuenta Meta (si hay token e historial) — decisiones con datos
        data_lines = self._account_data_prompt_lines(account_data)
        if data_lines:
            context_lines.append("\nDATOS REALES DE LA CUENTA META (úsalos para decidir):")
            context_lines.extend(data_lines)

        user_prompt = "Contexto de la campaña:\n" + "\n".join(context_lines)

        try:
            resp = await self.client.chat.completions.create(
                model="gpt-4o",
                max_tokens=1024,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": OPTIMIZER_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
            raw = json.loads(resp.choices[0].message.content or "{}")
        except Exception:
            return {}

        return self._sanitize_optimization(raw, funnel_cfg)

    def _sanitize_optimization(self, raw: dict, funnel_cfg: dict) -> dict:
        """Filtra la respuesta del LLM dejando solo valores válidos."""
        out: dict[str, Any] = {}
        if not isinstance(raw, dict):
            return out

        def _clamp_age(v: Any) -> int | None:
            try:
                return max(13, min(65, int(v)))
            except (TypeError, ValueError):
                return None

        amin = _clamp_age(raw.get("age_min"))
        amax = _clamp_age(raw.get("age_max"))
        if amin is not None and amax is not None and amin <= amax:
            out["age_min"], out["age_max"] = amin, amax

        genders = raw.get("genders")
        if isinstance(genders, list):
            g = [x for x in genders if x in (1, 2)]
            # [] y [1,2] significan "todos" → no fijamos genders (mejor alcance)
            if g and set(g) != {1, 2}:
                out["genders"] = g

        bid = raw.get("bid_strategy")
        if bid in _OPT_BID_STRATEGIES:
            out["bid_strategy"] = bid
            if bid in _OPT_BID_CAP_STRATEGIES:
                try:
                    amount = float(raw.get("bid_amount_eur"))
                    if amount > 0:
                        out["bid_amount"] = int(round(amount * 100))
                except (TypeError, ValueError):
                    pass

        pacing = raw.get("pacing_type")
        if isinstance(pacing, list):
            p = [x for x in pacing if x in _OPT_PACING]
            if p:
                out["pacing_type"] = p[:1]

        freq = raw.get("frequency_control_specs")
        if isinstance(freq, list):
            clean_freq = []
            for f in freq[:3]:
                if not isinstance(f, dict):
                    continue
                event = f.get("event")
                if event not in _OPT_FREQ_EVENTS:
                    continue
                try:
                    interval = max(1, min(90, int(f.get("interval_days", 7))))
                    maxfreq = max(1, min(50, int(f.get("max_frequency", 2))))
                except (TypeError, ValueError):
                    continue
                clean_freq.append(
                    {"event": event, "interval_days": interval, "max_frequency": maxfreq}
                )
            # Solo aplicamos freq cap si el objetivo lo tolera bien
            if clean_freq and funnel_cfg["optimization_goal"] in _FREQ_CAP_FRIENDLY_GOALS:
                out["frequency_control_specs"] = clean_freq

        attr = raw.get("attribution_spec")
        if isinstance(attr, list):
            clean_attr = []
            for a in attr[:2]:
                if not isinstance(a, dict):
                    continue
                et = a.get("event_type")
                try:
                    win = int(a.get("window_days"))
                except (TypeError, ValueError):
                    continue
                if et in _OPT_ATTR_EVENTS and win in _OPT_ATTR_WINDOWS:
                    clean_attr.append({"event_type": et, "window_days": win})
            if clean_attr:
                out["attribution_spec"] = clean_attr

        cats = raw.get("special_ad_categories")
        if isinstance(cats, list):
            c = [x for x in cats if x in _OPT_SPECIAL_CATS]
            if c:
                out["special_ad_categories"] = c

        if isinstance(raw.get("is_dynamic_creative"), bool):
            out["is_dynamic_creative"] = raw["is_dynamic_creative"]

        try:
            dd = int(raw.get("deadline_days"))
            if 1 <= dd <= 90:
                out["deadline_days"] = dd
        except (TypeError, ValueError):
            pass

        rationale = raw.get("rationale")
        if isinstance(rationale, str) and rationale.strip():
            out["rationale"] = rationale.strip()[:400]

        return out

    def _apply_optimization(
        self, campaign_json: dict, opt: dict, step: dict, funnel_cfg: dict
    ) -> list[str]:
        """Mezcla los parámetros optimizados en el campaign_json. Devuelve notas
        legibles de lo aplicado (para mostrar al usuario)."""
        notes: list[str] = []
        campaign = campaign_json["campaign"]
        ad_set = campaign_json["ad_set"]
        targeting = ad_set["targeting"]

        # ── Edad ──
        if "age_min" in opt and "age_max" in opt:
            if (opt["age_min"], opt["age_max"]) != (targeting.get("age_min"), targeting.get("age_max")):
                targeting["age_min"] = opt["age_min"]
                targeting["age_max"] = opt["age_max"]
                notes.append(f"Edad ajustada al ICP: {opt['age_min']}-{opt['age_max']}")

        # ── Géneros ──
        if "genders" in opt:
            targeting["genders"] = opt["genders"]
            label = "hombres" if opt["genders"] == [1] else "mujeres"
            notes.append(f"Segmentación por género: {label}")

        # ── Estrategia de puja ──
        if "bid_strategy" in opt:
            campaign["bid_strategy"] = opt["bid_strategy"]
            ad_set["bid_strategy"] = opt["bid_strategy"]
            if "bid_amount" in opt:
                ad_set["bid_amount"] = opt["bid_amount"]
                # bid_amount a nivel campaña no aplica con CBO daily; va en ad set
                notes.append(
                    f"Puja {opt['bid_strategy']} con coste objetivo €{opt['bid_amount'] / 100:.2f}"
                )
            else:
                notes.append(f"Estrategia de puja: {opt['bid_strategy']}")

        # ── Pacing ──
        if "pacing_type" in opt:
            ad_set["pacing_type"] = opt["pacing_type"]
            if opt["pacing_type"] == ["no_pacing"]:
                notes.append("Entrega acelerada (no_pacing)")

        # ── Frequency cap ──
        if "frequency_control_specs" in opt:
            ad_set["frequency_control_specs"] = opt["frequency_control_specs"]
            f0 = opt["frequency_control_specs"][0]
            notes.append(
                f"Frequency cap: máx {f0['max_frequency']} cada {f0['interval_days']}d"
            )

        # ── Atribución ──
        ad_set["attribution_spec"] = opt.get(
            "attribution_spec", self._default_attribution(funnel_cfg["optimization_goal"])
        )

        # ── Categorías especiales + saneado de targeting que Meta exige ──
        if "special_ad_categories" in opt:
            cats = opt["special_ad_categories"]
            campaign["special_ad_categories"] = cats
            notes.append(f"Categorías especiales: {', '.join(cats)}")
            if any(c in _OPT_RESTRICTIVE_CATS for c in cats):
                targeting.pop("genders", None)
                targeting["age_min"] = 18
                targeting["age_max"] = 65
                targeting.pop("flexible_spec", None)
                targeting.get("targeting_automation", {}).pop("advantage_audience", None)
                # Evitar que publish_campaign re-inyecte intereses vía keywords
                campaign_json["interest_keywords"] = []
                notes.append(
                    "Targeting saneado por categoría restringida (sin género, edad 18-65, sin intereses)"
                )

        # ── Fecha límite por urgencia → end_time del ad set ──
        urgencia = step.get("urgencia", "sin_urgencia") or "sin_urgencia"
        if "deadline_days" in opt and urgencia != "sin_urgencia":
            end_dt = (datetime.now(timezone.utc) + timedelta(days=opt["deadline_days"])).replace(
                microsecond=0
            )
            ad_set["end_time"] = end_dt.isoformat()
            notes.append(f"Fin de campaña en {opt['deadline_days']} días por urgencia de la oferta")

        return notes

    # ------------------------------------------------------------------
    # Multi-ad-set (Fase 3): test de audiencia + retargeting
    # ------------------------------------------------------------------

    # Mínimo €/día para fragmentar la campaña en varios ad sets sin matar el aprendizaje
    _MULTI_ADSET_MIN_DAILY = 10.0

    @staticmethod
    def _clone(obj: Any) -> Any:
        """Copia profunda segura (todo el contenido es JSON-serializable)."""
        return json.loads(json.dumps(obj))

    def _clone_primary_delivery(self, primary: dict) -> dict:
        """Copia los ajustes de entrega del ad set primario (sin name/targeting/ads)."""
        keep = {
            "optimization_goal", "billing_event", "bid_strategy", "bid_amount",
            "status", "destination_type", "attribution_spec", "pacing_type",
            "frequency_control_specs", "dsa_beneficiary", "dsa_payor",
            "is_dynamic_creative",
        }
        out = {k: self._clone(v) for k, v in primary.items() if k in keep}
        if primary.get("promoted_object"):
            out["promoted_object"] = self._clone(primary["promoted_object"])
        return out

    def _build_additional_ad_sets(
        self, campaign_json: dict, step: dict, interests: list[dict],
        custom_audiences: list[dict], budget: dict,
    ) -> tuple[list[dict], list[str]]:
        """Construye ad sets extra reutilizando el creativo A del primario.

        - Test de audiencia: variante "amplia" (sin intereses) frente al primario
          (con intereses) → deja que Meta encuentre qué audiencia rinde mejor.
        - Retargeting: si la cuenta tiene audiencias personalizadas, ad set templado.
        """
        extras: list[dict] = []
        notes: list[str] = []
        primary = campaign_json["ad_set"]
        primary_ads = campaign_json.get("ads", [])
        if not primary_ads:
            return extras, notes

        daily = budget["daily_eur"]
        primary_targeting = primary.get("targeting", {})
        base_name = primary.get("name", "Ad set")

        def _clone_ad(suffix: str) -> dict:
            ad = self._clone(primary_ads[0])
            ad["name"] = f"{ad.get('name', 'Anuncio')} — {suffix}"
            return ad

        # ── P2: test de audiencia amplia (solo si hay intereses con los que contrastar)
        audience_test = step.get("audience_test", True)
        if audience_test and interests and daily >= self._MULTI_ADSET_MIN_DAILY:
            broad_targeting = self._clone(primary_targeting)
            broad_targeting.pop("flexible_spec", None)  # sin intereses = amplia
            broad_targeting.setdefault("targeting_automation", {"advantage_audience": 1})
            ad_set = self._clone_primary_delivery(primary)
            ad_set["name"] = f"{base_name} — Audiencia amplia (test)"
            ad_set["targeting"] = broad_targeting
            ad_set["ads"] = [_clone_ad("Amplia")]
            extras.append(ad_set)
            notes.append("Test de audiencia: ad set amplio (sin intereses) vs. ad set con intereses")

        # ── P3: retargeting con audiencias personalizadas existentes ──────
        retargeting = step.get("retargeting", True)
        if retargeting and custom_audiences:
            ca = [{"id": a["id"], "name": a.get("name", "")} for a in custom_audiences[:5]]
            retarget_targeting: dict[str, Any] = {
                "geo_locations": self._clone(primary_targeting.get("geo_locations", {"countries": ["ES"]})),
                "age_min": primary_targeting.get("age_min", 18),
                "age_max": primary_targeting.get("age_max", 65),
                "custom_audiences": ca,
                # retargeting es preciso: sin expansión Advantage+
            }
            ad_set = self._clone_primary_delivery(primary)
            ad_set["name"] = f"{base_name} — Retargeting"
            ad_set["targeting"] = retarget_targeting
            ad_set["ads"] = [_clone_ad("Retargeting")]
            extras.append(ad_set)
            names = ", ".join(a["name"] for a in ca if a["name"])[:120]
            notes.append(f"Ad set de retargeting sobre tus audiencias: {names or 'personalizadas'}")

        return extras, notes

    # ------------------------------------------------------------------
    # Multi-Angle (Capa 7): 1 campaign → N ad sets (1 por ángulo)
    # ------------------------------------------------------------------

    async def _build_multi_angle_campaign(
        self, step: dict, research: dict, copy: dict, landing: dict, budget: dict,
        interests: list[dict], ad_account_id: str, funnel_cfg: dict,
    ) -> tuple[dict, list[dict]]:
        """Construye una campaña con un ad set por ángulo. Cada ad set lleva su
        propio creativo (copy + imagen del ángulo). Presupuesto equitativo en fase 1.
        Devuelve (campaign_json, angles_tested)."""
        copies = [c for c in copy.get("copies", []) if c]
        if not copies:
            cj = await self._build_campaign_json(
                step, research, copy, landing, budget, interests, ad_account_id, funnel_cfg
            )
            return cj, []

        n = len(copies)
        per_ad_set_cents = max(100, math.ceil(budget["daily_cents"] / n))

        base_cj: dict | None = None
        ad_sets: list[dict] = []
        angles_tested: list[dict] = []

        for idx, ac in enumerate(copies):
            angle = ac.get("angle") or f"angulo_{idx + 1}"
            single_copy = {
                "copies": [ac],
                "creative_type": ac.get("creative_source") or copy.get("creative_type") or "image_ai",
                "ab_testing": False,
            }
            cj = await self._build_campaign_json(
                step, research, single_copy, landing, budget, interests, ad_account_id, funnel_cfg
            )
            if base_cj is None:
                base_cj = cj
            ad_set = cj["ad_set"]
            ad_set["name"] = f"{ad_set.get('name', 'Ad set')} — Ángulo: {angle}"
            ad_set["daily_budget"] = per_ad_set_cents
            ad_set["ads"] = cj.get("ads", [])
            ad_set["_angle"] = angle
            ad_sets.append(ad_set)
            angles_tested.append({
                "angle": angle,
                "hook": ac.get("hook", ""),
                "image_url": ac.get("image_url"),
                "budget_share": round(1 / n, 3),
                "ctr": None, "cpl": None, "roas": None,
                "status": "active",
            })

        campaign = base_cj["campaign"]
        # Presupuesto a nivel ad set (equitativo) → desactivar CBO en fase de exploración
        campaign.pop("daily_budget", None)
        campaign["campaign_budget_optimization"] = False

        campaign_json = {
            "api_version": META_API_VERSION,
            "ad_account_id": ad_account_id,
            "creation_order": ["campaign", "ad_sets", "adcreatives", "ads"],
            "campaign": campaign,
            "ad_set": ad_sets[0],
            "additional_ad_sets": ad_sets[1:],
            "ab_mode": "multi_angle",
            "interest_keywords": self._extract_interest_keywords(research),
        }
        return campaign_json, angles_tested

    # ------------------------------------------------------------------
    # Entrypoint
    # ------------------------------------------------------------------

    async def run_task(self, step: dict, context: dict | None = None) -> dict[str, Any]:
        context = context or {}
        research: dict = context.get("ResearchAgent", {})
        copy: dict = context.get("CopyAgent", {})
        landing: dict = context.get("LandingAgent", {})

        funnel_type: str = step.get("funnel_type", "landing_lm")
        post_conversion_goal: str = step.get("post_conversion_goal", "thank_you_only")
        funnel_cfg = _resolve_funnel_config(funnel_type, post_conversion_goal)

        budget = self._extract_budget(step)
        access_token: str | None = step.get("meta_access_token") or None
        # Keywords tipo-interés (LLM) con fallback al extractor determinista
        interest_keywords = await self._generate_interest_keywords(step, research)
        if not interest_keywords:
            interest_keywords = self._extract_interest_keywords(research)
        interests = await self._map_interests(interest_keywords, access_token)
        ad_account_id: str = step.get("meta_ad_account_id") or "act_XXXXXXXXXX"

        ab_mode: str = step.get("ab_mode") or "ab_classic"
        multi_angle = ab_mode == "multi_angle" and len(copy.get("copies", [])) > 1
        angles_tested: list[dict] = []

        if multi_angle:
            campaign_json, angles_tested = await self._build_multi_angle_campaign(
                step, research, copy, landing, budget, interests, ad_account_id, funnel_cfg
            )
        else:
            campaign_json = await self._build_campaign_json(
                step, research, copy, landing, budget, interests, ad_account_id, funnel_cfg
            )

        # Propagar las keywords buenas (LLM) para la re-búsqueda al publicar
        campaign_json["interest_keywords"] = interest_keywords

        # Datos reales de la cuenta Meta (Fase 2): tamaño de audiencia + benchmarks
        # históricos. Solo si hay token; alimentan al optimizador y al chequeo de
        # presupuesto para decidir con datos en vez de a ciegas.
        account_data: dict[str, Any] = {}
        custom_audiences: list[dict] = []
        if access_token:
            benchmarks = await get_account_benchmarks(access_token, ad_account_id)
            estimate = await get_delivery_estimate(
                access_token,
                ad_account_id,
                campaign_json["ad_set"].get("targeting", {}),
                funnel_cfg["optimization_goal"],
            )
            account_data = {"benchmarks": benchmarks, "audience_estimate": estimate}
            custom_audiences = await get_custom_audiences(access_token, ad_account_id)

        # Optimización del modelo: el LLM completa los parámetros técnicos que el
        # builder deja en valores por defecto (puja, pacing, freq cap, géneros,
        # edad, ventana de atribución, fechas por urgencia, categorías especiales).
        optimization = await self._optimize_campaign(
            step, research, funnel_cfg, budget, account_data
        )
        optimization_notes = self._apply_optimization(campaign_json, optimization, step, funnel_cfg)

        # Multi-ad-set (Fase 3): test de audiencia amplia + retargeting, reutilizando
        # el creativo del primario. Se construye DESPUÉS de optimizar para heredar
        # los ajustes de entrega ya optimizados.
        # En multi_angle NO se añade: los ad sets adicionales ya son los ángulos.
        if not multi_angle:
            additional_ad_sets, multi_notes = self._build_additional_ad_sets(
                campaign_json, step, interests, custom_audiences, budget
            )
            if additional_ad_sets:
                campaign_json["additional_ad_sets"] = additional_ad_sets
                optimization_notes.extend(multi_notes)
        else:
            optimization_notes.append(
                f"Multi-Angle: {len(angles_tested)} ángulos en paralelo, presupuesto equitativo en fase 1"
            )

        validation_errors, validation_warnings = self._validate_before_publish(step, campaign_json)
        validation_warnings.extend(self._budget_learning_check(budget, funnel_cfg, account_data))

        # Aviso si la audiencia quedó amplia por no resolver intereses (P1)
        if not interests:
            validation_warnings.append(
                "Sin intereses resueltos: la campaña usará audiencia amplia + Advantage+ Audience. "
                "Conecta tu token de Meta para segmentar por intereses reales."
            )

        result: dict[str, Any] = {
            "status": "ready_to_publish",
            "budget_summary": budget["summary"],
            "budget": budget,
            "interests_mapped": interests,
            "funnel_type": funnel_type,
            "post_conversion_goal": post_conversion_goal,
            "meta_objective": funnel_cfg["objective"],
            "ab_mode": ab_mode,
            "angles_tested": angles_tested,
            "campaign_json": campaign_json,
            "optimization_applied": optimization_notes,
            "optimization_rationale": optimization.get("rationale", ""),
            "account_data": account_data,
            "meta_api_base": f"https://graph.facebook.com/{META_API_VERSION}",
            "creation_flow": [
                "POST /act_{ad_account_id}/adimages × N → image_hash (si hace falta)",
                "POST /act_{ad_account_id}/campaigns → campaign_id",
                "POST /act_{ad_account_id}/adsets   → adset_id  (requiere campaign_id)",
                "POST /act_{ad_account_id}/adcreatives × 2 → creative_id_a, creative_id_b",
                "POST /act_{ad_account_id}/ads      × 2 → ad_id_a, ad_id_b",
            ],
            "requires_meta_keys": not bool(access_token),
            "validation_errors": validation_errors,
            "validation_warnings": validation_warnings,
            "note": "Campaña lista. Aprueba para publicar en Meta Graph API.",
        }

        # Publicar solo si todo está OK y el usuario aprobó explícitamente
        if access_token and step.get("approved") and not validation_errors:
            try:
                published = await publish_campaign(
                    access_token=access_token,
                    ad_account_id=ad_account_id,
                    campaign_json=campaign_json,
                    dsa_beneficiary=step.get("company_name", "Anunciante"),
                    dsa_payor=step.get("company_name", "Anunciante"),
                    page_id=step.get("meta_page_id", ""),
                    instagram_user_id=step.get("instagram_user_id", ""),
                )
                result["status"] = "published"
                result["published_ids"] = published
            except MetaAdsError as exc:
                result["status"] = "publish_error"
                result["error"] = str(exc)
            except httpx.HTTPStatusError as exc:
                result["status"] = "publish_error"
                result["error"] = exc.response.text

        return result
