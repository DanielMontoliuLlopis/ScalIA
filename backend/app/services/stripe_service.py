"""Stripe service: products, prices, customers, checkout, portal.

Products and prices are auto-created on startup if they don't exist.
Cada tier tiene DOS precios:
  - precio normal           → metadata.growth_plan = <tier>
  - precio fundador (50%)    → metadata.growth_plan = <tier>, metadata.founder = "true"

El precio fundador es de por vida (programa Fundadores, cupos limitados).
"""
from __future__ import annotations

import logging
from typing import Literal

import stripe

from app.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

PlanTier = Literal["starter", "growth", "agency"]
ResearchTier = Literal["research_10", "research_100"]

# Research Mode — suscripción mensual por escaneos. Sin precio fundador.
RESEARCH_PLAN_DEFS: dict[str, dict] = {
    "research_10": {
        "name": "ScalIA — Research 10",
        "description": "10 escaneos de research/mes (ICP + 6 ángulos con copy e imagen).",
        "amount": settings.STRIPE_PRICE_RESEARCH_10_AMOUNT,
        "scans_per_month": 10,
        "research": True,
    },
    "research_100": {
        "name": "ScalIA — Research 100",
        "description": "100 escaneos de research/mes para agencias y uso intensivo.",
        "amount": settings.STRIPE_PRICE_RESEARCH_100_AMOUNT,
        "scans_per_month": 100,
        "research": True,
    },
}


def is_research_plan(plan: str) -> bool:
    return plan in RESEARCH_PLAN_DEFS


PLAN_DEFS: dict[PlanTier, dict] = {
    "starter": {
        "name": "ScalIA — Starter",
        "description": "1 campaña activa. Agentes IA completos. Para empezar.",
        "amount": settings.STRIPE_PRICE_STARTER_AMOUNT,
        "founder_amount": settings.STRIPE_PRICE_STARTER_FOUNDER_AMOUNT,
        "active_campaigns_limit": 1,
    },
    "growth": {
        "name": "ScalIA — Growth",
        "description": "5 campañas activas. Tests de oferta. Equipo hasta 3 personas.",
        "amount": settings.STRIPE_PRICE_GROWTH_AMOUNT,
        "founder_amount": settings.STRIPE_PRICE_GROWTH_FOUNDER_AMOUNT,
        "active_campaigns_limit": 5,
    },
    "agency": {
        "name": "ScalIA — Agency",
        "description": "30 campañas activas. Multi-cuenta Meta, white-label, equipo ilimitado.",
        "amount": settings.STRIPE_PRICE_AGENCY_AMOUNT,
        "founder_amount": settings.STRIPE_PRICE_AGENCY_FOUNDER_AMOUNT,
        "active_campaigns_limit": 30,
    },
}

# Cache de price_ids. Clave: (tier, founder_bool)
_PRICE_IDS: dict[tuple[PlanTier, bool], str] = {}

# IVA español (21%). Tax rate exclusivo: se añade encima del precio en checkout.
SPAIN_VAT_PERCENTAGE = 21.0
_VAT_TAX_RATE_ID: str | None = None


def _configure() -> bool:
    if not settings.STRIPE_SECRET_KEY:
        return False
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return True


def _app() -> str:
    """Namespace de esta app en la cuenta Stripe (para convivir con otro SaaS)."""
    return settings.STRIPE_APP_NAMESPACE


def belongs_to_app(metadata: dict | None) -> bool:
    """True si el objeto Stripe pertenece a esta app.

    Convivencia con otro SaaS en la misma cuenta: solo procesamos objetos cuyo
    metadata.app coincide con nuestro namespace. Objetos antiguos sin `app`
    (creados antes de este cambio) se aceptan por compatibilidad si llevan
    `growth_plan` — son nuestros de todas formas.
    """
    meta = metadata or {}
    app = meta.get("app")
    if app:
        return app == _app()
    # Compat: objetos previos sin namespace pero con nuestro marcador de plan.
    return bool(meta.get("growth_plan"))


