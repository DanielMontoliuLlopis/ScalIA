import json
import logging
from typing import Any

import httpx

META_API_VERSION = "v23.0"
META_GRAPH_BASE = f"https://graph.facebook.com/{META_API_VERSION}"

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Constantes Meta API v23
# ──────────────────────────────────────────────────────────────────────────────

LEGACY_TO_OUTCOME_OBJECTIVE = {
    "LEAD_GENERATION": "OUTCOME_LEADS",
    "CONVERSIONS": "OUTCOME_SALES",
    "LINK_CLICKS": "OUTCOME_TRAFFIC",
    "TRAFFIC": "OUTCOME_TRAFFIC",
    "BRAND_AWARENESS": "OUTCOME_AWARENESS",
    "REACH": "OUTCOME_AWARENESS",
    "VIDEO_VIEWS": "OUTCOME_AWARENESS",
    "ENGAGEMENT": "OUTCOME_ENGAGEMENT",
    "POST_ENGAGEMENT": "OUTCOME_ENGAGEMENT",
    "PAGE_LIKES": "OUTCOME_ENGAGEMENT",
    "MESSAGES": "OUTCOME_ENGAGEMENT",
    "APP_INSTALLS": "OUTCOME_APP_PROMOTION",
    "STORE_VISITS": "OUTCOME_AWARENESS",
}

# Posiciones válidas Meta v23 — corrección automática
FB_POSITION_FIXES = {
    "reels": "facebook_reels",
}

# Atribución por defecto recomendada por Meta para conversiones
DEFAULT_ATTRIBUTION_SPEC = [
    {"event_type": "CLICK_THROUGH", "window_days": 7},
    {"event_type": "VIEW_THROUGH", "window_days": 1},
]


# ──────────────────────────────────────────────────────────────────────────────
# Errores y POST helper
# ──────────────────────────────────────────────────────────────────────────────

class MetaAdsError(Exception):
    pass


async def _post(access_token: str, path: str, data: dict) -> dict:
    url = f"{META_GRAPH_BASE}{path}"
    logger.warning("META POST %s payload=%s", path, json.dumps(data, ensure_ascii=False)[:3000])
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, params={"access_token": access_token}, json=data)
    body = resp.json()
    if "error" in body:
        logger.error("META ERROR %s → %s", path, json.dumps(body["error"]))
        raise MetaAdsError(body["error"].get("message", str(body["error"])))
    return body


# ──────────────────────────────────────────────────────────────────────────────
# Insights & validation helpers
# ──────────────────────────────────────────────────────────────────────────────

async def get_campaign_insights(access_token: str, campaign_id: str) -> dict:
    """Devuelve métricas Meta Insights de una campaña (lifetime)."""
    fields = "impressions,clicks,spend,reach,cpc,ctr,cpp,actions"
    url = f"{META_GRAPH_BASE}/{campaign_id}/insights"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params={
            "access_token": access_token,
            "fields": fields,
            "date_preset": "lifetime",
            "level": "campaign",
        })
    body = resp.json()
    if "error" in body:
        raise MetaAdsError(body["error"].get("message", str(body["error"])))
    data = body.get("data", [])
    if not data:
        return {}
    row = data[0]
    actions = row.get("actions", [])
    leads = next((int(a["value"]) for a in actions if a["action_type"] == "lead"), 0)
    return {
        "impressions": int(row.get("impressions", 0)),
        "clicks": int(row.get("clicks", 0)),
        "spend": float(row.get("spend", 0)),
        "reach": int(row.get("reach", 0)),
        "cpc": float(row.get("cpc", 0)) if row.get("cpc") else None,
        "ctr": float(row.get("ctr", 0)) if row.get("ctr") else None,
        "cpp": float(row.get("cpp", 0)) if row.get("cpp") else None,
        "leads": leads,
    }


