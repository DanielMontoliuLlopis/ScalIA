"""Celery tasks para snapshots de métricas Meta — corre cada hora.

Guarda Meta Insights en `metric_snapshots` con `time_increment=1` (una fila por
día) a nivel de ad + breakdowns a nivel de campaña. Idempotente (upsert): cada
hora reescribe la ventana reciente, así el día en curso se va completando.
Es la base de series temporales, comparación de periodos y detección de anomalías.
"""
import asyncio
import uuid
from datetime import date, datetime

from app.workers.celery_app import celery_app

# Cuántos días recientes refrescar en cada corrida (el día en curso muta).
SYNC_WINDOW_PRESET = "last_7d"


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


@celery_app.task(name="sync_metrics_for_all_campaigns")
def sync_metrics_for_all_campaigns() -> dict:
    """Encola un sync de métricas por cada campaña publicada (meta_campaign_id)."""
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker

    from app.config import settings
    from app.models.plan import Plan

    sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    engine = create_engine(sync_url, pool_pre_ping=True)
    Session = sessionmaker(engine)

    db = Session()
    processed = 0
    try:
        plans = db.execute(
            select(Plan).where(
                Plan.meta_campaign_id.isnot(None),
                Plan.status.in_(["executing", "pending_ads_approval", "done"]),
            )
        ).scalars().all()
        for plan in plans:
            sync_metrics_for_plan.delay(str(plan.id))
            processed += 1
    finally:
        db.close()
    return {"queued": processed}


@celery_app.task(name="sync_metrics_for_plan")
def sync_metrics_for_plan(plan_id: str, date_preset: str | None = None) -> dict:
    """Trae insights de Meta para un plan y los persiste en metric_snapshots."""
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker

    from app.config import settings
    from app.models.plan import Plan
    from app.models.user_settings import UserSettings
    from app.tools.meta_ads import SUPPORTED_BREAKDOWNS, fetch_insights

    sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    engine = create_engine(sync_url, pool_pre_ping=True)
    Session = sessionmaker(engine)
    db = Session()

    preset = date_preset or SYNC_WINDOW_PRESET

    try:
        plan = db.get(Plan, uuid.UUID(plan_id))
        if not plan or not plan.meta_campaign_id:
            return {"plan_id": plan_id, "skipped": "no meta campaign"}

        st = db.execute(
            select(UserSettings).where(
                UserSettings.client_account_id == plan.client_account_id
            )
        ).scalar_one_or_none()
        token = st.meta_access_token if st else None
        if not token:
            return {"plan_id": plan_id, "skipped": "no meta token"}

        campaign_id = plan.meta_campaign_id

        # Backfill: planes multi_angle publicados antes del fix no tienen ad_set_id en
        # angles_tested. Lo rellenamos casando por nombre de ad set ("... Ángulo: X").
        if (plan.ab_mode or "ab_classic") == "multi_angle" and plan.angles_tested:
            if any(not a.get("ad_set_id") for a in plan.angles_tested):
                _backfill_angle_adset_ids(db, plan, token, campaign_id)

        # ad_set_id → angle (multi_angle)
        angle_by_adset: dict[str, str] = {}
        for a in (plan.angles_tested or []):
            asid = a.get("ad_set_id")
            if asid:
                angle_by_adset[str(asid)] = a.get("angle")

        async def _pull() -> list[dict]:
            tasks = [
                fetch_insights(token, campaign_id, level="ad",
                               time_increment=1, date_preset=preset),
            ]
            for bd in SUPPORTED_BREAKDOWNS:
                tasks.append(fetch_insights(
                    token, campaign_id, level="campaign",
                    breakdown=bd, time_increment=1, date_preset=preset,
                ))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            level_for = ["ad"] + ["campaign"] * len(SUPPORTED_BREAKDOWNS)
            merged: list[dict] = []
            for lvl, res in zip(level_for, results):
                if isinstance(res, Exception):
                    continue
                for r in res:
                    r["_level"] = lvl
                    merged.append(r)
            return merged

        rows = asyncio.run(_pull())

        written = _upsert_snapshots(db, plan, campaign_id, angle_by_adset, rows)
        _sync_angles_from_snapshots(db, plan)
        alerts = _evaluate_alerts(db, plan)
        db.commit()
        return {"plan_id": plan_id, "rows": len(rows), "written": written, "alerts": alerts}
    finally:
        db.close()