def get_price_id(plan: PlanTier, founder: bool = False) -> str | None:
    return _PRICE_IDS.get((plan, founder))


def ensure_products_and_prices() -> None:
    """Crea products y prices (normal + fundador) en Stripe si no existen. Idempotente."""
    if not _configure():
        logger.warning("STRIPE_SECRET_KEY no configurada — saltando setup de products/prices")
        return

    vat_id = _find_or_create_vat_tax_rate()
    logger.info("Stripe IVA tax rate ready: %s", vat_id)

    for plan_key, plan_def in PLAN_DEFS.items():
        product = _find_or_create_product(plan_key, plan_def)
        normal = _find_or_create_price(plan_key, plan_def["amount"], product.id, founder=False)
        founder = _find_or_create_price(
            plan_key, plan_def["founder_amount"], product.id, founder=True
        )
        _PRICE_IDS[(plan_key, False)] = normal.id
        _PRICE_IDS[(plan_key, True)] = founder.id
        logger.info(
            "Stripe plan %s ready: product=%s normal=%s founder=%s",
            plan_key, product.id, normal.id, founder.id,
        )

    # Research Mode — solo precio normal (sin fundador)
    for plan_key, plan_def in RESEARCH_PLAN_DEFS.items():
        product = _find_or_create_product(plan_key, plan_def)
        normal = _find_or_create_price(plan_key, plan_def["amount"], product.id, founder=False)
        _PRICE_IDS[(plan_key, False)] = normal.id
        logger.info("Stripe research plan %s ready: product=%s price=%s", plan_key, product.id, normal.id)


def _find_or_create_product(plan_key: PlanTier, plan_def: dict):
    products = stripe.Product.list(active=True, limit=100).data
    for p in products:
        meta = p.metadata or {}
        if meta.get("growth_plan") == plan_key and belongs_to_app(meta):
            return p
    return stripe.Product.create(
        name=plan_def["name"],
        description=plan_def["description"],
        metadata={"growth_plan": plan_key, "app": _app()},
    )


def _find_or_create_price(plan_key: PlanTier, amount: int, product_id: str, founder: bool):
    founder_flag = "true" if founder else "false"
    prices = stripe.Price.list(product=product_id, active=True, limit=100).data
    for pr in prices:
        if (
            pr.unit_amount == amount
            and pr.currency == settings.STRIPE_CURRENCY
            and pr.recurring
            and pr.recurring.interval == "month"
            and (pr.metadata or {}).get("founder", "false") == founder_flag
        ):
            return pr
    return stripe.Price.create(
        product=product_id,
        unit_amount=amount,
        currency=settings.STRIPE_CURRENCY,
        recurring={"interval": "month"},
        tax_behavior="exclusive",  # IVA se añade encima del precio mostrado
        metadata={"growth_plan": plan_key, "founder": founder_flag, "app": _app()},
    )


def _find_or_create_vat_tax_rate() -> str:
    """Devuelve el TaxRate id del IVA español (21%). Lo crea si no existe. Idempotente."""
    global _VAT_TAX_RATE_ID
    if _VAT_TAX_RATE_ID:
        return _VAT_TAX_RATE_ID
    rates = stripe.TaxRate.list(active=True, limit=100).data
    for r in rates:
        if (
            (r.metadata or {}).get("growth_tax") == "es_vat"
            and float(r.percentage) == SPAIN_VAT_PERCENTAGE
            and r.inclusive is False
        ):
            _VAT_TAX_RATE_ID = r.id
            return r.id
    rate = stripe.TaxRate.create(
        display_name="IVA",
        description="IVA España",
        jurisdiction="ES",
        country="ES",
        percentage=SPAIN_VAT_PERCENTAGE,
        inclusive=False,
        tax_type="vat",
        metadata={"growth_tax": "es_vat"},
    )
    _VAT_TAX_RATE_ID = rate.id
    return rate.id