async def get_delivery_estimate(
    access_token: str,
    ad_account_id: str,
    targeting: dict,
    optimization_goal: str,
) -> dict:
    """Tamaño de audiencia estimado para un targeting+objetivo (Meta delivery_estimate).

    Devuelve {} si falla. No lanza — es un dato de apoyo, no bloqueante.
    """
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(
                f"{META_GRAPH_BASE}/{ad_account_id}/delivery_estimate",
                params={
                    "access_token": access_token,
                    "optimization_goal": optimization_goal,
                    "targeting_spec": json.dumps(targeting),
                },
            )
        body = r.json()
        if "error" in body:
            logger.warning("delivery_estimate error: %s", body["error"].get("message"))
            return {}
        data = body.get("data", [])
        if not data:
            return {}
        row = data[0]
        lower = row.get("estimate_mau_lower_bound") or row.get("estimate_dau")
        upper = row.get("estimate_mau_upper_bound")
        return {
            "estimate_ready": row.get("estimate_ready"),
            "audience_lower": int(lower) if lower is not None else None,
            "audience_upper": int(upper) if upper is not None else None,
        }
    except Exception as exc:
        logger.warning("get_delivery_estimate failed: %s", exc)
        return {}


async def get_account_benchmarks(access_token: str, ad_account_id: str) -> dict:
    """Métricas medias de la cuenta (últimos 90 días) para calibrar decisiones.

    Devuelve {} si la cuenta no tiene historial o falla.
    """
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{META_GRAPH_BASE}/{ad_account_id}/insights",
                params={
                    "access_token": access_token,
                    "fields": "cpm,cpc,ctr,spend,cost_per_action_type",
                    "date_preset": "last_90d",
                    "level": "account",
                },
            )
        body = r.json()
        if "error" in body:
            logger.warning("account benchmarks error: %s", body["error"].get("message"))
            return {}
        data = body.get("data", [])
        if not data:
            return {}
        row = data[0]
        cpa_map: dict[str, float] = {}
        for item in row.get("cost_per_action_type", []) or []:
            try:
                cpa_map[item.get("action_type", "")] = float(item.get("value", 0) or 0)
            except (TypeError, ValueError):
                continue
        return {
            "cpm": float(row["cpm"]) if row.get("cpm") else None,
            "cpc": float(row["cpc"]) if row.get("cpc") else None,
            "ctr": float(row["ctr"]) if row.get("ctr") else None,
            "spend_90d": float(row.get("spend", 0) or 0),
            "cost_per_action": cpa_map,
        }
    except Exception as exc:
        logger.warning("get_account_benchmarks failed: %s", exc)
        return {}


async def get_custom_audiences(
    access_token: str, ad_account_id: str, limit: int = 15
) -> list[dict]:
    """Lista las audiencias personalizadas de la cuenta (para retargeting/lookalike).

    Devuelve [{id, name, subtype, approximate_count}]. [] si falla o no hay.
    """
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(
                f"{META_GRAPH_BASE}/{ad_account_id}/customaudiences",
                params={
                    "access_token": access_token,
                    "fields": "id,name,subtype,approximate_count_lower_bound",
                    "limit": limit,
                },
            )
        body = r.json()
        if "error" in body:
            logger.warning("custom_audiences error: %s", body["error"].get("message"))
            return []
        out: list[dict] = []
        for a in body.get("data", []):
            out.append({
                "id": str(a.get("id")),
                "name": a.get("name", ""),
                "subtype": a.get("subtype"),
                "approximate_count": a.get("approximate_count_lower_bound"),
            })
        return out
    except Exception as exc:
        logger.warning("get_custom_audiences failed: %s", exc)
        return []


async def validate_interest_ids(access_token: str, interest_ids: list[str]) -> list[str]:
    """Devuelve solo los IDs que Meta confirma vía Targeting Search API."""
    valid: list[str] = []
    async with httpx.AsyncClient(timeout=10) as client:
        for iid in interest_ids:
            try:
                r = await client.get(
                    f"{META_GRAPH_BASE}/search",
                    params={
                        "type": "adinterest",
                        "q": iid,
                        "access_token": access_token,
                        "limit": 1,
                    },
                )
                data = r.json()
                items = data.get("data", [])
                if any(str(item.get("id")) == str(iid) for item in items):
                    valid.append(iid)
            except Exception:
                pass
    return valid