def _upsert_snapshots(db, plan, campaign_id, angle_by_adset, rows) -> int:
    """Upsert idempotente sobre la unique constraint de metric_snapshots."""
    from sqlalchemy import func
    from sqlalchemy.dialects.postgresql import insert

    from app.models.metric_snapshot import MetricSnapshot

    written = 0
    for r in rows:
        snap_date = _parse_date(r.get("date_start"))
        if not snap_date:
            continue
        level = r.get("_level", "campaign")
        adset_id = str(r.get("adset_id") or "")
        ad_id = str(r.get("ad_id") or "")
        impressions = r["impressions"]
        clicks = r["clicks"]
        spend = r["spend"]
        leads = r["leads"]

        values = {
            "id": uuid.uuid4(),
            "client_account_id": plan.client_account_id,
            "plan_id": plan.id,
            "meta_campaign_id": str(r.get("campaign_id") or campaign_id),
            "meta_adset_id": adset_id,
            "meta_ad_id": ad_id,
            "level": level,
            "angle": angle_by_adset.get(adset_id),
            "breakdown_key": r.get("breakdown_key", ""),
            "breakdown_value": r.get("breakdown_value", ""),
            "snapshot_date": snap_date,
            "impressions": impressions,
            "clicks": clicks,
            "reach": r["reach"],
            "leads": leads,
            "conversions": r["conversions"],
            "spend": spend,
            "revenue": r["revenue"],
            "ctr": r.get("ctr") if r.get("ctr") is not None else (clicks / impressions * 100 if impressions else None),
            "cpc": r.get("cpc") if r.get("cpc") is not None else (spend / clicks if clicks else None),
            "cpm": r.get("cpm") if r.get("cpm") is not None else (spend / impressions * 1000 if impressions else None),
            "cpl": (spend / leads) if leads else None,
        }

        stmt = insert(MetricSnapshot).values(**values)
        update_cols = {
            c: stmt.excluded[c]
            for c in (
                "impressions", "clicks", "reach", "leads", "conversions",
                "spend", "revenue", "ctr", "cpc", "cpm", "cpl",
                "angle", "meta_campaign_id", "fetched_at",
            )
        }
        update_cols["fetched_at"] = func.now()
        stmt = stmt.on_conflict_do_update(
            constraint="uq_metric_snapshot_identity",
            set_=update_cols,
        )
        db.execute(stmt)
        written += 1
    return written


def _backfill_angle_adset_ids(db, plan, token: str, campaign_id: str) -> None:
    """Rellena ad_set_id en angles_tested casando por nombre de ad set en Meta.
    El AdsAgent nombra cada ad set '… — Ángulo: {angle}'. Auto-cura planes viejos."""
    from sqlalchemy.orm.attributes import flag_modified

    from app.tools.meta_ads import get_campaign_adsets

    try:
        adsets = asyncio.run(get_campaign_adsets(token, campaign_id))
    except Exception:
        return
    if not adsets:
        return

    angles = [dict(a) for a in plan.angles_tested]
    used: set[str] = {str(a["ad_set_id"]) for a in angles if a.get("ad_set_id")}
    changed = False
    for a in angles:
        if a.get("ad_set_id"):
            continue
        angle = (a.get("angle") or "").lower()
        match = next(
            (s for s in adsets
             if str(s["id"]) not in used
             and angle and f"ángulo: {angle}" in (s.get("name") or "").lower()),
            None,
        )
        if match:
            a["ad_set_id"] = str(match["id"])
            used.add(str(match["id"]))
            changed = True

    if changed:
        plan.angles_tested = angles
        flag_modified(plan, "angles_tested")


