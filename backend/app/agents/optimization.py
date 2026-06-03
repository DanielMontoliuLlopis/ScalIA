"""OptimizationAgent — analiza campañas activas y genera recomendaciones accionables."""
import json
import math
from typing import Any

from app.agents.base import BaseAgent


# ── Multi-Angle: umbrales de señal mínima y significancia ───────────────────
MIN_IMPRESSIONS_PER_ANGLE = 3000   # impresiones mínimas antes de evaluar
MIN_SPEND_PER_ANGLE = 30           # € mínimo gastado antes de evaluar
SIGNIFICANCE_ALPHA = 0.05          # z-test de dos colas, p<0.05


def _normal_cdf(z: float) -> float:
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def two_proportion_ztest(c1: int, n1: int, c2: int, n2: int) -> float:
    """z-test de dos proporciones. Devuelve el p-value (dos colas).
    c=conversiones, n=muestras (impresiones o clicks)."""
    if n1 <= 0 or n2 <= 0:
        return 1.0
    p1, p2 = c1 / n1, c2 / n2
    p_pool = (c1 + c2) / (n1 + n2)
    denom = p_pool * (1 - p_pool) * (1 / n1 + 1 / n2)
    if denom <= 0:
        return 1.0
    z = (p1 - p2) / math.sqrt(denom)
    return 2 * (1 - _normal_cdf(abs(z)))


def is_significant(angle_a: dict, angle_b: dict, alpha: float = SIGNIFICANCE_ALPHA) -> bool:
    """True solo si la diferencia de conversión (conversions/impressions) entre
    dos ángulos es estadísticamente concluyente al nivel alpha."""
    n1 = int(angle_a.get("impressions") or 0)
    n2 = int(angle_b.get("impressions") or 0)
    c1 = int(angle_a.get("conversions") or angle_a.get("clicks") or angle_a.get("leads") or 0)
    c2 = int(angle_b.get("conversions") or angle_b.get("clicks") or angle_b.get("leads") or 0)
    return two_proportion_ztest(c1, n1, c2, n2) < alpha


SYSTEM_PROMPT = """Eres un experto en optimización de campañas Meta Ads.
Recibes métricas de una campaña activa y debes generar recomendaciones concretas y accionables.

REGLAS:
- Máximo 3 recomendaciones por campaña
- Cada recomendación debe tener tipo, razonamiento claro y payload de acción específico
- Prioriza por impacto potencial en ROAS y CPL
- Sé directo: di exactamente qué cambiar y por qué

Tipos de recomendación válidos:
- budget_increase: aumentar presupuesto diario
- budget_decrease: reducir presupuesto (desperdicio detectado)
- copy_refresh: renovar copies del anuncio
- audience_expand: ampliar targeting
- audience_narrow: restringir targeting (CTR bajo en segmentos)
- bid_adjustment: cambiar estrategia de puja
- pause_variant: pausar variante A o B que bajo rendimiento
- pause_campaign: pausar campaña completa (señales muy negativas)

Responde en JSON con esta estructura exacta:
{
  "recommendations": [
    {
      "type": "budget_increase",
      "reasoning": "El CPL está 40% por debajo del objetivo con ROAS de 3.2x. Aumentar presupuesto capturará más demanda calificada.",
      "action_payload": {
        "current_daily_eur": 10.0,
        "suggested_daily_eur": 15.0,
        "change_pct": 50
      },
      "priority": "high"
    }
  ]
}"""


class OptimizationAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(model="gpt-4o")
        self.system_prompt = SYSTEM_PROMPT

    def _apply_deterministic_rules(
        self,
        meta: dict,
        funnel: dict,
    ) -> list[dict]:
        """Reglas rápidas sin LLM. Generan alertas inmediatas."""
        rules: list[dict] = []

        ctr = float(meta.get("ctr") or 0)
        cpm = float(meta.get("cpm") or 0)
        spend = float(meta.get("spend") or 0)
        impressions = int(meta.get("impressions") or 0)
        leads = int(funnel.get("total_leads") or 0)
        roas = funnel.get("roas")

        # CTR bajo (< 0.5%) con suficiente tráfico
        if ctr < 0.5 and impressions > 5000:
            rules.append({
                "type": "copy_refresh",
                "reasoning": f"CTR de {ctr:.2f}% está por debajo del umbral mínimo (0.5%) con {impressions:,} impresiones. El copy no está resonando con la audiencia.",
                "action_payload": {
                    "metric": "ctr",
                    "current_value": ctr,
                    "threshold": 0.5,
                    "impressions": impressions,
                },
                "priority": "high",
            })

        # CPM muy alto (> €25) — audiencia saturada
        if cpm > 25 and spend > 50:
            rules.append({
                "type": "audience_expand",
                "reasoning": f"CPM de €{cpm:.2f} indica audiencia saturada o competencia alta. Expandir targeting reducirá el coste por mil impresiones.",
                "action_payload": {
                    "metric": "cpm",
                    "current_value": cpm,
                    "threshold": 25.0,
                },
                "priority": "medium",
            })

        # ROAS excelente (> 3x) con poco presupuesto
        if roas and float(roas) > 3.0 and spend < 300:
            rules.append({
                "type": "budget_increase",
                "reasoning": f"ROAS de {float(roas):.1f}x es excelente. Aumentar presupuesto capturará más demanda calificada con el mismo retorno.",
                "action_payload": {
                    "metric": "roas",
                    "current_value": float(roas),
                    "suggested_increase_pct": 50,
                },
                "priority": "high",
            })

        # Sin leads después de €50 gastados
        if spend > 50 and leads == 0:
            rules.append({
                "type": "pause_campaign",
                "reasoning": f"Se han gastado €{spend:.2f} sin capturar ningún lead. Revisar landing page, targeting y copy antes de continuar.",
                "action_payload": {
                    "metric": "leads",
                    "spend": spend,
                    "leads": leads,
                },
                "priority": "critical",
            })

        return rules

    def evaluate_angles(self, angles: list[dict]) -> tuple[list[dict], dict | None]:
        """Evalúa los ángulos en test (multi_angle). Marca el estado de cada uno
        (insufficient_data | inconclusive | winner | loser) tras señal mínima Y
        significancia estadística. Devuelve (ángulos_actualizados, recomendación|None).

        NUNCA declara ganador/perdedor sin superar el mínimo de señal ni sin que la
        diferencia sea concluyente — si no lo es, el estado es `inconclusive`."""
        updated = [dict(a) for a in angles]

        # 1. ¿Quién tiene señal suficiente?
        def _has_signal(a: dict) -> bool:
            return (int(a.get("impressions") or 0) >= MIN_IMPRESSIONS_PER_ANGLE
                    and float(a.get("spend") or 0) >= MIN_SPEND_PER_ANGLE)

        with_signal = [a for a in updated if _has_signal(a)]
        for a in updated:
            if not _has_signal(a):
                a["status"] = "insufficient_data"

        if len(with_signal) < 2:
            # Aún no hay suficientes ángulos con señal para comparar
            return updated, None

        # 2. Líder por CTR (proxy de conversión de mensaje)
        def _ctr(a: dict) -> float:
            imp = int(a.get("impressions") or 0)
            clk = int(a.get("conversions") or a.get("clicks") or a.get("leads") or 0)
            return (clk / imp) if imp else 0.0

        leader = max(with_signal, key=_ctr)
        winners, losers, inconclusive = [], [], []
        for a in with_signal:
            if a is leader:
                continue
            if is_significant(leader, a):
                a["status"] = "loser"
                losers.append(a["angle"])
            else:
                a["status"] = "inconclusive"
                inconclusive.append(a["angle"])

        # El líder solo es "winner" si vence de forma concluyente a alguien
        if losers:
            leader["status"] = "winner"
            winners = [leader["angle"]]
        else:
            leader["status"] = "inconclusive"
            inconclusive.append(leader["angle"])

        if not losers:
            reasoning = (
                f"Diferencia aún no concluyente entre ángulos ({', '.join(inconclusive)}). "
                f"Seguir testeando antes de redistribuir presupuesto."
            )
            rec = {
                "type": "angle_inconclusive",
                "reasoning": reasoning,
                "action_payload": {"winners": [], "losers": [], "inconclusive": inconclusive},
                "priority": "low",
            }
            return updated, rec

        # 3. Recomendar redistribución hacia ganadores + pausar perdedores
        leader_ctr = _ctr(leader) * 100
        avg_loser_ctr = (
            sum(_ctr(a) for a in with_signal if a["angle"] in losers) / max(1, len(losers))
        ) * 100
        reasoning = (
            f"Ángulo '{leader['angle']}': CTR {leader_ctr:.2f}% tras "
            f"{int(leader.get('impressions') or 0):,} impresiones, frente a "
            f"{avg_loser_ctr:.2f}% de media en {', '.join(losers)} — diferencia significativa "
            f"(p<{SIGNIFICANCE_ALPHA}). Concentrar presupuesto en el ganador y pausar perdedores."
        )
        rec = {
            "type": "angle_redistribute",
            "reasoning": reasoning,
            "action_payload": {
                "winners": winners,
                "losers": losers,
                "inconclusive": inconclusive,
                "action": "concentrate_budget_on_winners_pause_losers",
            },
            "priority": "high",
        }
        return updated, rec

    async def analyze(
        self,
        plan_id: str,
        plan_title: str,
        meta_insights: dict,
        funnel_metrics: dict,
        ads_output: dict | None,
        copy_output: dict | None,
    ) -> list[dict]:
        """Retorna lista de recomendaciones para esta campaña."""

        # 1. Reglas deterministas primero
        deterministic = self._apply_deterministic_rules(meta_insights, funnel_metrics)

        # Si ya tenemos recomendación crítica, no hace falta LLM
        has_critical = any(r.get("priority") == "critical" for r in deterministic)
        if has_critical:
            return deterministic[:3]

        # 2. Análisis LLM para recomendaciones más matizadas
        context = {
            "plan_id": plan_id,
            "campaign_title": plan_title,
            "meta_insights": {
                "spend": meta_insights.get("spend"),
                "impressions": meta_insights.get("impressions"),
                "clicks": meta_insights.get("clicks"),
                "ctr": meta_insights.get("ctr"),
                "cpm": meta_insights.get("cpm"),
                "cpc": meta_insights.get("cpc"),
                "cpp": meta_insights.get("cpp"),
                "reach": meta_insights.get("reach"),
                "frequency": meta_insights.get("frequency"),
            },
            "funnel_metrics": {
                "total_leads": funnel_metrics.get("total_leads"),
                "contacted": funnel_metrics.get("contacted"),
                "showed_up": funnel_metrics.get("showed_up"),
                "closed": funnel_metrics.get("closed"),
                "cpl_real": funnel_metrics.get("cpl_real"),
                "cost_per_close": funnel_metrics.get("cost_per_close"),
                "roas": funnel_metrics.get("roas"),
                "revenue_attributed": funnel_metrics.get("revenue_attributed"),
            },
            "deterministic_alerts": deterministic,
        }

        # Añadir contexto de copy si hay
        if copy_output and copy_output.get("copies"):
            copies = copy_output["copies"][:2]
            context["current_copies"] = [
                {"angle": c.get("angle"), "headline": c.get("headline")}
                for c in copies
            ]

        messages = [
            {
                "role": "user",
                "content": f"Analiza esta campaña y genera recomendaciones accionables:\n\n{json.dumps(context, indent=2, ensure_ascii=False)}",
            }
        ]

        try:
            raw = await self.run(messages, max_tokens=1024)
            # Limpiar si viene con markdown
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            parsed = json.loads(clean.strip())
            llm_recs = parsed.get("recommendations", [])
        except Exception:
            llm_recs = []

        # Merge: deterministic primero, luego LLM, sin duplicar tipos
        existing_types = {r["type"] for r in deterministic}
        merged = list(deterministic)
        for rec in llm_recs:
            if rec.get("type") not in existing_types:
                merged.append(rec)
                existing_types.add(rec.get("type", ""))

        return merged[:3]