async def search_interests_by_keywords(
    access_token: str,
    keywords: list[str],
    locale: str = "es_ES",
    max_interests: int = 8,
) -> list[dict]:
    """Busca intereses reales en Meta Targeting Search API por keywords.

    Devuelve lista de {"id": str, "name": str} con IDs verificados por Meta.
    """
    seen_ids: set[str] = set()
    interests: list[dict] = []

    async with httpx.AsyncClient(timeout=10) as client:
        for kw in keywords:
            if not kw or not kw.strip():
                continue
            try:
                r = await client.get(
                    f"{META_GRAPH_BASE}/search",
                    params={
                        "type": "adinterest",
                        "q": kw.strip()[:50],
                        "locale": locale,
                        "access_token": access_token,
                        "limit": 3,
                    },
                )
                items = r.json().get("data", [])
                for item in items[:1]:
                    iid = str(item.get("id", ""))
                    name = item.get("name", "")
                    if iid and iid not in seen_ids:
                        seen_ids.add(iid)
                        interests.append({"id": iid, "name": name})
            except Exception:
                pass
            if len(interests) >= max_interests:
                break

    return interests


async def upload_image_url(
    access_token: str, ad_account_id: str, image_url: str
) -> str | None:
    """Sube una imagen por URL a /adimages → devuelve image_hash."""
    if not image_url or image_url.startswith("{{") or image_url.startswith("data:"):
        return None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{META_GRAPH_BASE}/{ad_account_id}/adimages",
                params={"access_token": access_token},
                json={"url": image_url},
            )
        body = resp.json()
        if "error" in body:
            logger.error("META adimages error: %s", body["error"])
            return None
        images = body.get("images", {})
        for file_data in images.values():
            return file_data.get("hash")
    except Exception as exc:
        logger.error("upload_image_url failed: %s", exc)
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Sanitizadores
# ──────────────────────────────────────────────────────────────────────────────

def _normalize_objective(objective: str) -> str:
    if objective in LEGACY_TO_OUTCOME_OBJECTIVE:
        return LEGACY_TO_OUTCOME_OBJECTIVE[objective]
    return objective


def _fix_facebook_positions(targeting: dict) -> dict:
    """Corrige posiciones inválidas (`reels` → `facebook_reels`)."""
    fb_pos = targeting.get("facebook_positions", [])
    if fb_pos:
        targeting["facebook_positions"] = [
            FB_POSITION_FIXES.get(p, p) for p in fb_pos
        ]
    return targeting


def _extract_interest_ids(targeting: dict) -> list[str]:
    """Lee IDs de intereses desde `flexible_spec` o `interests` legacy."""
    ids: list[str] = []
    for group in targeting.get("flexible_spec", []) or []:
        for interest in group.get("interests", []) or []:
            iid = interest.get("id")
            if iid:
                ids.append(str(iid))
    for interest in targeting.get("interests", []) or []:
        iid = interest.get("id")
        if iid:
            ids.append(str(iid))
    return list(dict.fromkeys(ids))  # dedupe preservando orden


def _filter_interests_by_valid_ids(targeting: dict, valid_ids: set[str]) -> dict:
    """Filtra `flexible_spec.interests` e `interests` para quedarse solo con IDs válidos."""
    new_flex = []
    for group in targeting.get("flexible_spec", []) or []:
        new_group = dict(group)
        interests = [i for i in (group.get("interests") or []) if str(i.get("id")) in valid_ids]
        if interests:
            new_group["interests"] = interests
        else:
            new_group.pop("interests", None)
        # Mantener grupo solo si conserva al menos un filtro
        if any(new_group.get(k) for k in ("interests", "behaviors", "demographics", "work_positions")):
            new_flex.append(new_group)
    if new_flex:
        targeting["flexible_spec"] = new_flex
    else:
        targeting.pop("flexible_spec", None)

    legacy = [i for i in (targeting.get("interests") or []) if str(i.get("id")) in valid_ids]
    if legacy:
        targeting["interests"] = legacy
    else:
        targeting.pop("interests", None)

    return targeting


