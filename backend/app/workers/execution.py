import asyncio
import json
import uuid
from typing import Any

import redis as redis_sync
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

from app.workers.celery_app import celery_app

CONTEXT_KEY = "plan_context:{plan_id}"
CONTEXT_TTL = 3600


def _get_sync_engine():
    from app.config import settings
    sync_url = settings.DATABASE_URL.replace(
        "postgresql+asyncpg://", "postgresql+psycopg2://"
    )
    return create_engine(sync_url, pool_pre_ping=True)


def _get_session() -> Session:
    engine = _get_sync_engine()
    SessionLocal = sessionmaker(engine)
    return SessionLocal()


def _save_context(plan_id: str, context: dict) -> None:
    from app.config import settings
    r = redis_sync.from_url(settings.REDIS_URL)
    r.setex(CONTEXT_KEY.format(plan_id=plan_id), CONTEXT_TTL, json.dumps(context))
    r.close()


def _load_context(plan_id: str) -> dict:
    from app.config import settings
    r = redis_sync.from_url(settings.REDIS_URL)
    data = r.get(CONTEXT_KEY.format(plan_id=plan_id))
    r.close()
    return json.loads(data) if data else {}


@celery_app.task(name="execute_plan", bind=True, max_retries=3)
def execute_plan(self, plan_id: str) -> dict:
    return _execute_plan_sync(plan_id, start_step=0)


@celery_app.task(name="execute_plan_resume", bind=True, max_retries=3)
def execute_plan_resume(self, plan_id: str, start_step: int, selected_copy_indices: list) -> dict:
    context = _load_context(plan_id)
    real_next_step = context.pop("__next_step", start_step)
    if "CopyAgent" in context and selected_copy_indices:
        copies = context["CopyAgent"].get("copies", [])
        context["CopyAgent"]["copies"] = [copies[i] for i in selected_copy_indices if i < len(copies)]
    return _execute_plan_sync(plan_id, start_step=real_next_step, context=context)


@celery_app.task(name="execute_plan_resume_ads", bind=True, max_retries=3)
def execute_plan_resume_ads(self, plan_id: str, start_step: int, campaign_edits: dict) -> dict:
    context = _load_context(plan_id)
    real_next_step = context.pop("__next_step", start_step)
    if "AdsAgent" in context and campaign_edits:
        context["AdsAgent"] = _apply_campaign_edits(context["AdsAgent"], campaign_edits)
    return _execute_plan_sync(plan_id, start_step=real_next_step, context=context)


@celery_app.task(name="execute_plan_resume_funnel", bind=True, max_retries=3)
def execute_plan_resume_funnel(self, plan_id: str, start_step: int) -> dict:
    """Resume after user picks funnel_type via /funnel-choice endpoint."""
    context = _load_context(plan_id)
    return _execute_plan_sync(plan_id, start_step=start_step, context=context)


@celery_app.task(name="execute_plan_resume_creative", bind=True, max_retries=3)
def execute_plan_resume_creative(self, plan_id: str) -> dict:
    """Resume after user picks creative_type via /creative-choice endpoint."""
    context = _load_context(plan_id)
    real_next_step = context.pop("__next_step", 0)
    return _execute_plan_sync(plan_id, start_step=real_next_step, context=context)


