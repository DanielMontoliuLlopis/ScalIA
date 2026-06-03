"""Celery tasks para OptimizationAgent — corre cada 24h por campaña activa."""
from app.workers.celery_app import celery_app


@celery_app.task(name="run_optimization_for_all_campaigns")
def run_optimization_for_all_campaigns() -> dict:
    """Itera sobre todas las campañas activas y genera recomendaciones."""
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker

    from app.config import settings
    from app.models.plan import Plan
    from app.models.user import User
    from app.services import permissions

    sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    engine = create_engine(sync_url, pool_pre_ping=True)
    Session = sessionmaker(engine)

    db = Session()
    processed = 0
    errors = 0
    skipped = 0

    try:
        plans = db.execute(
            select(Plan).where(Plan.status == "done", Plan.meta_campaign_id.isnot(None))
        ).scalars().all()

        for plan in plans:
            try:
                # OptimizationAgent es feature de tier Growth+: saltar cuentas sin
                # el feature para no gastar tokens de LLM en planes que no lo incluyen.
                user = db.get(User, plan.user_id)
                owner = db.get(User, user.parent_account_id) if user and user.parent_account_id else user
                if not owner or not permissions.has_feature(owner, "optimization"):
                    skipped += 1
                    continue

                run_optimization_for_plan.delay(str(plan.id), str(plan.user_id))
                processed += 1
            except Exception as exc:
                errors += 1
                print(f"[OptimizationBeat] Error encolando plan {plan.id}: {exc}")
    finally:
        db.close()

    return {"processed": processed, "errors": errors, "skipped": skipped}


@celery_app.task(name="run_optimization_for_plan")
def run_optimization_for_plan(plan_id: str, user_id: str) -> dict:
    """Genera recomendaciones para un plan específico."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.config import settings
    from app.agents.optimization import run_optimization_for_plan as _run

    sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    engine = create_engine(sync_url, pool_pre_ping=True)
    Session = sessionmaker(engine)
    db = Session()

    try:
        created_ids = _run(plan_id, user_id, db)
        return {"plan_id": plan_id, "created": len(created_ids), "ids": created_ids}
    finally:
        db.close()