# ──────────────────────────────────────────────────────────────────────────────
# Creación de entidades Meta
# ──────────────────────────────────────────────────────────────────────────────

async def create_campaign(
    access_token: str, ad_account_id: str, campaign: dict
) -> tuple[str, int | None]:
    """Crea la campaña. Devuelve (campaign_id, daily_budget_cents)."""
    objective = _normalize_objective(campaign["objective"])
    use_cbo = bool(campaign.get("campaign_budget_optimization"))
    daily_budget = campaign.get("daily_budget")
    lifetime_budget = campaign.get("lifetime_budget")

    data: dict[str, Any] = {
        "name": campaign["name"],
        "objective": objective,
        "status": campaign.get("status", "PAUSED"),
        "special_ad_categories": campaign.get("special_ad_categories", []),
        "buying_type": campaign.get("buying_type", "AUCTION"),
    }

    if use_cbo:
        data["campaign_budget_optimization"] = True
        if daily_budget:
            data["daily_budget"] = int(daily_budget)
        elif lifetime_budget:
            data["lifetime_budget"] = int(lifetime_budget)
        if campaign.get("bid_strategy"):
            data["bid_strategy"] = campaign["bid_strategy"]
        if campaign.get("bid_cap"):
            data["bid_cap"] = int(campaign["bid_cap"])

    if campaign.get("spend_cap"):
        data["spend_cap"] = int(campaign["spend_cap"])
    if campaign.get("start_time"):
        data["start_time"] = campaign["start_time"]
    if campaign.get("stop_time"):
        data["stop_time"] = campaign["stop_time"]
    if campaign.get("special_ad_category_country"):
        data["special_ad_category_country"] = campaign["special_ad_category_country"]

    result = await _post(access_token, f"/{ad_account_id}/campaigns", data)
    # Si CBO está activo, el adset no debe llevar presupuesto
    adset_daily = None if use_cbo else daily_budget
    return result["id"], adset_daily