async def run_optimization_for_plan(
    plan_id: str,
    user_id: str,
    db_session: Any,
) -> list[str]:
    """Ejecuta el agente y persiste las recomendaciones en DB. Retorna IDs creados."""
    import uuid as uuid_mod
    from sqlalchemy import select
    from app.models.plan import Plan
    from app.models.recommendation import Recommendation
    from app.models.task import AgentTask
    from app.models.user_settings import UserSettings

    plan = db_session.execute(
        select(Plan).where(Plan.id == uuid_mod.UUID(plan_id))
    ).scalar_one_or_none()
    if not plan or plan.status != "done":
        return []

    # Solo campañas con meta_campaign_id publicada
    if not plan.meta_campaign_id:
        return []

    settings = db_session.execute(
        select(UserSettings).where(UserSettings.client_account_id == plan.client_account_id)
    ).scalar_one_or_none()

    meta_insights: dict = {}
    if settings and settings.meta_access_token:
        try:
            import asyncio
            from app.tools.meta_ads import get_campaign_insights
            meta_insights = asyncio.run(
                get_campaign_insights(settings.meta_access_token, plan.meta_campaign_id)
            ) or {}
        except Exception:
            pass

    # Calcular funnel metrics desde DB
    from app.models.lead import Lead
    from sqlalchemy import func as sqlfunc
    leads_rows = db_session.execute(
        select(Lead).where(Lead.plan_id == uuid_mod.UUID(plan_id))
    ).scalars().all()

    total = len(leads_rows)
    showed_up = sum(1 for l in leads_rows if getattr(l, "lead_status", None) in ("showed_up", "closed"))
    closed = sum(1 for l in leads_rows if getattr(l, "lead_status", None) == "closed")
    revenue = sum(float(l.closed_value) for l in leads_rows if getattr(l, "closed_value", None) is not None)
    spend = float(meta_insights.get("spend") or 0)
    roas = (revenue / spend) if spend and revenue else None
    cpl_real = (spend / total) if total and spend else None

    funnel_metrics = {
        "total_leads": total,
        "showed_up": showed_up,
        "closed": closed,
        "revenue_attributed": revenue,
        "roas": roas,
        "cpl_real": cpl_real,
    }

    tasks = db_session.execute(
        select(AgentTask).where(
            AgentTask.plan_id == uuid_mod.UUID(plan_id),
            AgentTask.agent_name.in_(["CopyAgent", "AdsAgent"]),
            AgentTask.status == "completed",
        )
    ).scalars().all()
    ads_output = next((t.output for t in tasks if t.agent_name == "AdsAgent"), None)
    copy_output = next((t.output for t in tasks if t.agent_name == "CopyAgent"), None)

    agent = OptimizationAgent()

    import asyncio as asyncio_mod

    loop = asyncio_mod.new_event_loop()
    try:
        recommendations = loop.run_until_complete(
            agent.analyze(
                plan_id=plan_id,
                plan_title=plan.title,
                meta_insights=meta_insights,
                funnel_metrics=funnel_metrics,
                ads_output=ads_output,
                copy_output=copy_output,
            )
        )
    finally:
        loop.close()

    # ── Offer Testing (Capa 5): consolidar la oferta ganadora ────────────
    offer_rec = _offer_test_consolidation(db_session, plan)
    if offer_rec:
        recommendations = [offer_rec] + list(recommendations)

    # ── Multi-Angle: evaluar ángulos + regla angle_redistribute ──────────
    if (plan.ab_mode or "ab_classic") == "multi_angle" and plan.angles_tested:
        updated_angles, angle_rec = agent.evaluate_angles(plan.angles_tested)
        plan.angles_tested = updated_angles
        if angle_rec:
            recommendations = [angle_rec] + list(recommendations)
        # Escribir histórico al consolidar (hay ganador/perdedor definidos)
        consolidated = any(a.get("status") in ("winner", "loser") for a in updated_angles)
        if consolidated:
            _write_angle_performance(
                db_session, plan, user_id, updated_angles, spend_total=spend
            )

    created_ids: list[str] = []
    for rec in recommendations:
        obj = Recommendation(
            plan_id=uuid_mod.UUID(plan_id),
            user_id=uuid_mod.UUID(user_id),
            client_account_id=plan.client_account_id,
            type=rec.get("type", "copy_refresh"),
            reasoning=rec.get("reasoning", ""),
            action_payload=rec.get("action_payload", {}),
            status="pending",
        )
        db_session.add(obj)
        db_session.flush()
        created_ids.append(str(obj.id))

    db_session.commit()
    return created_ids


