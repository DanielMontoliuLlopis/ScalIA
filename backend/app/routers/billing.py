import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.billing import (
    CheckoutRequest,
    CheckoutResponse,
    FounderStatus,
    PlanInfo,
    PortalResponse,
)
from app.services import commissions, permissions, stripe_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


def _plan_info(tier: str) -> PlanInfo:
    d = stripe_service.PLAN_DEFS[tier]
    return PlanInfo(
        id=tier,
        name=d["name"],
        amount=d["amount"],
        founder_amount=d["founder_amount"],
        currency=settings.STRIPE_CURRENCY,
        trial_days=settings.STRIPE_TRIAL_DAYS,
        active_campaigns_limit=d["active_campaigns_limit"],
        team_seats=permissions.TIER_LIMITS[tier]["team_seats"],
        features=sorted(permissions.TIER_FEATURES[tier]),
    )


@router.get("/plans", response_model=list[PlanInfo])
async def list_plans() -> list[PlanInfo]:
    return [_plan_info("starter"), _plan_info("growth"), _plan_info("agency")]


@router.get("/research-plans")
async def list_research_plans() -> list[dict]:
    """Planes Research Mode (suscripción mensual por escaneos, sin fundador)."""
    out = []
    for tier, d in stripe_service.RESEARCH_PLAN_DEFS.items():
        out.append({
            "id": tier,
            "name": d["name"],
            "description": d["description"],
            "amount": d["amount"],
            "currency": settings.STRIPE_CURRENCY,
            "scans_per_month": d["scans_per_month"],
            "price_per_scan": round(d["amount"] / 100 / d["scans_per_month"], 2),
        })
    return out


async def _count_founders(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(User.id)).where(User.is_founder.is_(True)))
    return int(result.scalar() or 0)


@router.get("/founder-status", response_model=FounderStatus)
async def founder_status(db: AsyncSession = Depends(get_db)) -> FounderStatus:
    total = settings.FOUNDER_SPOTS_LIMIT
    taken = await _count_founders(db)
    left = max(total - taken, 0)
    return FounderStatus(
        spots_total=total,
        spots_taken=taken,
        spots_left=left,
        is_open=left > 0,
    )


@router.post("/checkout-session", response_model=CheckoutResponse)
async def create_checkout_session(
    body: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe no configurado")

    # Solo el owner de la cuenta gestiona la facturación
    if not permissions.can(current_user, "manage_billing"):
        raise HTTPException(status_code=403, detail="Solo el owner puede gestionar la suscripción")

    # Plataforma completa (starter/growth/agency) aún no disponible — solo Research Mode.
    if not stripe_service.is_research_plan(body.plan):
        raise HTTPException(
            status_code=403,
            detail="La plataforma completa llega pronto. De momento solo Research Mode.",
        )

    # Research Mode no tiene precio fundador
    founder = body.founder and not stripe_service.is_research_plan(body.plan)
    if founder:
        taken = await _count_founders(db)
        if taken >= settings.FOUNDER_SPOTS_LIMIT and not current_user.is_founder:
            raise HTTPException(
                status_code=409,
                detail="Programa Fundadores agotado — todos los cupos están ocupados.",
            )

    success_url = f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{settings.FRONTEND_URL}/onboarding/plan?canceled=1"

    try:
        url, customer_id = stripe_service.create_checkout_session(
            user=current_user,
            plan=body.plan,
            success_url=success_url,
            cancel_url=cancel_url,
            founder=founder,
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Error creando checkout session")
        raise HTTPException(status_code=500, detail=f"Error Stripe: {e}")

    if not current_user.stripe_customer_id:
        current_user.stripe_customer_id = customer_id
        await db.commit()

    return CheckoutResponse(url=url)


@router.post("/portal-session", response_model=PortalResponse)
async def create_portal_session(
    current_user: User = Depends(get_current_user),
) -> PortalResponse:
    if not permissions.can(current_user, "manage_billing"):
        raise HTTPException(status_code=403, detail="Solo el owner puede gestionar la suscripción")
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="Sin cliente Stripe — primero suscríbete")
    return_url = f"{settings.FRONTEND_URL}/settings"
    url = stripe_service.create_portal_session(
        customer_id=current_user.stripe_customer_id, return_url=return_url
    )
    return PortalResponse(url=url)


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    payload = await request.body()
    if not stripe_signature or not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=400, detail="Firma faltante")

    try:
        event = stripe_service.parse_webhook(payload, stripe_signature)
    except Exception as e:
        logger.exception("Webhook signature invalid")
        raise HTTPException(status_code=400, detail=f"Invalid signature: {e}")

    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type in (
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.trial_will_end",
    ):
        # Convivencia con otro SaaS en la misma cuenta Stripe: ignora subs ajenas.
        if not stripe_service.subscription_belongs_to_app(obj):
            return {"received": True, "ignored": "foreign_app"}
        await _sync_subscription(db, obj)
    elif event_type == "customer.subscription.deleted":
        if not stripe_service.subscription_belongs_to_app(obj):
            return {"received": True, "ignored": "foreign_app"}
        await _mark_subscription_canceled(db, obj)
    elif event_type in ("invoice.paid", "invoice.payment_succeeded"):
        # Solo invoices de esta app generan comisión (idempotente por invoice_id).
        if not stripe_service.invoice_belongs_to_app(obj):
            return {"received": True, "ignored": "foreign_app"}
        await commissions.record_commission_from_invoice(db, obj)
    elif event_type == "checkout.session.completed":
        # cuando el checkout termina, Stripe ya manda subscription.created
        pass

    return {"received": True}


async def _sync_subscription(db: AsyncSession, sub: dict) -> None:
    customer_id = sub.get("customer")
    if not customer_id:
        return
    result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
    user = result.scalar_one_or_none()
    if not user:
        logger.warning("Subscription para customer desconocido %s", customer_id)
        return

    plan = stripe_service.plan_from_subscription(sub)
    if plan:
        prev_plan = user.plan
        user.plan = plan
        if stripe_service.is_research_plan(plan):
            # Research Mode: sin campañas; recargar saldo de escaneos del ciclo
            user.active_campaigns_limit = 0
            cap = stripe_service.RESEARCH_PLAN_DEFS[plan]["scans_per_month"]
            # Recargar al activar/renovar o al cambiar de plan (no acumula)
            if prev_plan != plan or (user.scans_remaining or 0) <= 0:
                user.scans_remaining = cap
        else:
            user.active_campaigns_limit = stripe_service.PLAN_DEFS[plan]["active_campaigns_limit"]

    # Precio fundador → bloqueo de por vida (una vez fundador, siempre fundador)
    if stripe_service.founder_from_subscription(sub):
        user.is_founder = True

    user.stripe_subscription_id = sub.get("id")
    user.subscription_status = sub.get("status")
    period_end = sub.get("current_period_end")
    if period_end:
        user.subscription_current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)
        if plan and stripe_service.is_research_plan(plan):
            user.scans_reset_at = user.subscription_current_period_end
    await db.commit()


async def _mark_subscription_canceled(db: AsyncSession, sub: dict) -> None:
    customer_id = sub.get("customer")
    if not customer_id:
        return
    result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
    user = result.scalar_one_or_none()
    if not user:
        return
    # Sin trial: al cancelar pierde el acceso por completo hasta volver a suscribirse.
    user.subscription_status = "canceled"
    user.plan = "canceled"
    user.active_campaigns_limit = 0
    user.scans_remaining = 0
    await db.commit()
