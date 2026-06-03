import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_active_client_account, get_current_user
from app.database import get_db
from app.models.client_account import ClientAccount
from app.models.plan import Plan, PlanStatus
from app.models.task import AgentTask, TaskStatus
from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.plan import PlanResponse, RejectRequest, AgentTaskResponse, ResumeCopyRequest, ResumeAdsRequest, PublishMetaResponse, FunnelChoiceRequest, CreativeChoiceRequest, OfferTestRequest, ResearchGenerateRequest, CampaignWizardRequest
from app.pubsub import async_publish_event
from app.services import permissions

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("", response_model=list[PlanResponse])
async def list_plans(
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> list[Plan]:
    result = await db.execute(
        select(Plan).where(Plan.client_account_id == client_account.id).order_by(Plan.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> Plan:
    result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.post("/wizard", response_model=PlanResponse, status_code=201)
async def create_campaign_from_wizard(
    body: CampaignWizardRequest,
    current_user: User = Depends(permissions.require_action("create_campaign")),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> Plan:
    """Crea una campaña desde el wizard visual (reemplaza el chat).
    Reúne el briefing estructurado y deja que el OrchestratorAgent (allow_clarification=False)
    infiera los campos de marketing y construya el plan en un solo turno."""
    # Tope de campañas del tier (incluye en progreso)
    await permissions.assert_can_create_campaign(db, current_user)

    # Negocio: del body (override) o de Settings del workspace activo
    settings_result = await db.execute(
        select(UserSettings).where(UserSettings.client_account_id == client_account.id)
    )
    user_settings = settings_result.scalar_one_or_none()
    business_description = body.business_description or (user_settings.business_description if user_settings else None)
    business_type = body.business_type or (user_settings.business_type if user_settings else None)
    if not business_description or not business_type:
        raise HTTPException(
            status_code=422,
            detail="Completa el perfil de tu empresa (descripción y tipo) en Ajustes antes de crear una campaña.",
        )

    company_profile = {
        "missing": [],
        "company_name": user_settings.company_name if user_settings else "",
        "business_description": business_description,
        "business_type": business_type,
    }

    # Briefing sintético: el wizard ya recogió todas las respuestas, así que el
    # Orchestrator no necesita preguntar — solo inferir y crear el plan.
    url_line = f"\n- Enlace de la acción (Calendly/trial/pricing): {body.post_conversion_url}" if body.post_conversion_url else ""
    briefing = (
        "Quiero crear una campaña. Estos son los datos del briefing:\n"
        f"- Negocio: {business_description}\n"
        f"- Tipo de negocio: {business_type}\n"
        f"- Audiencia / cliente objetivo: {body.target_customer}\n"
        f"- Ubicación para anunciarme: {body.location}\n"
        f"- Presupuesto mensual: {body.monthly_budget}€\n"
        f"- Precio del producto/servicio: {body.precio_base}€\n"
        f"- Resultado concreto que consigue el cliente (transformación): {body.transformacion}\n"
        f"- Garantía: {body.garantia or 'ninguna'}\n"
        f"- Qué quiero que haga el cliente tras contactar: {body.post_conversion_action}{url_line}\n"
        "Crea el plan ahora con esta información, infiriendo lo que falte."
    )

    from app.agents.orchestrator import OrchestratorAgent
    agent = OrchestratorAgent(
        db=db,
        user_id=current_user.id,
        client_account_id=client_account.id,
        allow_clarification=False,
        company_profile=company_profile,
    )
    await agent.run([{"role": "user", "content": briefing}])
    plan_id = agent.created_plan_id
    if not plan_id:
        raise HTTPException(status_code=502, detail="No se pudo generar el plan. Inténtalo de nuevo.")

    await db.commit()

    result = await db.execute(select(Plan).where(Plan.id == uuid.UUID(plan_id)))
    plan = result.scalar_one()

    await async_publish_event(str(current_user.id), {"type": "new_plan", "plan_id": plan_id})
    return plan


@router.post("/research", response_model=PlanResponse, status_code=201)
async def generate_research_plan(
    body: ResearchGenerateRequest,
    current_user: User = Depends(permissions.require_feature("research_export")),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> Plan:
    """Lanza un research desde la librería: corre ResearchAgent → CopyAgent (multi-angle)
    directamente y deja el plan en research_view. No pasa por chat/funnel/creative-choice."""
    # Negocio: del body (override) o de Settings del workspace activo
    settings_result = await db.execute(
        select(UserSettings).where(UserSettings.client_account_id == client_account.id)
    )
    user_settings = settings_result.scalar_one_or_none()
    business_description = body.business_description or (user_settings.business_description if user_settings else None)
    business_type = body.business_type or (user_settings.business_type if user_settings else None)
    if not business_description or not business_type:
        raise HTTPException(
            status_code=422,
            detail="Completa el perfil de tu empresa (descripción y tipo) en Ajustes antes de generar research.",
        )

    target_customer = (body.target_customer or "").strip()
    if not target_customer:
        raise HTTPException(status_code=422, detail="Indica la audiencia objetivo.")

    # Cada research descuenta 1 escaneo del saldo mensual (402 si no hay saldo)
    await permissions.consume_scan(db, current_user)

    # Ángulos prioritarios por histórico (feedback loop), si hay datos para este business_type
    priority_angles = await _recommended_angles(db, current_user, business_type)

    common = {
        "business_description": business_description,
        "business_type": business_type,
        "target_customer": target_customer,
        "post_conversion_goal": "thank_you_only",
        "post_conversion_url": "",
        "objective": body.objective or "",
    }
    steps = [
        {
            **common,
            "order": 1,
            "agent": "ResearchAgent",
            "action": "research",
            "description": "Investiga pain points reales, ICP y 6 ángulos de copy",
            "estimated_time": "2 min",
        },
        {
            **common,
            "order": 2,
            "agent": "CopyAgent",
            "action": "generate_multi_angle_copy",
            "description": "Genera un copy + imagen propia por cada ángulo",
            "estimated_time": "3 min",
            "ab_mode": "multi_angle",
            "num_angles": 6,
            "priority_angles": priority_angles,
        },
    ]

    plan = Plan(
        user_id=current_user.id,
        client_account_id=client_account.id,
        title=f"Research · {business_type} · {target_customer[:40]}",
        description=body.objective or "Research independiente (ICP + 6 ángulos)",
        steps=steps,
        status=PlanStatus.executing,
        research_export=True,
        ab_mode="multi_angle",
        num_angles=6,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    from app.workers.execution import generate_research
    generate_research.delay(str(plan.id))

    await async_publish_event(str(current_user.id), {"type": "new_plan", "plan_id": str(plan.id)})

    return plan


@router.post("/{plan_id}/approve", response_model=PlanResponse)
async def approve_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(permissions.require_action("create_campaign")),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> Plan:
    result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.status != PlanStatus.pending_approval:
        raise HTTPException(status_code=400, detail="Plan is not pending approval")

    plan.status = PlanStatus.approved
    await db.commit()
    await db.refresh(plan)

    from app.workers.execution import execute_plan
    execute_plan.delay(str(plan_id))

    await async_publish_event(str(current_user.id), {"type": "plan_approved", "plan_id": str(plan_id)})

    return plan


@router.post("/{plan_id}/reject", response_model=PlanResponse)
async def reject_plan(
    plan_id: uuid.UUID,
    body: RejectRequest,
    current_user: User = Depends(permissions.require_action("create_campaign")),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> Plan:
    result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.status != PlanStatus.pending_approval:
        raise HTTPException(status_code=400, detail="Plan is not pending approval")

    plan.status = PlanStatus.rejected
    plan.feedback = body.feedback
    await db.commit()
    await db.refresh(plan)
    return plan


@router.post("/{plan_id}/resume-copy", response_model=PlanResponse)
async def resume_after_copy(
    plan_id: uuid.UUID,
    body: ResumeCopyRequest,
    current_user: User = Depends(permissions.require_action("create_campaign")),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> Plan:
    result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.status != PlanStatus.pending_copy_approval:
        raise HTTPException(status_code=400, detail="Plan is not pending copy approval")

    plan.status = PlanStatus.approved
    await db.commit()
    await db.refresh(plan)

    from app.workers.execution import execute_plan_resume
    execute_plan_resume.delay(str(plan_id), body.next_step, body.selected_copy_indices)

    await async_publish_event(str(current_user.id), {"type": "plan_approved", "plan_id": str(plan_id)})

    return plan


@router.post("/{plan_id}/resume-ads", response_model=PlanResponse)
async def resume_after_ads(
    plan_id: uuid.UUID,
    body: ResumeAdsRequest,
    current_user: User = Depends(permissions.require_action("create_campaign")),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> Plan:
    result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.status != PlanStatus.pending_ads_approval:
        raise HTTPException(status_code=400, detail="Plan is not pending ads approval")

    plan.status = PlanStatus.approved
    await db.commit()
    await db.refresh(plan)

    from app.workers.execution import execute_plan_resume_ads
    execute_plan_resume_ads.delay(str(plan_id), body.next_step, body.campaign_edits)

    await async_publish_event(str(current_user.id), {"type": "plan_approved", "plan_id": str(plan_id)})

    return plan


def _build_funnel_steps(
    base_step: dict,
    funnel_type: str,
    sale_type: str | None,
    redirect_url: str | None,
) -> list[dict]:
    """Genera los steps que siguen tras la elección de funnel.

    base_step: plantilla con business_description, business_type, target_customer,
               post_conversion_goal, post_conversion_url ya inyectados.
    """
    common = {
        **base_step,
        "funnel_type": funnel_type,
        "sale_type": sale_type,
        "redirect_url": redirect_url,
    }

    if funnel_type == "instant_form":
        return [
            {**common, "agent": "AdsAgent", "action": "generate_lead_ad",
             "description": "Genera Lead Ad con formulario nativo Meta",
             "estimated_time": "2 min"},
        ]

    if funnel_type == "landing_direct":
        return [
            {**common, "agent": "LandingAgent", "action": "generate_landing_sale",
             "landing_subtype": "sale",
             "campaign_type": "direct_sale",
             "description": "Genera landing de venta directa (A/B)",
             "estimated_time": "3 min"},
            {**common, "agent": "AdsAgent", "action": "generate_campaign",
             "description": "Genera campaña Meta con 2 ads A/B",
             "estimated_time": "2 min"},
        ]

    if funnel_type == "external_url":
        # Sin LandingAgent — los ads apuntan directamente a redirect_url del cliente
        return [
            {**common, "agent": "AdsAgent", "action": "generate_campaign",
             "campaign_type": "direct_sale",
             "description": "Genera campaña Meta con 2 ads apuntando directo a la URL externa",
             "estimated_time": "2 min"},
        ]

    if funnel_type == "landing_lm":
        return [
            {**common, "agent": "LandingAgent", "action": "generate_landing_lm",
             "landing_subtype": "lm",
             "campaign_type": "lead_gen",
             "description": "Genera landing de captura lead magnet (A/B)",
             "estimated_time": "3 min"},
            {**common, "agent": "LeadMagnetAgent", "action": "generate_pdf",
             "description": "Genera PDF del lead magnet con IA",
             "estimated_time": "3 min"},
            {**common, "agent": "EmailAgent", "action": "generate_sequence",
             "description": "Genera secuencia 5 emails + WhatsApp + página gracias",
             "estimated_time": "3 min"},
            {**common, "agent": "CRMAgent", "action": "configure_scoring",
             "description": "Configura rubrica de scoring para leads",
             "estimated_time": "1 min"},
            {**common, "agent": "AdsAgent", "action": "generate_campaign",
             "description": "Genera campaña Meta apuntando a landings LM A/B",
             "estimated_time": "2 min"},
        ]

    if funnel_type == "landing_lm_direct":
        return [
            {**common, "agent": "LandingAgent", "action": "generate_landing_lm",
             "landing_subtype": "lm",
             "campaign_type": "lead_gen",
             "description": "Genera landing de captura lead magnet (A/B)",
             "estimated_time": "3 min"},
            {**common, "agent": "LandingAgent", "action": "generate_landing_sale",
             "landing_subtype": "sale",
             "campaign_type": "direct_sale",
             "description": "Genera landing de venta propia (A/B)",
             "estimated_time": "3 min"},
            {**common, "agent": "LeadMagnetAgent", "action": "generate_pdf",
             "description": "Genera PDF del lead magnet con IA",
             "estimated_time": "3 min"},
            {**common, "agent": "EmailAgent", "action": "generate_sequence",
             "description": "Genera secuencia 5 emails + WhatsApp + página gracias",
             "estimated_time": "3 min"},
            {**common, "agent": "CRMAgent", "action": "configure_scoring",
             "description": "Configura rubrica de scoring para leads",
             "estimated_time": "1 min"},
            {**common, "agent": "AdsAgent", "action": "generate_campaign",
             "description": "Genera campaña Meta apuntando a landings LM A/B",
             "estimated_time": "2 min"},
        ]

    return []


@router.post("/{plan_id}/funnel-choice", response_model=PlanResponse)
async def funnel_choice(
    plan_id: uuid.UUID,
    body: FunnelChoiceRequest,
    current_user: User = Depends(permissions.require_action("create_campaign")),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> Plan:
    result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.status != PlanStatus.awaiting_funnel_choice:
        raise HTTPException(status_code=400, detail=f"Plan no está esperando elección de funnel (status={plan.status})")

    # ── Salida temprana: solo research + ángulos, sin funnel ──────────
    if body.research_export:
        if not permissions.has_feature(current_user, "research_export"):
            raise HTTPException(
                status_code=403,
                detail=f"Tu plan ({permissions.tier_of(current_user)}) no incluye el modo Research. Mejora tu plan.",
            )
        plan.research_export = True
        plan.status = PlanStatus.research_view
        await db.commit()
        await db.refresh(plan)
        await async_publish_event(str(current_user.id), {
            "type": "plan_research_view",
            "plan_id": str(plan_id),
        })
        return plan

    valid_funnels = {"instant_form", "landing_direct", "landing_lm", "landing_lm_direct", "external_url"}
    if body.funnel_type not in valid_funnels:
        raise HTTPException(status_code=422, detail=f"funnel_type inválido. Válidos: {valid_funnels}")

    # Los funnels con lead magnet requieren email sequences + lead magnet (tier starter+)
    if body.funnel_type in {"landing_lm", "landing_lm_direct"}:
        for feat in ("email_sequences", "lead_magnet"):
            if not permissions.has_feature(current_user, feat):
                raise HTTPException(
                    status_code=403,
                    detail=(
                        f"Tu plan ({permissions.tier_of(current_user)}) no incluye '{feat}'. "
                        f"Mejora a Starter o superior para usar funnels con lead magnet."
                    ),
                )

    if body.funnel_type in {"landing_lm", "landing_lm_direct"}:
        if body.sale_type not in {"call", "payment"}:
            raise HTTPException(status_code=422, detail="sale_type requerido (call|payment) para funnels lead magnet")
        if not body.redirect_url:
            raise HTTPException(status_code=422, detail="redirect_url requerido (URL Calendly o de pago)")

    if body.funnel_type == "landing_direct" and not body.redirect_url:
        raise HTTPException(status_code=422, detail="redirect_url requerido para landing_direct (URL pricing/checkout)")

    if body.funnel_type == "external_url" and not body.redirect_url:
        raise HTTPException(status_code=422, detail="redirect_url requerido para external_url")

    # ── Modo de testeo: A/B clásico vs Multi-Angle ───────────────────
    ab_mode = body.ab_mode or "ab_classic"
    if ab_mode not in {"ab_classic", "multi_angle"}:
        raise HTTPException(status_code=422, detail="ab_mode inválido (ab_classic|multi_angle)")
    if ab_mode == "multi_angle":
        if not permissions.has_feature(current_user, "multi_angle"):
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Tu plan ({permissions.tier_of(current_user)}) no incluye Multi-Angle Testing. "
                    f"Mejora tu plan."
                ),
            )
        num_angles = body.num_angles or 3
        if not 2 <= num_angles <= 6:
            raise HTTPException(status_code=422, detail="num_angles debe estar entre 2 y 6")
        plan.num_angles = num_angles
    plan.ab_mode = ab_mode

    plan.funnel_type = body.funnel_type
    plan.sale_type = body.sale_type
    plan.redirect_url = body.redirect_url

    existing_steps = list(plan.steps or [])
    template_step: dict = {}
    for s in existing_steps:
        if s.get("business_description"):
            template_step = {
                "business_description": s.get("business_description"),
                "business_type": s.get("business_type"),
                "target_customer": s.get("target_customer"),
                "post_conversion_goal": s.get("post_conversion_goal"),
                "post_conversion_url": s.get("post_conversion_url"),
                "budget": s.get("budget", ""),
                **({"monthly_budget": s["monthly_budget"]} if s.get("monthly_budget") is not None else {}),
            }
            break

    new_steps_raw = _build_funnel_steps(
        template_step, body.funnel_type, body.sale_type, body.redirect_url
    )

    next_order = (max((s.get("order", 0) for s in existing_steps), default=0)) + 1
    appended = []
    angle_meta = {"ab_mode": ab_mode}
    if ab_mode == "multi_angle":
        angle_meta["num_angles"] = plan.num_angles
        # Feedback loop: priorizar ángulos con buen histórico para este business_type
        business_type = next(
            (s.get("business_type") for s in existing_steps if s.get("business_type")), None
        )
        priority_angles = await _recommended_angles(db, current_user, business_type)
        # En multi_angle regeneramos el copy: 1 copy + 1 imagen por ángulo.
        appended.append({
            **template_step, **angle_meta,
            "agent": "CopyAgent",
            "action": "generate_multi_angle_copy",
            "description": "Genera un copy + imagen propia por cada ángulo seleccionado",
            "estimated_time": "3 min",
            "priority_angles": priority_angles,
            "order": next_order,
        })
        next_order += 1
        # Validar cada ángulo por separado contra políticas de Meta
        appended.append({
            **template_step, **angle_meta,
            "agent": "MetaPolicyAgent",
            "action": "validate_angles",
            "description": "Valida y humaniza cada ángulo por separado",
            "estimated_time": "1 min",
            "order": next_order,
        })
        next_order += 1
    for new_s in new_steps_raw:
        appended.append({**new_s, **angle_meta, "order": next_order})
        next_order += 1

    plan.steps = existing_steps + appended
    plan.status = PlanStatus.executing
    await db.commit()
    await db.refresh(plan)

    from app.workers.execution import execute_plan_resume_funnel
    execute_plan_resume_funnel.delay(str(plan_id), len(existing_steps))

    await async_publish_event(str(current_user.id), {
        "type": "plan_funnel_chosen",
        "plan_id": str(plan_id),
        "funnel_type": body.funnel_type,
    })

    return plan


async def _recommended_angles(db: AsyncSession, user: User, business_type: str | None) -> list[str]:
    """Ordena los ángulos por win rate histórico para ese business_type (feedback loop).
    Devuelve solo los ángulos con histórico, de mejor a peor; [] si no hay datos."""
    if not business_type or not permissions.has_feature(user, "angle_history"):
        return []
    from app.models.angle_performance import AnglePerformance

    owner_id = permissions.account_owner_id(user)
    rows = await db.execute(
        select(AnglePerformance.angle, AnglePerformance.result).where(
            (AnglePerformance.user_id == user.id) | (AnglePerformance.account_id == owner_id),
            AnglePerformance.business_type == business_type,
        )
    )
    counts: dict[str, dict] = {}
    for angle, result in rows:
        c = counts.setdefault(angle, {"total": 0, "wins": 0})
        c["total"] += 1
        if result == "winner":
            c["wins"] += 1
    ranked = sorted(
        counts.items(),
        key=lambda kv: (kv[1]["wins"] / kv[1]["total"] if kv[1]["total"] else 0, kv[1]["total"]),
        reverse=True,
    )
    return [angle for angle, _ in ranked]


async def _gather_research(db: AsyncSession, plan: Plan) -> dict:
    """Reúne ICP + pain points + 6 ángulos (copy + imagen) desde las tasks."""
    res = await db.execute(
        select(AgentTask).where(
            AgentTask.plan_id == plan.id,
            AgentTask.agent_name == "ResearchAgent",
            AgentTask.status == "completed",
        ).order_by(AgentTask.created_at.desc())
    )
    research_task = res.scalars().first()
    res2 = await db.execute(
        select(AgentTask).where(
            AgentTask.plan_id == plan.id,
            AgentTask.agent_name == "CopyAgent",
            AgentTask.status == "completed",
        ).order_by(AgentTask.created_at.desc())
    )
    copy_task = res2.scalars().first()

    r_out = (research_task.output or {}) if research_task else {}
    c_out = (copy_task.output or {}) if copy_task else {}

    # ángulos del research (hook_example + rationale)
    research_angles = {a.get("angle"): a for a in (r_out.get("angles") or [])}
    # copies del copy agent (1 por ángulo en multi_angle), enriquecen con copy + imagen
    copies_by_angle: dict[str, dict] = {}
    for c in (c_out.get("copies") or []):
        ang = c.get("angle")
        if ang and ang not in copies_by_angle:
            copies_by_angle[ang] = c

    angle_names = ["dolor", "aspiracion", "miedo_urgencia", "social_proof", "curiosidad", "credibilidad"]
    angles = []
    for name in angle_names:
        ra = research_angles.get(name, {})
        ca = copies_by_angle.get(name, {})
        if not ra and not ca:
            continue
        angles.append({
            "angle": name,
            "hook": ca.get("hook") or ra.get("hook_example"),
            "copy": ca.get("body") or ra.get("rationale"),
            "image_url": ca.get("image_url"),
            "headline": ca.get("headline"),
        })

    return {
        "plan_id": plan.id,
        "business_type": next((s.get("business_type") for s in (plan.steps or []) if s.get("business_type")), None),
        "icp": r_out.get("icp"),
        "pain_points": r_out.get("pain_points") or [],
        "angles": angles,
        "audience_language": r_out.get("audience_language") or [],
        "export_url": plan.export_url,
    }


@router.get("/{plan_id}/research")
async def get_research(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    data = await _gather_research(db, plan)
    data["scans_remaining"] = current_user.scans_remaining
    # Histórico de ángulos por business_type (win rate)
    data["angle_history"] = []
    if permissions.has_feature(current_user, "angle_history") and data.get("business_type"):
        from app.models.angle_performance import AnglePerformance
        rows = await db.execute(
            select(AnglePerformance.angle, AnglePerformance.result).where(
                AnglePerformance.user_id == current_user.id,
                AnglePerformance.business_type == data["business_type"],
            )
        )
        counts: dict[str, dict] = {}
        for angle, res_val in rows:
            c = counts.setdefault(angle, {"total": 0, "wins": 0})
            c["total"] += 1
            if res_val == "winner":
                c["wins"] += 1
        data["angle_history"] = [
            {"angle": a, "total": c["total"],
             "win_rate": round(c["wins"] / c["total"] * 100) if c["total"] else 0}
            for a, c in counts.items()
        ]
    return data

# El export PDF se genera en el frontend (window.print de ResearchModeScreen "tal cual").
# Ya no hay endpoint /export ni dependencia de reportlab/Cloudinary para el research.


@router.post("/{plan_id}/creative-choice", response_model=PlanResponse)
async def creative_choice(
    plan_id: uuid.UUID,
    body: CreativeChoiceRequest,
    current_user: User = Depends(permissions.require_action("create_campaign")),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> Plan:
    result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.status != PlanStatus.awaiting_creative_choice:
        raise HTTPException(status_code=400, detail=f"Plan no está esperando elección de creativo (status={plan.status})")

    valid_types = {"image_ai", "image_upload", "video_upload", "reel_upload", "meta_post", "dco"}
    if body.creative_type not in valid_types:
        raise HTTPException(status_code=422, detail=f"creative_type inválido. Válidos: {valid_types}")

    # DCO e image_ai no requieren variantes A/B; otros sí
    if body.creative_type not in ("image_ai", "dco"):
        if not body.creative_a or not body.creative_b:
            raise HTTPException(status_code=422, detail="Se requieren ambas variantes A y B")
        for label, asset in (("A", body.creative_a), ("B", body.creative_b)):
            if body.creative_type == "meta_post":
                if not asset.post_id:
                    raise HTTPException(status_code=422, detail=f"Variante {label}: post_id obligatorio para meta_post")
            else:
                if not asset.url:
                    raise HTTPException(status_code=422, detail=f"Variante {label}: url obligatoria")

    plan.creative_type = body.creative_type
    plan.creative_a = body.creative_a.model_dump() if body.creative_a else None
    plan.creative_b = body.creative_b.model_dump() if body.creative_b else None
    plan.status = PlanStatus.executing
    await db.commit()
    await db.refresh(plan)

    from app.workers.execution import execute_plan_resume_creative
    execute_plan_resume_creative.delay(str(plan_id))

    await async_publish_event(str(current_user.id), {
        "type": "plan_creative_chosen",
        "plan_id": str(plan_id),
        "creative_type": body.creative_type,
    })

    return plan


@router.post("/{plan_id}/publish-meta", response_model=PublishMetaResponse)
async def publish_to_meta(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> PublishMetaResponse:
    plan_result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if plan.meta_campaign_id:
        raise HTTPException(status_code=409, detail=f"Ya publicado. campaign_id: {plan.meta_campaign_id}")

    # Permiso de rol + límite de campañas activas del tier
    if not permissions.can(current_user, "publish_campaign"):
        raise HTTPException(status_code=403, detail=f"Tu rol ({current_user.role}) no permite publicar campañas")
    await permissions.assert_can_publish_campaign(db, current_user)

    settings_result = await db.execute(
        select(UserSettings).where(UserSettings.client_account_id == client_account.id)
    )
    user_settings = settings_result.scalar_one_or_none()

    if not user_settings or not user_settings.meta_access_token:
        raise HTTPException(status_code=400, detail="Meta Access Token no configurado en Settings")
    if not user_settings.meta_ad_account_id:
        raise HTTPException(status_code=400, detail="Meta Ad Account ID no configurado en Settings")
    if not user_settings.meta_page_id:
        raise HTTPException(status_code=400, detail="Meta Page ID no configurado en Settings. Conecta tu página de Facebook.")

    ads_task_result = await db.execute(
        select(AgentTask).where(
            AgentTask.plan_id == plan_id,
            AgentTask.agent_name == "AdsAgent",
            AgentTask.status == TaskStatus.completed,
        )
    )
    ads_task = ads_task_result.scalar_one_or_none()
    if not ads_task or not ads_task.output:
        raise HTTPException(status_code=400, detail="AdsAgent no completado para este plan")

    campaign_json = ads_task.output.get("campaign_json")
    if not campaign_json:
        raise HTTPException(status_code=400, detail="campaign_json no encontrado en output del AdsAgent")

    from app.tools.meta_ads import publish_campaign, MetaAdsError
    try:
        company = user_settings.company_name or current_user.email or "Anunciante"
        result = await publish_campaign(
            access_token=user_settings.meta_access_token,
            ad_account_id=user_settings.meta_ad_account_id,
            campaign_json=campaign_json,
            dsa_beneficiary=company,
            dsa_payor=company,
            page_id=user_settings.meta_page_id or "",
        )
    except MetaAdsError as e:
        raise HTTPException(status_code=422, detail=f"Error Meta API: {e}")

    plan.meta_campaign_id = result["campaign_id"]
    await db.commit()

    return PublishMetaResponse(**result)


class OfferComparisonItem(BaseModel):
    plan_id: uuid.UUID
    title: str
    status: str
    is_offer_test: bool
    offer_test_label: str | None
    tipo_oferta: str | None
    urgencia: str | None
    garantia: str | None
    transformacion: str | None
    precio_base: float | None
    total_leads: int
    total_views: int
    total_conversions: int
    meta_campaign_id: str | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/{plan_id}/offer-test", response_model=PlanResponse)
async def create_offer_test(
    plan_id: uuid.UUID,
    body: OfferTestRequest,
    current_user: User = Depends(permissions.require_action("create_campaign")),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> Plan:
    """Creates a second campaign with an alternative offer (10% of original budget)."""
    from app.models.lead import Lead
    from sqlalchemy import func as sqlfunc

    result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )
    original = result.scalar_one_or_none()
    if not original:
        raise HTTPException(status_code=404, detail="Plan not found")

    if original.is_offer_test:
        raise HTTPException(status_code=400, detail="No se puede crear un test desde otro test")

    # Offer testing es feature de tier Growth+
    if not permissions.has_feature(current_user, "offer_testing"):
        raise HTTPException(
            status_code=403,
            detail=(
                f"Tu plan ({permissions.tier_of(current_user)}) no incluye testeo de ofertas. "
                f"Mejora a Growth o Agency."
            ),
        )

    # Extract monthly_budget from steps (first step that has it)
    monthly_budget = None
    for s in (original.steps or []):
        if s.get("monthly_budget") is not None:
            monthly_budget = s["monthly_budget"]
            break

    test_budget = round((monthly_budget or 300) * 0.10, 2)

    # Clone steps with 10% budget and new offer params
    new_steps = []
    for i, s in enumerate(original.steps or []):
        step = {**s, "order": i + 1}
        if monthly_budget is not None:
            step["monthly_budget"] = test_budget
        if body.transformacion:
            step["transformacion"] = body.transformacion
        new_steps.append(step)

    offer_label = body.offer_test_label or "Oferta B"
    test_plan = Plan(
        user_id=current_user.id,
        client_account_id=client_account.id,
        title=f"{original.title} [{offer_label}]",
        description=original.description,
        steps=new_steps,
        status=PlanStatus.pending_approval,
        ab_testing=original.ab_testing,
        funnel_type=original.funnel_type,
        sale_type=original.sale_type,
        redirect_url=original.redirect_url,
        creative_type=original.creative_type,
        creative_a=original.creative_a,
        creative_b=original.creative_b,
        # Offer fields: override with test values, fallback to original
        precio_base=body.precio_base if body.precio_base is not None else original.precio_base,
        tipo_oferta=body.tipo_oferta or original.tipo_oferta,
        urgencia=body.urgencia or original.urgencia,
        garantia=body.garantia or original.garantia,
        transformacion=body.transformacion or original.transformacion,
        # Offer testing metadata
        parent_plan_id=original.id,
        is_offer_test=True,
        offer_test_label=offer_label,
    )
    db.add(test_plan)
    await db.commit()
    await db.refresh(test_plan)

    await async_publish_event(str(current_user.id), {
        "type": "offer_test_created",
        "plan_id": str(test_plan.id),
        "parent_plan_id": str(original.id),
    })

    return test_plan


@router.get("/{plan_id}/offer-comparison", response_model=list[OfferComparisonItem])
async def offer_comparison(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Returns comparison data for a plan and all its offer test siblings."""
    from app.models.lead import Lead
    from sqlalchemy import func as sqlfunc

    result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    root_id = plan.parent_plan_id if plan.parent_plan_id else plan.id

    siblings_result = await db.execute(
        select(Plan).where(
            Plan.client_account_id == client_account.id,
            (Plan.id == root_id) | (Plan.parent_plan_id == root_id),
        ).order_by(Plan.created_at.asc())
    )
    siblings = siblings_result.scalars().all()

    from app.models.landing_page import LandingPage
    items = []
    for p in siblings:
        leads_count = (await db.execute(
            select(sqlfunc.count()).where(Lead.plan_id == p.id)
        )).scalar() or 0

        views_result = await db.execute(
            select(sqlfunc.sum(LandingPage.views), sqlfunc.sum(LandingPage.conversions))
            .where(LandingPage.plan_id == p.id)
        )
        row = views_result.one()
        total_views = row[0] or 0
        total_conversions = row[1] or 0

        items.append({
            "plan_id": p.id,
            "title": p.title,
            "status": p.status,
            "is_offer_test": p.is_offer_test,
            "offer_test_label": p.offer_test_label,
            "tipo_oferta": p.tipo_oferta,
            "urgencia": p.urgencia,
            "garantia": p.garantia,
            "transformacion": p.transformacion,
            "precio_base": float(p.precio_base) if p.precio_base is not None else None,
            "total_leads": leads_count,
            "total_views": total_views,
            "total_conversions": total_conversions,
            "meta_campaign_id": p.meta_campaign_id,
            "created_at": p.created_at,
        })

    return items


@router.get("/{plan_id}/tasks", response_model=list[AgentTaskResponse])
async def get_plan_tasks(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> list[AgentTask]:
    # Verify plan belongs to user
    plan_result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )
    if not plan_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Plan not found")

    result = await db.execute(
        select(AgentTask).where(AgentTask.plan_id == plan_id).order_by(AgentTask.created_at.asc())
    )
    return result.scalars().all()