OFFER_TEST_MIN_LEADS = 20  # leads combinados mínimos antes de recomendar consolidar


def _offer_test_consolidation(db_session: Any, plan: Any) -> dict | None:
    """Si el plan participa en un test de oferta (A vs B), tras señal mínima
    compara y recomienda consolidar la oferta ganadora. Propone, no ejecuta."""
    import uuid as uuid_mod
    from sqlalchemy import select
    from app.models.plan import Plan
    from app.models.lead import Lead

    root_id = plan.parent_plan_id or plan.id
    variants = db_session.execute(
        select(Plan).where((Plan.id == root_id) | (Plan.parent_plan_id == root_id))
    ).scalars().all()
    if len(variants) < 2:
        return None

    # Solo el plan raíz dispara la recomendación (evita duplicar por variante)
    if plan.id != root_id:
        return None

    stats = []
    total_leads = 0
    for v in variants:
        leads = db_session.execute(
            select(Lead).where(Lead.plan_id == v.id)
        ).scalars().all()
        n = len(leads)
        closed = sum(1 for l in leads if getattr(l, "lead_status", None) == "closed")
        revenue = sum(float(l.closed_value) for l in leads if getattr(l, "closed_value", None) is not None)
        total_leads += n
        # Matriz ángulo × oferta: mejor ángulo de esta variante (si es multi_angle)
        best_angle = None
        if (v.ab_mode or "ab_classic") == "multi_angle" and v.angles_tested:
            ranked = sorted(
                v.angles_tested,
                key=lambda a: (
                    a.get("status") == "winner",
                    (int(a.get("clicks") or a.get("conversions") or 0) / int(a.get("impressions") or 1)),
                ),
                reverse=True,
            )
            best_angle = ranked[0].get("angle") if ranked else None
        stats.append({
            "plan_id": str(v.id),
            "label": v.offer_test_label or ("Oferta A" if v.id == root_id else "Oferta B"),
            "leads": n,
            "closed": closed,
            "revenue": revenue,
            "transformacion": v.transformacion,
            "best_angle": best_angle,
        })

    if total_leads < OFFER_TEST_MIN_LEADS:
        return None

    # Ganador por leads (proxy simple); desempate por revenue
    winner = max(stats, key=lambda s: (s["leads"], s["revenue"]))
    loser = min(stats, key=lambda s: (s["leads"], s["revenue"]))
    if winner["plan_id"] == loser["plan_id"]:
        return None

    reasoning = (
        f"Test de oferta con {total_leads} leads acumulados. '{winner['label']}' "
        f"({winner['leads']} leads, {winner['closed']} cierres) supera a '{loser['label']}' "
        f"({loser['leads']} leads, {loser['closed']} cierres). Consolidar presupuesto en la ganadora."
    )
    # Matriz ángulo × oferta: si la oferta ganadora es multi_angle, recomendar la
    # combinación ganadora (ángulo, oferta), no solo la oferta.
    combo = None
    if winner.get("best_angle"):
        combo = {"angle": winner["best_angle"], "offer": winner["label"]}
        reasoning += (
            f" Combinación ganadora: ángulo '{winner['best_angle']}' × oferta "
            f"'{winner['label']}'. Escalar esa pareja."
        )
    return {
        "type": "offer_test_consolidate",
        "reasoning": reasoning,
        "action_payload": {
            "winner_plan_id": winner["plan_id"],
            "loser_plan_id": loser["plan_id"],
            "winner_label": winner["label"],
            "winning_combo": combo,
            "action": "consolidate_budget_on_winner",
        },
        "priority": "high",
    }