# ── Multi-Angle en vivo: refrescar plan.angles_tested desde snapshots ─────────

def _sync_angles_from_snapshots(db, plan) -> None:
    """Agrega snapshots por ad set y vuelca las métricas en plan.angles_tested.

    Mantiene el rendimiento por ángulo fresco (cada hora) en lugar de esperar al
    ciclo de 24h del OptimizationAgent. No cambia de estado ángulos (winner/loser);
    eso sigue siendo decisión del OptimizationAgent con z-test.
    """
    from sqlalchemy import func, select

    from app.models.metric_snapshot import MetricSnapshot

    angles = plan.angles_tested or []
    if not angles:
        return

    rows = db.execute(
        select(
            MetricSnapshot.meta_adset_id,
            func.sum(MetricSnapshot.impressions),
            func.sum(MetricSnapshot.clicks),
            func.sum(MetricSnapshot.leads),
            func.sum(MetricSnapshot.spend),
            func.sum(MetricSnapshot.revenue),
        )
        .where(
            MetricSnapshot.plan_id == plan.id,
            MetricSnapshot.level == "ad",
            MetricSnapshot.breakdown_key == "",
            MetricSnapshot.meta_adset_id != "",
        )
        .group_by(MetricSnapshot.meta_adset_id)
    ).all()
    by_adset = {r[0]: r for r in rows}

    changed = False
    for a in angles:
        asid = str(a.get("ad_set_id") or "")
        m = by_adset.get(asid)
        if not m:
            continue
        impr = int(m[1] or 0)
        clicks = int(m[2] or 0)
        leads = int(m[3] or 0)
        spend = float(m[4] or 0)
        revenue = float(m[5] or 0)
        a["impressions"] = impr
        a["clicks"] = clicks
        a["leads"] = leads
        a["spend"] = round(spend, 2)
        a["ctr"] = round(clicks / impr * 100, 4) if impr else None
        a["cpl"] = round(spend / leads, 2) if leads else None
        a["roas"] = round(revenue / spend, 2) if spend else None
        changed = True

    if changed:
        from sqlalchemy.orm.attributes import flag_modified
        plan.angles_tested = angles
        flag_modified(plan, "angles_tested")


# ── Alertas automáticas sobre snapshots ──────────────────────────────────────

# Umbrales (alineados con los del OptimizationAgent / CLAUDE.md)
CPL_SPIKE_RATIO = 1.30        # CPL hoy > 130% del de ayer
CPL_SPIKE_MIN_SPEND = 10.0
CTR_DROP_MIN_IMPRESSIONS = 3000
CTR_DROP_THRESHOLD = 0.5      # % CTR
SPEND_NO_LEADS_MIN = 30.0     # € gastados sin un solo lead
ROAS_LOW_MIN_SPEND = 30.0


