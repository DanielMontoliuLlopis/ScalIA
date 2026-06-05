"""Ejecuta en Meta Graph API una recomendación del OptimizationAgent tras su
aprobación. Cierra el ciclo propone → apruebo → ejecuta (y permite deshacer).

Cada handler devuelve un dict de resultado:
    {"status": "applied" | "manual" | "failed", "executed": bool,
     "detail": str, "changes": list[dict], "planned": list[dict] | None}

- "applied": se mutó algo en Meta correctamente.
- "manual": recomendación de asesoría (copy_refresh, audience_*, etc.) — no se
  ejecuta automáticamente; queda aprobada para que el usuario actúe.
- "failed": se intentó mutar Meta y falló (detalle en `detail`).

Idempotencia: las mutaciones de presupuesto guardan el plan absoluto de objetivos en
`planned`. Un reintento reaplica esos valores absolutos (poner el mismo daily_budget
dos veces es inocuo) en vez de recomputar el factor sobre un presupuesto ya subido.

`changes` registra cada mutación con `from`/`to` para poder DESHACER (reactivar
pausados, restaurar presupuestos).

NUNCA lanza: cualquier error de Meta se captura y se devuelve como "failed".
"""
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.plan import Plan
from app.models.user_settings import UserSettings
from app.tools.meta_ads import (
    MetaAdsError,
    get_campaign_adsets,
    get_campaign_budget,
    update_adset_budget,
    update_campaign_budget,
    update_entity_status,
)

# Tipos que no se ejecutan en Meta — requieren acción manual / regeneración.
ADVISORY_TYPES = {
    "copy_refresh",
    "audience_expand",
    "audience_narrow",
    "bid_adjustment",
    "angle_inconclusive",
}

DEFAULT_INCREASE_PCT = 50.0
DEFAULT_DECREASE_PCT = 30.0

# pause_variant: señal mínima en el ad perdedor antes de pausarlo.
PAUSE_VARIANT_MIN_IMPRESSIONS = 500


def _manual(detail: str) -> dict:
    return {"status": "manual", "executed": False, "detail": detail, "changes": [], "planned": None}


def _applied(detail: str, changes: list[dict], planned: list[dict] | None = None) -> dict:
    return {"status": "applied", "executed": True, "detail": detail,
            "changes": changes, "planned": planned}


def _failed(detail: str, planned: list[dict] | None = None) -> dict:
    return {"status": "failed", "executed": False, "detail": detail,
            "changes": [], "planned": planned}


def _budget_factor(rec_type: str, payload: dict) -> float:
    """Factor multiplicativo para budget_increase / budget_decrease."""
    increase = rec_type == "budget_increase"
    pct = payload.get("suggested_increase_pct")
    if pct is None:
        pct = payload.get("change_pct")
    if pct is None:
        pct = DEFAULT_INCREASE_PCT if increase else DEFAULT_DECREASE_PCT
    pct = abs(float(pct))
    return (1 + pct / 100) if increase else max(0.1, 1 - pct / 100)


# ──────────────────────────────────────────────────────────────────────────────
# Presupuesto (idempotente vía `planned`)
# ──────────────────────────────────────────────────────────────────────────────