@celery_app.task(name="generate_research", bind=True, max_retries=2)
def generate_research(self, plan_id: str) -> dict:
    """Research independiente desde la librería: corre ResearchAgent → CopyAgent
    (multi-angle) y deja el plan en research_view. Sin pausas de creative/funnel/ads."""
    from app.models.plan import Plan, PlanStatus
    from app.models.task import AgentTask, TaskStatus
    from app.pubsub import publish_event

    db = _get_session()
    try:
        plan = db.execute(select(Plan).where(Plan.id == uuid.UUID(plan_id))).scalar_one_or_none()
        if not plan:
            return {"error": "Plan not found"}

        user_id = str(plan.user_id)
        plan.status = PlanStatus.executing
        db.commit()

        context: dict = {"__ab_mode": "multi_angle", "__num_angles": plan.num_angles or 6}
        publish_event(user_id, {"type": "plan_executing", "plan_id": plan_id})

        for step in (plan.steps or []):
            agent_name = step.get("agent", "unknown").removeprefix("functions.")
            task = AgentTask(
                plan_id=plan.id,
                agent_name=agent_name,
                tool_name=step.get("action", "unknown"),
                input=step,
                status=TaskStatus.running,
            )
            db.add(task)
            db.commit()
            task_id = str(task.id)
            publish_event(user_id, {
                "type": "task_update", "task_id": task_id,
                "status": "running", "agent": agent_name,
            })

            try:
                output = _run_agent_sync(
                    agent_name, step, context,
                    plan_id=str(plan.id), user_id=str(plan.user_id),
                )
                task.status = TaskStatus.completed
                task.output = output
                context[agent_name] = output
                # Renombrar el plan con el título derivado del research (no genérico)
                if agent_name == "ResearchAgent" and isinstance(output, dict):
                    new_title = (output.get("title") or "").strip()
                    if new_title:
                        plan.title = new_title[:120]
            except Exception as exc:
                db.rollback()
                task.status = TaskStatus.failed
                task.output = {"error": str(exc)}
            db.commit()

            publish_event(user_id, {
                "type": "task_update", "task_id": task_id,
                "status": task.status, "output": task.output,
            })

        plan.status = PlanStatus.research_view
        db.commit()
        publish_event(user_id, {"type": "plan_research_view", "plan_id": plan_id})
        return {"plan_id": plan_id, "status": "research_view"}
    finally:
        db.close()


