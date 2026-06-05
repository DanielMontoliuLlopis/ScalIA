"""Validación de message match (hilo narrativo) — determinista, sin LLM.

El mayor asesino de campañas es el *message mismatch*: el anuncio promete X,
la landing dice Y, los emails hablan de Z. Esta validación comprueba que todas
las piezas comparten el hook del anuncio y que la urgencia de la oferta se
refleja en la landing de venta. Los warnings se muestran en el panel de
aprobación antes de publicar (CLAUDE.md → Narrative Thread).
"""
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.landing_page import LandingPage
from app.models.plan import Plan
from app.models.task import AgentTask

# Palabras vacías en español que no aportan señal al hook.
_STOPWORDS = {
    "para", "como", "pero", "porque", "cuando", "donde", "este", "esta", "esto",
    "esos", "esas", "tienes", "tiene", "tener", "hacer", "haces", "todo", "toda",
    "todos", "todas", "tuyo", "tuya", "tus", "sus", "más", "menos", "muy", "sin",
    "con", "los", "las", "del", "una", "uno", "que", "qué", "por", "and", "the",
    "your", "you", "con", "puedes", "puede", "ahora", "desde", "hasta", "sobre",
}

# Términos que indican urgencia explícita en el contenido de la landing.
_URGENCY_TERMS = [
    "hoy", "últim", "ultim", "plazas", "limitad", "solo quedan", "quedan",
    "cupo", "cierra", "deadline", "fecha límite", "fecha limite", "antes de",
    "expira", "caduca", "termina", "no te quedes", "última oportunidad",
    "bonus", "regalo por tiempo",
]


def _hook_keywords(hook: str) -> set[str]:
    """Extrae palabras con señal del hook (>3 chars, sin stopwords)."""
    words = re.findall(r"[a-záéíóúñü0-9]+", (hook or "").lower())
    return {w for w in words if len(w) > 3 and w not in _STOPWORDS}


def _text_has_any(text: str | None, keywords: set[str]) -> bool:
    if not text:
        return False
    low = text.lower()
    return any(k in low for k in keywords)


def _mentions_urgency(*texts: str | None) -> bool:
    blob = " ".join(t for t in texts if t).lower()
    return any(term in blob for term in _URGENCY_TERMS)


def check_message_match(
    hook: str,
    landings: list[LandingPage],
    emails: list[dict],
    urgencia: str | None,
) -> list[str]:
    """Comprueba que landings y emails reflejan el hook del anuncio.

    Devuelve una lista de warnings legibles (vacía = todo coherente).
    """
    warnings: list[str] = []
    keywords = _hook_keywords(hook)
    if not keywords:
        return warnings  # sin hook no se puede validar

    lm = [l for l in landings if l.landing_subtype == "lm"]
    sale = [l for l in landings if l.landing_subtype == "sale"]

    if lm and not any(_text_has_any(l.headline, keywords) for l in lm):
        warnings.append("La landing de captura no refleja el hook del anuncio.")

    if sale and not any(_text_has_any(l.headline, keywords) for l in sale):
        warnings.append("La landing de venta no refleja el hook del anuncio.")

    if urgencia and urgencia != "sin_urgencia" and sale:
        if not any(_mentions_urgency(l.headline, l.subheadline) for l in sale):
            warnings.append(
                "La oferta tiene urgencia pero la landing de venta no la menciona."
            )

    if emails:
        first = emails[0]
        combined = f"{first.get('subject', '')} {first.get('body_html', '')}"
        if not _text_has_any(combined, keywords):
            warnings.append("El primer email no retoma el hook del anuncio.")

    return warnings


def _latest_task(tasks: list[AgentTask], agent_name: str) -> AgentTask | None:
    matches = [t for t in tasks if t.agent_name == agent_name and t.status == "completed"]
    matches.sort(key=lambda t: t.created_at, reverse=True)
    return matches[0] if matches else None


def _resolve_hook(plan: Plan, copy_task: AgentTask | None) -> str:
    """El hook fuente de verdad: copy A en ab_classic, primer ángulo en multi_angle."""
    if plan.ab_mode == "multi_angle" and plan.angles_tested:
        for a in plan.angles_tested:
            if a.get("hook"):
                return a["hook"]
    out = (copy_task.output or {}) if copy_task else {}
    copies = out.get("copies") or []
    if copies:
        return copies[0].get("hook") or copies[0].get("headline") or ""
    return ""


def _collect_policy_warnings(policy_task: AgentTask | None) -> tuple[list[str], str | None]:
    """Reúne los problemas de política detectados por el MetaPolicyAgent."""
    if not policy_task or not policy_task.output:
        return [], None
    out = policy_task.output
    warnings: list[str] = []

    if out.get("rejection_reason"):
        warnings.append(out["rejection_reason"])

    for c in out.get("validated_copies", []):
        angle = c.get("angle") or c.get("hook") or ""
        prefix = f"[{angle}] " if angle else ""
        for issue in c.get("policy_issues_found", []):
            warnings.append(f"{prefix}{issue}")

    garantia = out.get("garantia_validation", {})
    for issue in garantia.get("issues_found", []):
        warnings.append(issue)

    targeting = out.get("targeting", {})
    for issue in targeting.get("issues_fixed", []):
        warnings.append(issue)

    # dedupe preservando orden
    seen: set[str] = set()
    deduped = [w for w in warnings if not (w in seen or seen.add(w))]
    return deduped, out.get("status")


async def gather_message_match(db: AsyncSession, plan: Plan) -> dict:
    """Reúne hook, landings y emails del plan y calcula warnings + política Meta."""
    tasks_res = await db.execute(
        select(AgentTask).where(AgentTask.plan_id == plan.id)
    )
    tasks = list(tasks_res.scalars().all())

    copy_task = _latest_task(tasks, "CopyAgent")
    email_task = _latest_task(tasks, "EmailAgent")
    policy_task = _latest_task(tasks, "MetaPolicyAgent")

    landings_res = await db.execute(
        select(LandingPage).where(LandingPage.plan_id == plan.id)
    )
    landings = list(landings_res.scalars().all())

    emails = (email_task.output or {}).get("emails", []) if email_task else []

    hook = _resolve_hook(plan, copy_task)
    warnings = check_message_match(hook, landings, emails, plan.urgencia)
    policy_warnings, policy_status = _collect_policy_warnings(policy_task)

    return {
        "hook": hook,
        "warnings": warnings,
        "policy_warnings": policy_warnings,
        "policy_status": policy_status,
    }
