"""Seed de datos de prueba para el Sistema de Métricas y Analytics (local).

Crea (idempotente) una campaña de prueba con:
  - un Plan multi_angle "publicado" (meta_campaign_id falso)
  - una landing + leads en varios estados (uno cerrado con revenue)
  - metric_snapshots de los últimos N días (nivel ad + breakdowns age/gender/
    publisher_platform/region/impression_device) con una curva que dispara alertas
  - reutiliza las funciones reales del worker para poblar angles_tested y alertas

Uso (desde backend/, con las migraciones aplicadas y la BD local levantada):
    python scripts/seed_metrics.py
    python scripts/seed_metrics.py --days 30 --reset

`--reset` borra los snapshots/alertas/leads del plan de prueba antes de recrear.
"""
import argparse
import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

# Permitir `import app...` ejecutando desde backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, func, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.config import settings  # noqa: E402
import app.models  # noqa: F401,E402  (registra todos los modelos)
from app.models.angle_performance import AnglePerformance  # noqa: E402
from app.models.client_account import ClientAccount  # noqa: E402
from app.models.landing_page import LandingPage  # noqa: E402
from app.models.lead import Lead  # noqa: E402
from app.models.metric_alert import MetricAlert  # noqa: E402
from app.models.metric_snapshot import MetricSnapshot  # noqa: E402
from app.models.plan import Plan  # noqa: E402
from app.models.user import User  # noqa: E402
from app.workers.metrics_tasks import (  # noqa: E402
    _evaluate_alerts,
    _sync_angles_from_snapshots,
    _upsert_snapshots,
)

SEED_CAMPAIGN_ID = "seed-campaign-001"

# Ad sets (1 por ángulo) — clave para multi_angle en vivo
ADSETS = [
    ("seed-adset-dolor", "dolor", 0.40),
    ("seed-adset-aspiracion", "aspiracion", 0.35),
    ("seed-adset-credibilidad", "credibilidad", 0.25),
]

# Histórico de ángulos: win rate objetivo por (business_type, ángulo).
# Genera filas winner/loser/inconclusive para alimentar los badges "X% win".
ANGLE_HISTORY = {
    "saas": {
        "credibilidad": 0.70, "aspiracion": 0.55, "social_proof": 0.50,
        "dolor": 0.45, "miedo_urgencia": 0.40, "curiosidad": 0.35,
    },
    "ecommerce": {
        "social_proof": 0.65, "miedo_urgencia": 0.55, "aspiracion": 0.45, "dolor": 0.40,
    },
}
ANGLE_HISTORY_ROWS_PER_ANGLE = 10

BREAKDOWNS = {
    "age": [("18-24", 0.2), ("25-34", 0.5), ("35-44", 0.3)],
    "gender": [("male", 0.45), ("female", 0.55)],
    "publisher_platform": [("facebook", 0.6), ("instagram", 0.4)],
    "region": [("Madrid", 0.5), ("Barcelona", 0.5)],
    "impression_device": [("mobile_app", 0.7), ("desktop", 0.3)],
}


def _day_totals(day_index: int, last_index: int) -> dict:
    """Curva de métricas por día. El último día degrada para disparar alertas
    (CPL spike + CTR drop + ROAS<1)."""
    if day_index == last_index:
        return {"impressions": 4200, "clicks": 17, "spend": 40.0, "leads": 2, "revenue": 25.0}
    # Día normal: CTR ~1.2%, CPL ~€8, ROAS ~1.5x
    wobble = (day_index % 4) * 0.05
    impressions = int(3500 * (1 + wobble))
    clicks = int(impressions * 0.012)
    spend = round(24.0 * (1 + wobble), 2)
    leads = 3
    revenue = round(spend * 1.5, 2)
    return {"impressions": impressions, "clicks": clicks, "spend": spend, "leads": leads, "revenue": revenue}


def _split(total: int | float, weight: float) -> float:
    return total * weight


def _mk_row(level, campaign_id, adset_id, ad_id, bkey, bval, snap_date, t) -> dict:
    return {
        "_level": level,
        "date_start": snap_date.isoformat(),
        "campaign_id": campaign_id,
        "adset_id": adset_id,
        "ad_id": ad_id,
        "breakdown_key": bkey,
        "breakdown_value": bval,
        "impressions": int(round(t["impressions"])),
        "clicks": int(round(t["clicks"])),
        "reach": int(round(t["impressions"] * 0.8)),
        "leads": int(round(t["leads"])),
        "conversions": int(round(t["leads"])),
        "spend": round(t["spend"], 2),
        "revenue": round(t["revenue"], 2),
        "ctr": None, "cpc": None, "cpm": None,  # los calcula el upsert
    }