@celery_app.task(name="generate_angle_images", bind=True, max_retries=2)
def generate_angle_images(self, plan_id: str, count: int = 2, angles: list[str] | None = None) -> dict:
    """Genera imágenes DALL-E para ángulos del research sin imagen. Si `angles` viene,
    genera exactamente esos; si no, los primeros `count`. Actualiza el output del
    CopyAgent y deja el plan en research_view. Se cobra 1 escaneo (en el endpoint)."""
    from sqlalchemy.orm.attributes import flag_modified

    from app.agents.copy import CopyAgent
    from app.models.plan import Plan, PlanStatus
    from app.models.task import AgentTask
    from app.pubsub import publish_event

    db = _get_session()
    try:
        plan = db.execute(select(Plan).where(Plan.id == uuid.UUID(plan_id))).scalar_one_or_none()
        if not plan:
            return {"error": "Plan not found"}
        user_id = str(plan.user_id)

        copy_task = db.execute(
            select(AgentTask).where(
                AgentTask.plan_id == plan.id,
                AgentTask.agent_name == "CopyAgent",
                AgentTask.status == "completed",
            ).order_by(AgentTask.created_at.desc())
        ).scalars().first()
        if not copy_task or not (copy_task.output or {}).get("copies"):
            return {"error": "No copies found"}

        copies = copy_task.output["copies"]
        pending = [c for c in copies if not c.get("image_url")]
        if angles:
            wanted = set(angles)
            pending = [c for c in pending if c.get("angle") in wanted]
        if not pending:
            publish_event(user_id, {"type": "plan_research_view", "plan_id": plan_id})
            return {"plan_id": plan_id, "status": "research_view", "generated": 0}

        # Datos de negocio desde el step del CopyAgent
        copy_step = next(
            (s for s in (plan.steps or []) if (s.get("agent", "")).endswith("CopyAgent")), {}
        )
        saas = copy_step.get("business_description") or plan.description or ""
        audience = copy_step.get("target_customer") or "audiencia objetivo"
        business_type = copy_step.get("business_type", "saas")

        # Con selección explícita generamos todos los pedidos; si no, los primeros `count`.
        targets = pending if angles else pending[: max(1, count)]
        agent = CopyAgent()

        async def _gen() -> None:
            for c in targets:
                c["image_url"] = await agent._generate_image_for_angle(
                    c, saas, audience, business_type, c.get("angle", "")
                )

        asyncio.run(_gen())

        flag_modified(copy_task, "output")
        plan.status = PlanStatus.research_view

        # Reembolso: el endpoint cobró ceil(pedidas/2). Solo se consume por lo que
        # realmente salió → devolvemos la diferencia en créditos si alguna falló.
        generated = sum(1 for c in targets if c.get("image_url"))
        charged = -(-len(targets) // 2)
        earned = -(-generated // 2)
        refund = charged - earned
        if refund > 0:
            from app.models.user import User
            user = db.execute(select(User).where(User.id == plan.user_id)).scalar_one_or_none()
            if user:
                user.scans_remaining += refund

        db.commit()
        publish_event(user_id, {"type": "plan_research_view", "plan_id": plan_id})
        return {"plan_id": plan_id, "status": "research_view", "generated": generated, "refunded": refund}
    finally:
        db.close()


def _apply_campaign_edits(ads_output: dict, edits: dict) -> dict:
    """Aplica los cambios del usuario al output del AdsAgent antes de continuar."""
    import copy as copy_mod
    result = copy_mod.deepcopy(ads_output)
    cj = result.get("campaign_json", {})

    if "campaign_name" in edits:
        cj.setdefault("campaign", {})["name"] = edits["campaign_name"]
    if "daily_budget_cents" in edits:
        cj.setdefault("campaign", {})["daily_budget"] = int(edits["daily_budget_cents"])
        result.setdefault("budget", {})["daily_cents"] = int(edits["daily_budget_cents"])
        result.setdefault("budget", {})["daily_eur"] = round(int(edits["daily_budget_cents"]) / 100, 2)
    if "age_min" in edits:
        cj.setdefault("ad_set", {}).setdefault("targeting", {})["age_min"] = int(edits["age_min"])
    if "age_max" in edits:
        cj.setdefault("ad_set", {}).setdefault("targeting", {})["age_max"] = int(edits["age_max"])
    if "countries" in edits:
        cj.setdefault("ad_set", {}).setdefault("targeting", {}).setdefault("geo_locations", {})["countries"] = edits["countries"]
    if "ad_a_message" in edits:
        cj.setdefault("ads", [{}, {}])[0].setdefault("creative", {}).setdefault("object_story_spec", {}).setdefault("link_data", {})["message"] = edits["ad_a_message"]
    if "ad_b_message" in edits:
        cj.setdefault("ads", [{}, {}])[1].setdefault("creative", {}).setdefault("object_story_spec", {}).setdefault("link_data", {})["message"] = edits["ad_b_message"]

    result["campaign_json"] = cj
    return result


def _execute_plan_sync(plan_id: str, start_step: int = 0, context: dict | None = None) -> dict:
    from app.models.plan import Plan, PlanStatus
    from app.models.task import AgentTask, TaskStatus
    from app.pubsub import publish_event

    accumulated_context: dict = context or {}

    db = _get_session()
    try:
        plan = db.execute(select(Plan).where(Plan.id == uuid.UUID(plan_id))).scalar_one_or_none()
        if not plan:
            return {"error": "Plan not found"}

        user_id = str(plan.user_id)
        plan.status = PlanStatus.executing
        db.commit()

        # ab_testing del plan se propaga a cada step en runtime (no se persiste)
        plan_ab_testing = bool(plan.ab_testing)
        accumulated_context["__ab_testing"] = plan_ab_testing
        # Modo de testeo Multi-Angle se propaga a CopyAgent y AdsAgent
        accumulated_context["__ab_mode"] = plan.ab_mode or "ab_classic"
        accumulated_context["__num_angles"] = plan.num_angles

        # Precargar meta settings del usuario en el contexto
        if "__meta_settings" not in accumulated_context:
            from app.models.user_settings import UserSettings
            us = db.execute(
                select(UserSettings).where(UserSettings.client_account_id == plan.client_account_id)
            ).scalar_one_or_none()
            if us:
                accumulated_context["__meta_settings"] = {
                    "meta_access_token": us.meta_access_token,
                    "meta_ad_account_id": us.meta_ad_account_id,
                    "meta_page_id": us.meta_page_id,
                    "meta_pixel_id": us.meta_pixel_id,
                }

        # Inyectar la elección de creativo del usuario en el contexto
        if plan.creative_type:
            accumulated_context["__creative_choice"] = {
                "creative_type": plan.creative_type,
                "creative_a": plan.creative_a,
                "creative_b": plan.creative_b,
            }

        # Pausa pre-Research si el usuario aún no eligió tipo de creativo
        if not plan.creative_type and start_step == 0:
            _save_context(plan_id, {**accumulated_context, "__next_step": 0})
            plan.status = PlanStatus.awaiting_creative_choice
            db.commit()
            publish_event(user_id, {
                "type": "plan_awaiting_creative_choice",
                "plan_id": plan_id,
                "next_step": 0,
            })
            return {"plan_id": plan_id, "status": "awaiting_creative_choice"}

        publish_event(user_id, {"type": "plan_executing", "plan_id": plan_id})

        steps = plan.steps or []
        for i, step in enumerate(steps):
            if i < start_step:
                continue

            agent_name = step.get("agent", "unknown").removeprefix("functions.")

            task = AgentTask(
                plan_id=plan.id,
                agent_name=agent_name,
                tool_name=step.get("action", "unknown"),
                input=step,
                status=TaskStatus.pending,
            )
            db.add(task)
            db.flush()
            task_id = str(task.id)

            task.status = TaskStatus.running
            db.commit()

            publish_event(user_id, {
                "type": "task_update",
                "task_id": task_id,
                "status": "running",
                "agent": agent_name,
            })

            try:
                step_enriched = {
                    **step,
                    "ab_testing": accumulated_context.get("__ab_testing", step.get("ab_testing", False)),
                    "ab_mode": step.get("ab_mode") or accumulated_context.get("__ab_mode", "ab_classic"),
                    "num_angles": step.get("num_angles") or accumulated_context.get("__num_angles"),
                }
                output = _run_agent_sync(agent_name, step_enriched, accumulated_context, plan_id=str(plan.id), user_id=str(plan.user_id))
                task.status = TaskStatus.completed
                task.output = output
                accumulated_context[agent_name] = output

                if agent_name == "LandingAgent" and output.get("variant_a"):
                    try:
                        landing_ids = _save_landings_sync(db, plan, step, output)
                        subtype = step.get("landing_subtype") or "lm"
                        # Acumular landing_ids por subtype (lm/sale) en el contexto
                        existing_landing = accumulated_context.get("LandingAgent", {})
                        existing_by_subtype = existing_landing.get("by_subtype", {})
                        existing_by_subtype[subtype] = {
                            "landing_ids": landing_ids,
                            "variant_a": output.get("variant_a"),
                            "variant_b": output.get("variant_b"),
                        }
                        task.output = {**output, "landing_ids": landing_ids, "landing_subtype": subtype}
                        accumulated_context[agent_name] = {
                            **task.output,
                            "by_subtype": existing_by_subtype,
                        }
                    except Exception as land_exc:
                        db.rollback()
                        print(f"[Worker] Error guardando landing: {land_exc}")

                if agent_name == "LeadMagnetAgent" and output.get("title"):
                    try:
                        lm_id = _save_lead_magnet_sync(db, plan, output)
                        task.output = {**output, "lead_magnet_id": lm_id}
                        accumulated_context[agent_name] = task.output
                    except Exception as lm_exc:
                        db.rollback()
                        print(f"[Worker] Error guardando lead magnet: {lm_exc}")

            except Exception as exc:
                db.rollback()
                task.status = TaskStatus.failed
                task.output = {"error": str(exc)}

            db.commit()

            publish_event(user_id, {
                "type": "task_update",
                "task_id": task_id,
                "status": task.status,
                "output": task.output,
            })

            if agent_name == "MetaPolicyAgent" and task.status == TaskStatus.completed:
                # Merge validated copies back into CopyAgent context so downstream agents use them
                if "CopyAgent" in accumulated_context and output.get("validated_copies"):
                    copy_ctx = dict(accumulated_context["CopyAgent"])
                    copy_ctx["copies"] = output["validated_copies"]
                    accumulated_context["CopyAgent"] = copy_ctx

            # La pausa de aprobación de copy solo ocurre en la fase inicial
            # (antes de elegir funnel). En multi_angle, la 2ª pasada de MetaPolicy
            # tras la elección de funnel NO vuelve a pausar — continúa hacia ads.
            if (
                agent_name == "MetaPolicyAgent"
                and task.status == TaskStatus.completed
                and not plan.funnel_type
            ):
                _save_context(plan_id, {**accumulated_context, "__next_step": i + 1})
                plan.status = PlanStatus.pending_copy_approval
                db.commit()
                publish_event(user_id, {
                    "type": "plan_pending_copy_approval",
                    "plan_id": plan_id,
                    "next_step": i + 1,
                    "meta_policy_summary": output.get("summary", {}),
                })
                return {"plan_id": plan_id, "status": "pending_copy_approval", "paused_at_step": i}

            if agent_name == "CopyAgent" and task.status == TaskStatus.completed:
                pass  # MetaPolicyAgent runs next and triggers the pause

            if agent_name == "AdsAgent" and task.status == TaskStatus.completed:
                # Persistir ángulos en test (multi_angle) para tracking posterior
                if output.get("angles_tested"):
                    plan.angles_tested = output["angles_tested"]
                _save_context(plan_id, {**accumulated_context, "__next_step": i + 1})
                plan.status = PlanStatus.pending_ads_approval
                db.commit()
                publish_event(user_id, {
                    "type": "plan_pending_ads_approval",
                    "plan_id": plan_id,
                    "next_step": i + 1,
                })
                return {"plan_id": plan_id, "status": "pending_ads_approval", "paused_at_step": i}

        # Si terminamos todos los steps y aún no hay funnel_type → pausa funnel_choice
        if not plan.funnel_type:
            _save_context(plan_id, {**accumulated_context, "__next_step": len(steps)})
            plan.status = PlanStatus.awaiting_funnel_choice
            db.commit()
            publish_event(user_id, {
                "type": "plan_awaiting_funnel_choice",
                "plan_id": plan_id,
                "next_step": len(steps),
            })
            return {"plan_id": plan_id, "status": "awaiting_funnel_choice"}

        plan.status = PlanStatus.done
        db.commit()

        publish_event(user_id, {"type": "plan_completed", "plan_id": plan_id})
        return {"plan_id": plan_id, "status": "done"}

    finally:
        db.close()


def _save_landings_sync(db: Session, plan: Any, step: dict, output: dict) -> dict:
    """Saves landing pages to DB and returns a dict with landing IDs."""
    from app.models.landing_page import LandingPage
    from app.models.user_settings import UserSettings

    user_settings = db.execute(
        select(UserSettings).where(UserSettings.client_account_id == plan.client_account_id)
    ).scalar_one_or_none()
    meta_pixel_id = user_settings.meta_pixel_id if user_settings else None
    logo_url = user_settings.logo_url if user_settings else None

    landing_subtype = step.get("landing_subtype") or output.get("landing_subtype")
    funnel_type = step.get("funnel_type")
    sale_type = step.get("sale_type")

    # Si subtype=sale, redirect_url viene del step (Calendly/pago)
    # Si subtype=lm, no hay redirect (entrega lead magnet)
    redirect_url = step.get("redirect_url") if landing_subtype != "lm" else None

    ids: dict[str, str] = {}
    variant_keys = ["variant_a"]
    if output.get("variant_b"):
        variant_keys.append("variant_b")
    for variant_key in variant_keys:
        variant_char = "a" if variant_key == "variant_a" else "b"
        variant_data = output.get(variant_key, {})
        if not variant_data:
            continue
        colors = variant_data.get("colors", {})
        landing = LandingPage(
            plan_id=plan.id,
            user_id=plan.user_id,
            client_account_id=plan.client_account_id,
            variant=variant_char,
            campaign_type=output.get("campaign_type", "lead_gen"),
            funnel_type=funnel_type,
            landing_subtype=landing_subtype,
            sale_type=sale_type,
            headline=variant_data.get("headline", ""),
            subheadline=variant_data.get("subheadline", ""),
            benefits=variant_data.get("benefits", []),
            cta_text=variant_data.get("cta_text", "Empieza gratis"),
            hero_image_url=variant_data.get("hero_image_url"),
            primary_color=colors.get("primary", "#6366f1"),
            secondary_color=colors.get("secondary", "#e0e7ff"),
            logo_url=logo_url,
            meta_pixel_id=meta_pixel_id,
            redirect_url=redirect_url,
            form_fields=variant_data.get("form_fields", []),
            sale_content=variant_data.get("sale_content"),
            template_id=output.get("template_id"),
        )
        db.add(landing)
        db.flush()
        ids[variant_char] = str(landing.id)
    return ids


def _save_lead_magnet_sync(db: Session, plan: Any, output: dict) -> str:
    """Saves lead magnet to DB and returns ID."""
    from app.models.lead_magnet import LeadMagnet

    lm = LeadMagnet(
        plan_id=plan.id,
        user_id=plan.user_id,
        client_account_id=plan.client_account_id,
        title=output.get("title", "Lead magnet"),
        subtitle=output.get("subtitle"),
        sections=output.get("sections", []),
        pdf_url=output.get("pdf_url"),
        pdf_html=output.get("pdf_html"),
    )
    db.add(lm)
    db.flush()
    return str(lm.id)


def _run_agent_sync(agent_name: str, step: dict, context: dict, plan_id: str = None, user_id: str = None) -> dict:
    """Ejecuta el agente en un nuevo event loop limpio."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run_agent_async(agent_name, step, context, plan_id, user_id))
    finally:
        loop.close()


async def _run_agent_async(agent_name: str, step: dict, context: dict, plan_id: str = None, user_id: str = None) -> dict:
    """Lógica async de los agentes — se ejecuta en un loop limpio por agente."""
    plan_uuid = uuid.UUID(plan_id) if plan_id else None
    user_uuid = uuid.UUID(user_id) if user_id else None

    if agent_name == "ResearchAgent":
        from app.agents.research import ResearchAgent
        creative_choice = context.get("__creative_choice") or {}
        meta_settings = context.get("__meta_settings") or {}
        enriched_step = {**step, **{
            "creative_type": creative_choice.get("creative_type"),
            "creative_a": creative_choice.get("creative_a"),
            "creative_b": creative_choice.get("creative_b"),
            "meta_access_token": meta_settings.get("meta_access_token"),
        }}
        agent = ResearchAgent(user_id=user_uuid, plan_id=plan_uuid, agent_name="ResearchAgent")
        return await agent.run_task(enriched_step)

    elif agent_name == "CopyAgent":
        from app.agents.copy import CopyAgent
        creative_choice = context.get("__creative_choice") or {}
        enriched_step = {**step, **{
            "creative_type": creative_choice.get("creative_type"),
            "creative_a": creative_choice.get("creative_a"),
            "creative_b": creative_choice.get("creative_b"),
        }}
        agent = CopyAgent(user_id=user_uuid, plan_id=plan_uuid, agent_name="CopyAgent")
        return await agent.run_task(enriched_step, context=context.get("ResearchAgent", {}))

    elif agent_name == "MetaPolicyAgent":
        from app.agents.meta_policy import MetaPolicyAgent
        agent = MetaPolicyAgent(user_id=user_uuid, plan_id=plan_uuid, agent_name="MetaPolicyAgent")
        return await agent.run_task(step, context=context)

    elif agent_name == "LandingAgent":
        from app.agents.landing import LandingAgent
        agent = LandingAgent(user_id=user_uuid, plan_id=plan_uuid, agent_name="LandingAgent")
        return await agent.run_task(step, context=context)

    elif agent_name == "AdsAgent":
        from app.agents.ads import AdsAgent
        meta_settings = context.get("__meta_settings", {})
        enriched_step = {**step, **{k: v for k, v in meta_settings.items() if v}}
        agent = AdsAgent(user_id=user_uuid, plan_id=plan_uuid, agent_name="AdsAgent")
        return await agent.run_task(enriched_step, context=context)

    elif agent_name == "CRMAgent":
        from app.agents.crm import CRMAgent
        agent = CRMAgent(user_id=user_uuid, plan_id=plan_uuid, agent_name="CRMAgent")
        return await agent.run_task(step, context=context)

    elif agent_name == "LeadMagnetAgent":
        from app.agents.lead_magnet import LeadMagnetAgent
        agent = LeadMagnetAgent(user_id=user_uuid, plan_id=plan_uuid, agent_name="LeadMagnetAgent")
        return await agent.run_task(step, context=context)

    elif agent_name == "EmailAgent":
        from app.agents.email import EmailAgent
        agent = EmailAgent(user_id=user_uuid, plan_id=plan_uuid, agent_name="EmailAgent")
        return await agent.run_task(step, context=context)

    return {"status": "pending_implementation", "agent": agent_name}