def _write_angle_performance(
    db_session: Any, plan: Any, user_id: str, angles: list[dict], spend_total: float
) -> None:
    """Persiste el resultado por ángulo en angle_performance (histórico defendible).
    No duplica: borra filas previas de este plan antes de reescribir."""
    import uuid as uuid_mod
    from datetime import datetime, timezone
    from sqlalchemy import delete, select
    from app.models.angle_performance import AnglePerformance
    from app.models.client_account import ClientAccount

    business_type = next(
        (s.get("business_type") for s in (plan.steps or []) if s.get("business_type")), None
    ) or "saas"

    # account_id = owner del client_account (agregación por agencia)
    account_id = None
    ca = db_session.execute(
        select(ClientAccount).where(ClientAccount.id == plan.client_account_id)
    ).scalar_one_or_none()
    if ca:
        account_id = ca.owner_id

    db_session.execute(
        delete(AnglePerformance).where(AnglePerformance.plan_id == plan.id)
    )

    now = datetime.now(timezone.utc)
    for a in angles:
        status = a.get("status")
        if status not in ("winner", "loser", "inconclusive"):
            continue
        impressions = int(a.get("impressions") or 0)
        clicks = int(a.get("clicks") or a.get("conversions") or 0)
        leads = int(a.get("leads") or 0)
        spend = float(a.get("spend") or 0)
        ctr = (clicks / impressions) if impressions else None
        cpl = (spend / leads) if leads else None
        db_session.add(AnglePerformance(
            user_id=uuid_mod.UUID(user_id),
            account_id=account_id,
            plan_id=plan.id,
            business_type=business_type,
            angle=a.get("angle", ""),
            tipo_oferta=plan.tipo_oferta,
            impressions=impressions,
            clicks=clicks,
            leads=leads,
            spend=spend,
            ctr=ctr,
            cpl=cpl,
            roas=a.get("roas"),
            result=status,
            period_start=plan.created_at or now,
            period_end=now,
        ))