async def _build_budget_plan(
    token: str, plan: Plan, rec_type: str, payload: dict, prior: dict | None
) -> tuple[list[dict] | None, str | None]:
    """Construye la lista de objetivos absolutos de presupuesto. Si un intento previo
    ya dejó `planned`, lo reutiliza (reintento idempotente: no recomputa el factor)."""
    if prior and prior.get("planned"):
        return prior["planned"], None

    campaign_id = plan.meta_campaign_id
    target_total_cents = None
    if payload.get("suggested_daily_eur") is not None:
        target_total_cents = max(100, int(round(float(payload["suggested_daily_eur"]) * 100)))

    try:
        camp = await get_campaign_budget(token, campaign_id)
    except MetaAdsError as e:
        return None, f"No se pudo leer el presupuesto de la campaña: {e}"

    camp_daily = camp.get("daily_budget")
    if camp_daily:  # CBO activo → presupuesto a nivel campaña
        current = int(camp_daily)
        new_cents = max(100, target_total_cents or int(round(current * _budget_factor(rec_type, payload))))
        return [{"level": "campaign", "id": campaign_id,
                 "from_cents": current, "to_cents": new_cents}], None

    # Sin CBO → presupuesto a nivel ad set.
    try:
        adsets = await get_campaign_adsets(token, campaign_id)
    except MetaAdsError as e:
        return None, f"No se pudieron leer los ad sets: {e}"

    budgeted = [a for a in adsets if a.get("daily_budget")]
    if not budgeted:
        return None, "Ningún ad set tiene presupuesto diario editable (¿CBO o lifetime budget?)."

    factor = _budget_factor(rec_type, payload)
    per_target = max(100, target_total_cents // len(budgeted)) if target_total_cents else None

    planned: list[dict] = []
    for a in budgeted:
        cur = int(a["daily_budget"])
        to_cents = per_target if per_target is not None else max(100, int(round(cur * factor)))
        planned.append({"level": "adset", "id": a["id"], "name": a.get("name"),
                        "from_cents": cur, "to_cents": to_cents})
    return planned, None


async def _execute_budget(
    token: str, plan: Plan, rec_type: str, payload: dict, prior: dict | None
) -> dict:
    planned, err = await _build_budget_plan(token, plan, rec_type, payload, prior)
    if err:
        return _failed(err)

    changes: list[dict] = []
    errors: list[str] = []
    for tgt in planned:
        to_cents = int(tgt["to_cents"])
        try:
            if tgt["level"] == "campaign":
                await update_campaign_budget(token, tgt["id"], to_cents)
            else:
                await update_adset_budget(token, tgt["id"], to_cents)
            changes.append({**tgt, "status": "budget"})
        except MetaAdsError as e:
            errors.append(f"{tgt.get('name') or tgt['id']}: {e}")

    if not changes:
        # Conservar `planned` para que el reintento reaplique los mismos objetivos.
        return _failed("Meta rechazó el cambio de presupuesto: " + "; ".join(errors), planned)

    total_from = sum(c["from_cents"] for c in changes)
    total_to = sum(c["to_cents"] for c in changes)
    detail = (
        f"Presupuesto: €{total_from/100:.2f} → €{total_to/100:.2f}/día "
        f"en {len(changes)} entidad(es)."
    )
    if errors:
        detail += f" {len(errors)} fallaron: " + "; ".join(errors)
    return _applied(detail, changes, planned)


# ──────────────────────────────────────────────────────────────────────────────
# Pausas
# ──────────────────────────────────────────────────────────────────────────────

async def _execute_pause_campaign(token: str, plan: Plan) -> dict:
    try:
        await update_entity_status(token, plan.meta_campaign_id, "PAUSED")
    except MetaAdsError as e:
        return _failed(f"Meta no pudo pausar la campaña: {e}")
    return _applied(
        "Campaña pausada en Meta.",
        [{"level": "campaign", "id": plan.meta_campaign_id, "status": "PAUSED", "from_status": "ACTIVE"}],
    )


async def _execute_angle_redistribute(token: str, plan: Plan, payload: dict, prior: dict | None) -> dict:
    """Pausa los ad sets de los ángulos perdedores y reparte SU presupuesto real
    entre los ganadores (multi_angle, presupuesto a nivel ad set). Idempotente vía
    `planned`: el reparto se calcula una vez y el reintento reaplica absolutos."""
    angles = plan.angles_tested or []
    by_angle = {a.get("angle"): a for a in angles}
    winners = [w for w in (payload.get("winners") or []) if w in by_angle]
    losers = [l for l in (payload.get("losers") or []) if l in by_angle]

    if not losers:
        return _manual("No hay ángulos perdedores concluyentes que pausar todavía.")
    if not winners:
        return _manual("No hay ángulo ganador donde concentrar el presupuesto todavía.")

    missing = [a for a in winners + losers if not by_angle[a].get("ad_set_id")]
    if missing:
        return _failed(
            f"Faltan ad_set_id en los ángulos ({', '.join(missing)}). "
            "Se rellenan solos en el próximo sync horario; reintenta luego."
        )

    # Plan de objetivos: leer presupuestos reales una sola vez.
    planned = (prior or {}).get("planned")
    if not planned:
        try:
            live = {x["id"]: x for x in await get_campaign_adsets(token, plan.meta_campaign_id)}
        except MetaAdsError as e:
            return _failed(f"No se pudieron leer los ad sets: {e}")

        loser_ids = [by_angle[l]["ad_set_id"] for l in losers]
        winner_ids = [by_angle[w]["ad_set_id"] for w in winners]
        freed = sum(int((live.get(i) or {}).get("daily_budget") or 0) for i in loser_ids)
        add_each = freed // len(winner_ids) if winner_ids else 0

        planned = []
        for l, lid in zip(losers, loser_ids):
            planned.append({"level": "adset", "angle": l, "id": lid,
                            "status": "PAUSED", "from_status": "ACTIVE"})
        for w, wid in zip(winners, winner_ids):
            cur = int((live.get(wid) or {}).get("daily_budget") or 0)
            planned.append({"level": "adset", "angle": w, "id": wid,
                            "from_cents": cur, "to_cents": max(100, cur + add_each)})

    changes: list[dict] = []
    errors: list[str] = []
    for tgt in planned:
        try:
            if tgt.get("status") == "PAUSED":
                await update_entity_status(token, tgt["id"], "PAUSED")
                if tgt.get("angle") in by_angle:
                    by_angle[tgt["angle"]]["status"] = "paused"
            else:
                await update_adset_budget(token, tgt["id"], int(tgt["to_cents"]))
            changes.append(tgt)
        except MetaAdsError as e:
            errors.append(f"{tgt.get('angle') or tgt['id']}: {e}")

    if not changes:
        return _failed("Meta rechazó la redistribución: " + "; ".join(errors), planned)

    plan.angles_tested = angles
    flag_modified(plan, "angles_tested")

    paused = [c for c in changes if c.get("status") == "PAUSED"]
    bumped = [c for c in changes if "to_cents" in c]
    detail = (
        f"Redistribución: {len(paused)} ángulo(s) pausado(s); presupuesto liberado "
        f"repartido en {', '.join(winners)} ({len(bumped)} ad set(s) subidos)."
    )
    if errors:
        detail += f" Incidencias: {'; '.join(errors)}"
    return _applied(detail, changes, planned)


async def _execute_pause_variant(token: str, db: AsyncSession, plan: Plan, payload: dict) -> dict:
    """Pausa el ad (variante A/B) peor. Solo aplica a ab_classic — en multi_angle el
    mecanismo correcto es angle_redistribute (señal por ángulo, no por ad suelto)."""
    if (plan.ab_mode or "ab_classic") == "multi_angle":
        return _manual(
            "En Multi-Angle no se pausa una variante suelta: usa 'Redistribuir ángulos', "
            "que decide por señal de ángulo con z-test."
        )

    from sqlalchemy import func

    from app.models.metric_snapshot import MetricSnapshot

    target_ad_id = payload.get("ad_id")
    if target_ad_id:
        try:
            await update_entity_status(token, str(target_ad_id), "PAUSED")
        except MetaAdsError as e:
            return _failed(f"Meta no pudo pausar el ad {target_ad_id}: {e}")
        return _applied(
            f"Ad {target_ad_id} pausado.",
            [{"level": "ad", "id": str(target_ad_id), "status": "PAUSED", "from_status": "ACTIVE"}],
        )

    rows = (await db.execute(
        select(
            MetricSnapshot.meta_ad_id,
            func.sum(MetricSnapshot.impressions),
            func.sum(MetricSnapshot.clicks),
        )
        .where(
            MetricSnapshot.plan_id == plan.id,
            MetricSnapshot.level == "ad",
            MetricSnapshot.breakdown_key == "",
            MetricSnapshot.meta_ad_id != "",
        )
        .group_by(MetricSnapshot.meta_ad_id)
    )).all()

    ads = [
        {"id": r[0], "impr": int(r[1] or 0), "clicks": int(r[2] or 0),
         "ctr": (int(r[2] or 0) / int(r[1])) if r[1] else 0.0}
        for r in rows
    ]
    if len(ads) < 2:
        return _manual("Solo hay un ad con datos — no hay variante peor que pausar todavía.")

    worst = min(ads, key=lambda a: a["ctr"])
    best = max(ads, key=lambda a: a["ctr"])
    if worst["id"] == best["id"]:
        return _manual("Las variantes rinden igual — sin perdedor claro todavía.")
    if worst["impr"] < PAUSE_VARIANT_MIN_IMPRESSIONS:
        return _manual(
            f"La variante peor solo tiene {worst['impr']} impresiones "
            f"(<{PAUSE_VARIANT_MIN_IMPRESSIONS}). Seguir testeando antes de pausar."
        )

    try:
        await update_entity_status(token, worst["id"], "PAUSED")
    except MetaAdsError as e:
        return _failed(f"Meta no pudo pausar el ad perdedor: {e}")
    return _applied(
        f"Variante peor pausada (CTR {worst['ctr']*100:.2f}% vs {best['ctr']*100:.2f}% "
        f"de la ganadora, {worst['impr']:,} impresiones).",
        [{"level": "ad", "id": worst["id"], "status": "PAUSED", "from_status": "ACTIVE",
          "ctr": round(worst["ctr"], 5)}],
    )


async def _execute_offer_consolidate(
    token: str, db: AsyncSession, plan: Plan, payload: dict
) -> dict:
    """Pausa la campaña de la oferta perdedora del test (la ganadora sigue activa)."""
    loser_plan_id = payload.get("loser_plan_id")
    if not loser_plan_id:
        return _manual("La recomendación no indica la oferta perdedora.")
    loser = (await db.execute(
        select(Plan).where(Plan.id == uuid.UUID(str(loser_plan_id)))
    )).scalar_one_or_none()
    if not loser or not loser.meta_campaign_id:
        return _manual("La oferta perdedora no tiene campaña publicada en Meta.")
    try:
        await update_entity_status(token, loser.meta_campaign_id, "PAUSED")
    except MetaAdsError as e:
        return _failed(f"Meta no pudo pausar la oferta perdedora: {e}")
    return _applied(
        f"Test consolidado en '{payload.get('winner_label', 'la oferta ganadora')}': "
        f"campaña de la oferta perdedora pausada.",
        [{"level": "campaign", "id": loser.meta_campaign_id, "status": "PAUSED",
          "from_status": "ACTIVE"}],
    )


# ──────────────────────────────────────────────────────────────────────────────
# Entradas públicas
# ──────────────────────────────────────────────────────────────────────────────

async def _resolve_token(db: AsyncSession, plan: Plan) -> str | None:
    settings = (await db.execute(
        select(UserSettings).where(UserSettings.client_account_id == plan.client_account_id)
    )).scalar_one_or_none()
    return settings.meta_access_token if settings else None


async def execute_recommendation(db: AsyncSession, plan: Plan, rec: Any) -> dict:
    """Punto de entrada. Resuelve token + dispatch por tipo. No lanza nunca.
    `rec.applied_result` (intento previo) se usa para reintentos idempotentes."""
    rec_type = rec.type
    payload = rec.action_payload or {}
    prior = rec.applied_result if isinstance(getattr(rec, "applied_result", None), dict) else None

    if rec_type in ADVISORY_TYPES:
        return _manual("Recomendación de asesoría: aplícala manualmente (no se ejecuta en Meta).")

    if not plan.meta_campaign_id:
        return _failed("El plan no tiene campaña publicada en Meta.")

    token = await _resolve_token(db, plan)
    if not token:
        return _failed("Meta Access Token no configurado en Ajustes.")

    try:
        if rec_type in ("budget_increase", "budget_decrease"):
            return await _execute_budget(token, plan, rec_type, payload, prior)
        if rec_type == "pause_campaign":
            return await _execute_pause_campaign(token, plan)
        if rec_type == "pause_variant":
            return await _execute_pause_variant(token, db, plan, payload)
        if rec_type == "angle_redistribute":
            return await _execute_angle_redistribute(token, plan, payload, prior)
        if rec_type == "offer_test_consolidate":
            return await _execute_offer_consolidate(token, db, plan, payload)
    except MetaAdsError as e:
        return _failed(f"Error Meta API: {e}")
    except Exception as e:  # red de seguridad — nunca romper el approve
        return _failed(f"Error inesperado al ejecutar: {e}")

    return _manual(f"Tipo '{rec_type}' sin ejecución automática. Aplícalo manualmente.")


async def undo_recommendation(db: AsyncSession, plan: Plan, rec: Any) -> dict:
    """Revierte una recomendación aplicada: reactiva entidades pausadas y restaura
    presupuestos a su valor previo (`from_cents`). Usa el `changes` registrado."""
    prior = rec.applied_result if isinstance(getattr(rec, "applied_result", None), dict) else None
    changes = (prior or {}).get("changes") or []
    if not changes:
        return _failed("No hay cambios registrados que deshacer.")

    token = await _resolve_token(db, plan)
    if not token:
        return _failed("Meta Access Token no configurado en Ajustes.")

    by_angle = {a.get("angle"): a for a in (plan.angles_tested or [])}
    reverted: list[dict] = []
    errors: list[str] = []

    for c in changes:
        try:
            if c.get("status") == "PAUSED":
                await update_entity_status(token, c["id"], "ACTIVE")
                if c.get("angle") in by_angle:
                    by_angle[c["angle"]]["status"] = "active"
                reverted.append({**c, "status": "ACTIVE"})
            elif "from_cents" in c and "to_cents" in c:
                back = int(c["from_cents"])
                if back <= 0:
                    continue
                if c.get("level") == "campaign":
                    await update_campaign_budget(token, c["id"], back)
                else:
                    await update_adset_budget(token, c["id"], back)
                reverted.append({**c, "to_cents": back, "restored_from_cents": c["to_cents"]})
        except MetaAdsError as e:
            errors.append(f"{c.get('angle') or c['id']}: {e}")

    if plan.angles_tested is not None:
        flag_modified(plan, "angles_tested")

    if not reverted:
        return _failed("Meta rechazó la reversión: " + "; ".join(errors))
    detail = f"Reversión aplicada: {len(reverted)} cambio(s) deshecho(s)."
    if errors:
        detail += f" Incidencias: {'; '.join(errors)}"
    return {"status": "reverted", "executed": True, "detail": detail,
            "changes": reverted, "planned": None}