def build_rows(days: int) -> list[dict]:
    rows: list[dict] = []
    today = datetime.now(timezone.utc).date()
    last_index = days - 1
    for i in range(days):
        snap_date = today - timedelta(days=last_index - i)
        totals = _day_totals(i, last_index)

        # Nivel ad — uno por ad set, repartido por budget_share
        for adset_id, _angle, share in ADSETS:
            t = {k: _split(v, share) for k, v in totals.items()}
            rows.append(_mk_row("ad", SEED_CAMPAIGN_ID, adset_id,
                                f"seed-ad-{_angle}", "", "", snap_date, t))

        # Nivel campaign — un grupo de filas por cada breakdown
        for bkey, buckets in BREAKDOWNS.items():
            for bval, weight in buckets:
                t = {k: _split(v, weight) for k, v in totals.items()}
                rows.append(_mk_row("campaign", SEED_CAMPAIGN_ID, "", "", bkey, bval, snap_date, t))
    return rows


def get_or_create_context(db):
    """Devuelve (user, client_account) para colgar la campaña de prueba."""
    owner_emails = [e.strip().lower() for e in settings.OWNER_EMAILS.split(",") if e.strip()]
    user = None
    if owner_emails:
        user = db.execute(
            select(User).where(func.lower(User.email).in_(owner_emails))
        ).scalars().first()
    if not user:
        user = db.execute(select(User).order_by(User.created_at.asc())).scalars().first()
    if not user:
        raise SystemExit("No hay usuarios en la BD. Regístrate en la app primero y reejecuta.")

    ca = db.execute(
        select(ClientAccount).where(ClientAccount.owner_id == user.id)
        .order_by(ClientAccount.created_at.asc())
    ).scalars().first()
    if not ca:
        ca = ClientAccount(owner_id=user.id, name="Workspace de prueba",
                           business_type="saas", color_palette="indigo")
        db.add(ca)
        db.flush()
        print(f"  + ClientAccount creado: {ca.id}")
    return user, ca


def get_or_create_plan(db, user, ca) -> Plan:
    plan = db.execute(
        select(Plan).where(Plan.client_account_id == ca.id,
                           Plan.meta_campaign_id == SEED_CAMPAIGN_ID)
    ).scalar_one_or_none()
    if plan:
        return plan
    plan = Plan(
        user_id=user.id,
        client_account_id=ca.id,
        title="[SEED] Campaña multi-ángulo de prueba",
        description="Campaña de prueba para el sistema de métricas.",
        steps=[],
        status="done",
        meta_campaign_id=SEED_CAMPAIGN_ID,
        funnel_type="landing_lm",
        ab_testing=True,
        ab_mode="multi_angle",
        num_angles=len(ADSETS),
        angles_tested=[
            {"angle": angle, "ad_set_id": adset_id, "hook": f"Hook del ángulo {angle}",
             "budget_share": share, "status": "active",
             "impressions": None, "clicks": None, "leads": None,
             "spend": None, "ctr": None, "cpl": None, "roas": None}
            for adset_id, angle, share in ADSETS
        ],
        precio_base=Decimal("997"),
        tipo_oferta="lanzamiento",
    )
    db.add(plan)
    db.flush()
    print(f"  + Plan creado: {plan.id}")
    return plan


def get_or_create_landing(db, plan, user, ca) -> LandingPage:
    lp = db.execute(
        select(LandingPage).where(LandingPage.plan_id == plan.id)
    ).scalars().first()
    if lp:
        return lp
    lp = LandingPage(
        plan_id=plan.id, user_id=user.id, client_account_id=ca.id,
        variant="a", campaign_type="lead_gen", funnel_type="landing_lm",
        landing_subtype="lm",
        headline="Consigue X sin Y", subheadline="La forma simple de lograrlo",
        benefits=["Beneficio 1", "Beneficio 2"], cta_text="Descargar guía",
        form_fields=[{"name": "email", "required": True}, {"name": "nombre", "required": True}],
        views=1200, conversions=64, published_at=datetime.now(timezone.utc),
    )
    db.add(lp)
    db.flush()
    print(f"  + LandingPage creada: {lp.id}")
    return lp