def _evaluate_alerts(db, plan) -> int:
    """Evalúa reglas sobre los snapshots diarios y crea/actualiza alertas."""
    from sqlalchemy import func, select

    from app.models.metric_snapshot import MetricSnapshot

    rows = db.execute(
        select(
            MetricSnapshot.snapshot_date,
            func.sum(MetricSnapshot.impressions),
            func.sum(MetricSnapshot.clicks),
            func.sum(MetricSnapshot.leads),
            func.sum(MetricSnapshot.spend),
            func.sum(MetricSnapshot.revenue),
        )
        .where(
            MetricSnapshot.plan_id == plan.id,
            MetricSnapshot.level == "ad",
            MetricSnapshot.breakdown_key == "",
        )
        .group_by(MetricSnapshot.snapshot_date)
        .order_by(MetricSnapshot.snapshot_date.desc())
    ).all()
    if not rows:
        return 0

    def _day(r) -> dict:
        impr = int(r[1] or 0)
        clicks = int(r[2] or 0)
        leads = int(r[3] or 0)
        spend = float(r[4] or 0)
        revenue = float(r[5] or 0)
        return {
            "date": r[0], "impr": impr, "clicks": clicks, "leads": leads,
            "spend": spend, "revenue": revenue,
            "ctr": (clicks / impr * 100) if impr else None,
            "cpl": (spend / leads) if leads else None,
            "roas": (revenue / spend) if spend else None,
        }

    today = _day(rows[0])
    prev = _day(rows[1]) if len(rows) > 1 else None
    created = 0

    # 1) CPL spike día/día
    if (today["cpl"] is not None and prev and prev["cpl"]
            and today["spend"] >= CPL_SPIKE_MIN_SPEND
            and today["cpl"] > prev["cpl"] * CPL_SPIKE_RATIO):
        pct = (today["cpl"] / prev["cpl"] - 1) * 100
        created += _upsert_alert(
            db, plan, "cpl_spike", "warning",
            f"CPL subió {pct:.0f}% en un día",
            f"El coste por lead pasó de €{prev['cpl']:.2f} a €{today['cpl']:.2f} "
            f"({today['leads']} leads, €{today['spend']:.2f} gastados hoy).",
            "cpl", today["cpl"], prev["cpl"], today["date"],
        )

    # 2) CTR bajo
    if (today["impr"] >= CTR_DROP_MIN_IMPRESSIONS
            and today["ctr"] is not None and today["ctr"] < CTR_DROP_THRESHOLD):
        created += _upsert_alert(
            db, plan, "ctr_drop", "warning",
            f"CTR bajo: {today['ctr']:.2f}%",
            f"Con {today['impr']:,} impresiones el CTR es {today['ctr']:.2f}% "
            f"(umbral {CTR_DROP_THRESHOLD}%). El creativo o el ángulo no conecta.",
            "ctr", today["ctr"], CTR_DROP_THRESHOLD, today["date"],
        )

    # 3) Gasto sin leads
    if today["spend"] >= SPEND_NO_LEADS_MIN and today["leads"] == 0:
        created += _upsert_alert(
            db, plan, "spend_no_leads", "critical",
            f"€{today['spend']:.0f} gastados hoy sin leads",
            f"La campaña lleva €{today['spend']:.2f} hoy sin un solo lead. "
            f"Revisa segmentación, oferta o landing.",
            "spend", today["spend"], 0, today["date"],
        )

    # 4) ROAS bajo (solo si hay revenue atribuido por Meta)
    if (today["spend"] >= ROAS_LOW_MIN_SPEND and today["revenue"] > 0
            and today["roas"] is not None and today["roas"] < 1):
        created += _upsert_alert(
            db, plan, "roas_low", "warning",
            f"ROAS por debajo de 1x ({today['roas']:.2f}x)",
            f"Hoy gastaste €{today['spend']:.2f} y generaste €{today['revenue']:.2f} "
            f"de revenue atribuido. Estás perdiendo dinero a este ritmo.",
            "roas", today["roas"], 1, today["date"],
        )

    return created


def _upsert_alert(db, plan, atype, severity, title, message, metric_key,
                  current_value, baseline_value, snap_date) -> int:
    from sqlalchemy.dialects.postgresql import insert

    from app.models.metric_alert import MetricAlert

    stmt = insert(MetricAlert).values(
        id=uuid.uuid4(),
        client_account_id=plan.client_account_id,
        plan_id=plan.id,
        type=atype,
        severity=severity,
        title=title,
        message=message,
        metric_key=metric_key,
        current_value=current_value,
        baseline_value=baseline_value,
        status="active",
        snapshot_date=snap_date,
    )
    # Mismo día + mismo tipo → refrescar el mensaje/valores, no duplicar.
    stmt = stmt.on_conflict_do_update(
        constraint="uq_metric_alert_identity",
        set_={
            "title": stmt.excluded.title,
            "message": stmt.excluded.message,
            "current_value": stmt.excluded.current_value,
            "baseline_value": stmt.excluded.baseline_value,
            "severity": stmt.excluded.severity,
        },
    )
    db.execute(stmt)
    return 1