async def create_ad_set(
    access_token: str,
    ad_account_id: str,
    ad_set: dict,
    campaign_id: str,
    daily_budget: int | None = None,
    dsa_beneficiary: str = "",
    dsa_payor: str = "",
    promoted_object: dict | None = None,
) -> str:
    """Crea ad set con destination_type, promoted_object, attribution_spec, Advantage+ Audience."""
    optimization_goal = ad_set.get("optimization_goal", "LINK_CLICKS")
    billing_event = ad_set.get("billing_event", "IMPRESSIONS")

    targeting = {**(ad_set.get("targeting") or {})}
    targeting = _fix_facebook_positions(targeting)
    # Advantage+ Audience ON por defecto — mejor rendimiento Meta 2025
    targeting.setdefault("targeting_automation", {"advantage_audience": 1})

    data: dict[str, Any] = {
        "name": ad_set["name"],
        "campaign_id": campaign_id,
        "optimization_goal": optimization_goal,
        "billing_event": billing_event,
        "bid_strategy": ad_set.get("bid_strategy", "LOWEST_COST_WITHOUT_CAP"),
        "targeting": targeting,
        "status": ad_set.get("status", "PAUSED"),
        "dsa_beneficiary": dsa_beneficiary or ad_set.get("dsa_beneficiary") or "Anunciante",
        "dsa_payor": dsa_payor or ad_set.get("dsa_payor") or dsa_beneficiary or "Anunciante",
    }

    if daily_budget:
        data["daily_budget"] = int(daily_budget)
    elif ad_set.get("lifetime_budget"):
        data["lifetime_budget"] = int(ad_set["lifetime_budget"])

    if ad_set.get("destination_type"):
        data["destination_type"] = ad_set["destination_type"]

    promoted = promoted_object or ad_set.get("promoted_object")
    if promoted:
        # No enviar pixel placeholder
        pixel = str(promoted.get("pixel_id", ""))
        if pixel.startswith("{{") or pixel == "":
            promoted = {k: v for k, v in promoted.items() if k != "pixel_id"}
        if promoted:
            data["promoted_object"] = promoted

    # Attribution spec recomendada Meta para conversiones
    if ad_set.get("attribution_spec"):
        data["attribution_spec"] = ad_set["attribution_spec"]
    elif optimization_goal in {"OFFSITE_CONVERSIONS", "VALUE", "LEAD_GENERATION", "QUALITY_LEAD"}:
        data["attribution_spec"] = DEFAULT_ATTRIBUTION_SPEC

    if ad_set.get("start_time"):
        data["start_time"] = ad_set["start_time"]
    if ad_set.get("end_time"):
        data["end_time"] = ad_set["end_time"]
    if ad_set.get("frequency_control_specs"):
        data["frequency_control_specs"] = ad_set["frequency_control_specs"]
    if ad_set.get("pacing_type"):
        data["pacing_type"] = ad_set["pacing_type"]
    if ad_set.get("bid_amount"):
        data["bid_amount"] = int(ad_set["bid_amount"])
    if ad_set.get("is_dynamic_creative"):
        data["is_dynamic_creative"] = True

    result = await _post(access_token, f"/{ad_account_id}/adsets", data)
    return result["id"]


async def create_ad_creative(
    access_token: str,
    ad_account_id: str,
    creative: dict,
    page_id: str = "",
    instagram_user_id: str = "",
) -> str:
    """Crea ad creative. Soporta inyección de page_id/instagram_user_id reales."""
    story_spec = {**(creative.get("object_story_spec") or {})}

    if page_id:
        story_spec["page_id"] = page_id
    if instagram_user_id and not story_spec.get("instagram_user_id"):
        story_spec["instagram_user_id"] = instagram_user_id

    # Limpiar image_url no-pública del link_data (Meta exige image_hash o URL pública)
    link_data = {**(story_spec.get("link_data") or {})}
    if link_data:
        image_url = link_data.get("image_url", "")
        if image_url and (image_url.startswith("data:") or not image_url.startswith("http")):
            link_data.pop("image_url", None)
        story_spec["link_data"] = link_data

    data: dict[str, Any] = {
        "name": creative.get("name", "Creative"),
        "object_story_spec": story_spec,
    }
    if creative.get("url_tags"):
        data["url_tags"] = creative["url_tags"]
    asset_feed = creative.get("asset_feed_spec")
    if asset_feed:
        asset_feed = {**asset_feed}
        # Resolver imágenes (image_url → image_hash) que exige el asset_feed_spec
        raw_images = asset_feed.get("images") or []
        resolved: list[dict] = []
        for img in raw_images:
            if img.get("hash"):
                resolved.append({"hash": img["hash"]})
                continue
            url = img.get("image_url") or img.get("url")
            h = await upload_image_url(access_token, ad_account_id, url or "")
            if h:
                resolved.append({"hash": h})
        if resolved:
            asset_feed["images"] = resolved
        else:
            asset_feed.pop("images", None)
        data["asset_feed_spec"] = asset_feed
    if creative.get("instagram_permalink_url"):
        data["instagram_permalink_url"] = creative["instagram_permalink_url"]
    if creative.get("effective_object_story_id"):
        data["effective_object_story_id"] = creative["effective_object_story_id"]

    result = await _post(access_token, f"/{ad_account_id}/adcreatives", data)
    return result["id"]