def seed_leads(db, plan, landing, user, ca) -> int:
    existing = db.execute(
        select(func.count()).where(Lead.plan_id == plan.id)
    ).scalar() or 0
    if existing:
        return 0
    samples = [
        ("ana@empresa.com", "Ana López", "closed", Decimal("997")),
        ("luis@startup.io", "Luis Pérez", "showed_up", None),
        ("marta@pyme.es", "Marta Ruiz", "contacted", None),
        ("jordi@negocio.cat", "Jordi Sala", "new", None),
        ("sara@agencia.com", "Sara Gil", "lost", None),
    ]
    for i, (email, nombre, status, value) in enumerate(samples):
        db.add(Lead(
            landing_page_id=landing.id, plan_id=plan.id, user_id=user.id,
            client_account_id=ca.id, email=email, nombre=nombre,
            telefono=f"+3460000000{i}", score=80 - i * 12,
            segment="hot" if i == 0 else ("warm" if i < 3 else "cold"),
            lead_status=status, closed_value=value,
            closed_at=datetime.now(timezone.utc) if status == "closed" else None,
            showed_up_at=datetime.now(timezone.utc) if status in ("showed_up", "closed") else None,
        ))
    print(f"  + {len(samples)} leads creados")
    return len(samples)


def seed_angle_performance(db, plan, user) -> int:
    """Histórico de ángulos × business_type para los badges de win-rate.

    Para cada (business_type, ángulo) crea ANGLE_HISTORY_ROWS_PER_ANGLE filas con
    una proporción de `winner` acorde al win rate objetivo; el resto se reparte
    entre loser/inconclusive. Idempotente: solo crea si no hay filas del plan.
    """
    existing = db.execute(
        select(func.count()).where(AnglePerformance.plan_id == plan.id)
    ).scalar() or 0
    if existing:
        return 0

    now = datetime.now(timezone.utc)
    created = 0
    for business_type, angles in ANGLE_HISTORY.items():
        for angle, win_rate in angles.items():
            n = ANGLE_HISTORY_ROWS_PER_ANGLE
            wins = round(win_rate * n)
            for i in range(n):
                if i < wins:
                    result, cpl, roas = "winner", 7.5, 2.4
                elif (i - wins) % 2 == 0:
                    result, cpl, roas = "loser", 22.0, 0.7
                else:
                    result, cpl, roas = "inconclusive", 13.0, 1.2
                impressions = 4000 + i * 250
                clicks = int(impressions * 0.011)
                leads = max(1, round(impressions * 0.0012))
                spend = round(leads * cpl, 2)
                db.add(AnglePerformance(
                    user_id=user.id, account_id=user.id, plan_id=plan.id,
                    business_type=business_type, angle=angle, tipo_oferta="lanzamiento",
                    impressions=impressions, clicks=clicks, leads=leads,
                    spend=Decimal(str(spend)),
                    ctr=Decimal(str(round(clicks / impressions * 100, 4))),
                    cpl=Decimal(str(cpl)), roas=Decimal(str(roas)),
                    result=result,
                    period_start=now - timedelta(days=(i + 1) * 7),
                    period_end=now - timedelta(days=i * 7),
                ))
                created += 1
    print(f"  + {created} filas de angle_performance creadas")
    return created


def reset_plan_data(db, plan) -> None:
    for model in (MetricSnapshot, MetricAlert, AnglePerformance, Lead):
        db.query(model).filter(model.plan_id == plan.id).delete(synchronize_session=False)
    print("  · datos previos del plan borrados (--reset)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30, help="días de histórico (default 30)")
    parser.add_argument("--reset", action="store_true", help="borra datos previos del plan de prueba")
    args = parser.parse_args()

    sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    engine = create_engine(sync_url, pool_pre_ping=True)
    Session = sessionmaker(engine)
    db = Session()

    try:
        print("→ Seed de métricas de prueba")
        user, ca = get_or_create_context(db)
        print(f"  · usuario: {user.email} · client_account: {ca.id}")
        plan = get_or_create_plan(db, user, ca)
        if args.reset:
            reset_plan_data(db, plan)
        landing = get_or_create_landing(db, plan, user, ca)
        seed_leads(db, plan, landing, user, ca)

        angle_by_adset = {asid: angle for asid, angle, _ in ADSETS}
        rows = build_rows(args.days)
        written = _upsert_snapshots(db, plan, SEED_CAMPAIGN_ID, angle_by_adset, rows)
        print(f"  + {written} snapshots upserted ({args.days} días)")

        _sync_angles_from_snapshots(db, plan)
        alerts = _evaluate_alerts(db, plan)
        print(f"  + ángulos sincronizados · {alerts} alertas evaluadas")

        seed_angle_performance(db, plan, user)

        db.commit()
        print("✓ Seed completado. Abre el Dashboard para ver métricas, breakdowns y alertas.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