def get_or_create_customer(user: User) -> str:
    """Devuelve stripe_customer_id; lo crea si no existe."""
    _configure()
    if user.stripe_customer_id:
        return user.stripe_customer_id
    customer = stripe.Customer.create(
        email=user.email,
        name=user.full_name or None,
        phone=user.phone or None,
        metadata={"user_id": str(user.id), "app": _app()},
    )
    return customer.id


def create_checkout_session(
    user: User, plan: PlanTier, success_url: str, cancel_url: str, founder: bool = False
) -> tuple[str, str]:
    """Crea sesión de checkout con cobro inmediato (sin trial). Devuelve (URL, customer_id)."""
    _configure()
    price_id = get_price_id(plan, founder)
    if not price_id:
        raise ValueError(
            f"Price ID no configurado para plan {plan} (founder={founder}). "
            "Ejecuta ensure_products_and_prices()."
        )

    customer_id = user.stripe_customer_id or get_or_create_customer(user)
    vat_id = _find_or_create_vat_tax_rate()

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1, "tax_rates": [vat_id]}],
        subscription_data={
            "metadata": {
                "user_id": str(user.id),
                "growth_plan": plan,
                "founder": "true" if founder else "false",
                "app": _app(),
            },
        },
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": str(user.id),
            "growth_plan": plan,
            "founder": "true" if founder else "false",
            "app": _app(),
        },
    )
    return session.url, customer_id


def create_portal_session(customer_id: str, return_url: str) -> str:
    _configure()
    session = stripe.billing_portal.Session.create(customer=customer_id, return_url=return_url)
    return session.url


def parse_webhook(payload: bytes, sig_header: str) -> stripe.Event:
    """Verifica firma y devuelve Event."""
    _configure()
    return stripe.Webhook.construct_event(
        payload=payload,
        sig_header=sig_header,
        secret=settings.STRIPE_WEBHOOK_SECRET,
    )


def plan_from_subscription(subscription: dict) -> str | None:
    """Extrae el tier de una subscription a partir del price.metadata.
    Reconoce tanto los tiers de plataforma como los planes Research Mode."""
    items = subscription.get("items", {}).get("data", [])
    for item in items:
        price = item.get("price", {})
        meta = price.get("metadata") or {}
        plan = meta.get("growth_plan")
        if plan in PLAN_DEFS or plan in RESEARCH_PLAN_DEFS:
            return plan
    return None


def subscription_belongs_to_app(sub: dict) -> bool:
    """True si la subscription es de esta app (por metadata.app o el price)."""
    if belongs_to_app(sub.get("metadata")):
        return True
    # Fallback: mira el metadata del price de cada item (lo marcamos con `app`).
    for item in sub.get("items", {}).get("data", []):
        if belongs_to_app((item.get("price") or {}).get("metadata")):
            return True
    return False


def invoice_belongs_to_app(invoice: dict) -> bool:
    """True si el invoice corresponde a una suscripción de esta app.

    Los invoices no llevan nuestro metadata directamente, pero sí el price de
    cada línea (que marcamos con `app`). También aceptamos metadata propio del
    invoice/subscription_details por si Stripe lo propaga.
    """
    if belongs_to_app(invoice.get("metadata")):
        return True
    sub_details = invoice.get("subscription_details") or {}
    if belongs_to_app(sub_details.get("metadata")):
        return True
    for line in (invoice.get("lines") or {}).get("data", []):
        if belongs_to_app((line.get("price") or {}).get("metadata")):
            return True
        if belongs_to_app(line.get("metadata")):
            return True
    return False


def founder_from_subscription(subscription: dict) -> bool:
    """Indica si la subscription usa precio fundador."""
    items = subscription.get("items", {}).get("data", [])
    for item in items:
        meta = (item.get("price", {}).get("metadata") or {})
        if meta.get("founder") == "true":
            return True
    return False