async def create_ad(
    access_token: str,
    ad_account_id: str,
    ad: dict,
    ad_set_id: str,
    creative_id: str,
) -> str:
    """Crea ad final. Propaga tracking_specs y conversion_domain."""
    data: dict[str, Any] = {
        "name": ad["name"],
        "adset_id": ad_set_id,
        "creative": {"creative_id": creative_id},
        "status": ad.get("status", "PAUSED"),
    }
    if ad.get("tracking_specs"):
        data["tracking_specs"] = ad["tracking_specs"]
    if ad.get("conversion_domain"):
        data["conversion_domain"] = ad["conversion_domain"]
    if ad.get("ad_schedule_end_time"):
        data["ad_schedule_end_time"] = ad["ad_schedule_end_time"]
    if ad.get("priority") is not None:
        data["priority"] = int(ad["priority"])

    result = await _post(access_token, f"/{ad_account_id}/ads", data)
    return result["id"]


# ──────────────────────────────────────────────────────────────────────────────
# Flujo completo de publicación
# ──────────────────────────────────────────────────────────────────────────────

def _inject_image_hash(creative: dict, image_hash: str) -> dict:
    """Inyecta image_hash real en el link_data del creative."""
    import copy as copy_lib
    creative = copy_lib.deepcopy(creative)
    link_data = creative.get("object_story_spec", {}).get("link_data", {})
    if link_data:
        link_data["image_hash"] = image_hash
        link_data.pop("image_url", None)
    return creative


async def publish_campaign(
    access_token: str,
    ad_account_id: str,
    campaign_json: dict,
    dsa_beneficiary: str = "Anunciante",
    dsa_payor: str = "Anunciante",
    page_id: str = "",
    instagram_user_id: str = "",
) -> dict:
    """Publica campaign + ad_set + N ads en Meta Graph API v23.0.

    Flujo:
      1. Subir imágenes pendientes → image_hash
      2. POST /campaigns           → campaign_id
      3. POST /adsets              → adset_id (requiere campaign_id)
      4. POST /adcreatives × N     → creative_id por ad
      5. POST /ads × N             → ad_id por ad
    """
    campaign = campaign_json["campaign"]
    use_cbo = bool(campaign.get("campaign_budget_optimization"))
    ad_set = {**campaign_json["ad_set"]}
    ads = campaign_json.get("ads", [])

    # ── Intereses: buscar frescos via API o validar pre-calculados ───────────
    targeting = ad_set.get("targeting", {})
    interest_keywords: list[str] = campaign_json.get("interest_keywords", [])

    if interest_keywords:
        # Buscar intereses reales directamente en Meta — máxima fiabilidad
        fresh_interests = await search_interests_by_keywords(access_token, interest_keywords)
        if fresh_interests:
            targeting = dict(targeting)
            targeting["flexible_spec"] = [{"interests": [{"id": i["id"], "name": i["name"]} for i in fresh_interests]}]
            targeting.pop("interests", None)
            ad_set["targeting"] = targeting
            logger.info("META interests resolved via API: %s", [i["name"] for i in fresh_interests])
        else:
            # Fallback: validar los pre-calculados y filtrar inválidos
            interest_ids = _extract_interest_ids(targeting)
            if interest_ids:
                valid = await validate_interest_ids(access_token, interest_ids)
                ad_set["targeting"] = _filter_interests_by_valid_ids(targeting, set(valid))
    else:
        interest_ids = _extract_interest_ids(targeting)
        if interest_ids:
            valid = await validate_interest_ids(access_token, interest_ids)
            ad_set["targeting"] = _filter_interests_by_valid_ids(targeting, set(valid))

    # Corregir posiciones inválidas
    ad_set["targeting"] = _fix_facebook_positions(ad_set.get("targeting", {}))

    # ── Paso 1: subir imágenes ───────────────────────────────────────────
    image_hashes: list[str | None] = []
    for ad in ads:
        link_data = (ad.get("creative", {}).get("object_story_spec", {}).get("link_data") or {})
        raw_hash = link_data.get("image_hash", "")
        if raw_hash and not str(raw_hash).startswith("{{"):
            image_hashes.append(raw_hash)
            continue
        image_url = link_data.get("image_url") or ad.get("_meta", {}).get("image_url")
        uploaded = await upload_image_url(access_token, ad_account_id, image_url or "")
        image_hashes.append(uploaded)

    # ── Paso 2: campaña ──────────────────────────────────────────────────
    campaign_id, adset_daily_budget = await create_campaign(access_token, ad_account_id, campaign)

    # ── Paso 3: ad set ───────────────────────────────────────────────────
    ad_set_id = await create_ad_set(
        access_token,
        ad_account_id,
        ad_set,
        campaign_id,
        daily_budget=adset_daily_budget or ad_set.get("daily_budget"),
        dsa_beneficiary=dsa_beneficiary,
        dsa_payor=dsa_payor,
        promoted_object=ad_set.get("promoted_object"),
    )

    # ── Pasos 4+5: creatives + ads por variante ──────────────────────────
    ad_ids: list[str] = []
    for i, ad in enumerate(ads):
        creative = ad.get("creative") or {}
        real_hash = image_hashes[i] if i < len(image_hashes) else None
        if real_hash:
            creative = _inject_image_hash(creative, real_hash)

        creative_id = await create_ad_creative(
            access_token,
            ad_account_id,
            creative,
            page_id=page_id,
            instagram_user_id=instagram_user_id,
        )
        ad_id = await create_ad(access_token, ad_account_id, ad, ad_set_id, creative_id)
        ad_ids.append(ad_id)

    # ── Ad sets adicionales (Fase 3: test de audiencia + retargeting) ─────
    # Cada uno con su propio targeting y sus ads. Con CBO el presupuesto lo
    # reparte Meta entre todos los ad sets de la campaña.
    additional_ad_set_ids: list[str] = []
    for extra in campaign_json.get("additional_ad_sets", []) or []:
        extra = {**extra}
        extra["targeting"] = _fix_facebook_positions({**(extra.get("targeting") or {})})
        extra_ads = extra.pop("ads", []) or []
        try:
            extra_ad_set_id = await create_ad_set(
                access_token,
                ad_account_id,
                extra,
                campaign_id,
                daily_budget=None if use_cbo else extra.get("daily_budget"),
                dsa_beneficiary=dsa_beneficiary,
                dsa_payor=dsa_payor,
                promoted_object=extra.get("promoted_object"),
            )
        except MetaAdsError as exc:
            logger.error("No se pudo crear ad set adicional '%s': %s", extra.get("name"), exc)
            continue
        additional_ad_set_ids.append(extra_ad_set_id)

        for ad in extra_ads:
            creative = ad.get("creative") or {}
            link_data = creative.get("object_story_spec", {}).get("link_data") or {}
            raw_hash = link_data.get("image_hash", "")
            if not raw_hash or str(raw_hash).startswith("{{"):
                img_url = link_data.get("image_url") or ad.get("_meta", {}).get("image_url")
                uploaded = await upload_image_url(access_token, ad_account_id, img_url or "")
                if uploaded:
                    creative = _inject_image_hash(creative, uploaded)
            creative_id = await create_ad_creative(
                access_token, ad_account_id, creative,
                page_id=page_id, instagram_user_id=instagram_user_id,
            )
            ad_id = await create_ad(access_token, ad_account_id, ad, extra_ad_set_id, creative_id)
            ad_ids.append(ad_id)

    return {
        "campaign_id": campaign_id,
        "ad_set_id": ad_set_id,
        "ad_ids": ad_ids,
        "additional_ad_set_ids": additional_ad_set_ids,
        "meta_ads_manager_url": (
            f"https://www.facebook.com/adsmanager/manage/campaigns?act="
            f"{ad_account_id.replace('act_', '')}"
        ),
    }
