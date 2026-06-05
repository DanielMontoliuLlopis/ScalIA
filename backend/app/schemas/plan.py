import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.plan import PlanStatus


class PlanStep(BaseModel):
    order: int
    agent: str
    action: str
    description: str


class PlanResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: str
    steps: list[Any]
    status: PlanStatus
    feedback: str | None = None
    funnel_type: str | None = None
    sale_type: str | None = None
    redirect_url: str | None = None
    creative_type: str | None = None
    creative_a: dict[str, Any] | None = None
    creative_b: dict[str, Any] | None = None
    ab_testing: bool = False
    ab_mode: str = "ab_classic"
    num_angles: int | None = None
    angles_tested: list[Any] | None = None
    research_export: bool = False
    export_url: str | None = None
    precio_base: float | None = None
    tipo_oferta: str | None = None
    urgencia: str | None = None
    garantia: str | None = None
    transformacion: str | None = None
    parent_plan_id: uuid.UUID | None = None
    is_offer_test: bool = False
    offer_test_label: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlanListItem(BaseModel):
    """Versión ligera para la lista `/plans`. Omite los JSONB pesados
    (`steps`, `creative_a`, `creative_b`, `angles_tested`) que ningún consumidor
    de la lista usa — PlanWorkspace pide el plan completo vía GET /plans/{id}."""
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: str
    status: PlanStatus
    feedback: str | None = None
    funnel_type: str | None = None
    sale_type: str | None = None
    redirect_url: str | None = None
    creative_type: str | None = None
    ab_testing: bool = False
    ab_mode: str = "ab_classic"
    num_angles: int | None = None
    research_export: bool = False
    export_url: str | None = None
    precio_base: float | None = None
    tipo_oferta: str | None = None
    urgencia: str | None = None
    garantia: str | None = None
    transformacion: str | None = None
    parent_plan_id: uuid.UUID | None = None
    is_offer_test: bool = False
    offer_test_label: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OfferTestRequest(BaseModel):
    tipo_oferta: str | None = None
    urgencia: str | None = None
    garantia: str | None = None
    transformacion: str | None = None
    precio_base: float | None = None
    offer_test_label: str = "Oferta B"


class RejectRequest(BaseModel):
    feedback: str


class ResumeCopyRequest(BaseModel):
    selected_copy_indices: list[int]
    next_step: int


class ResumeAdsRequest(BaseModel):
    campaign_edits: dict[str, Any]
    next_step: int


class FunnelChoiceRequest(BaseModel):
    funnel_type: str | None = None  # instant_form | landing_direct | landing_lm | landing_lm_direct
    sale_type: str | None = None  # call | payment
    redirect_url: str | None = None  # URL Calendly/pago si sale_type set, o URL pricing si landing_direct
    # Modo de testeo
    ab_mode: str = "ab_classic"  # ab_classic | multi_angle
    num_angles: int | None = None  # 2-6, solo si multi_angle
    # Lead Ad form (instant_form): plantilla a usar; si null se auto-crea al publicar
    lead_form_id: uuid.UUID | None = None
    # Salida temprana: solo research + ángulos, sin funnel
    research_export: bool = False


class ResearchAngle(BaseModel):
    angle: str
    hook: str | None = None
    copy: str | None = None
    image_url: str | None = None
    headline: str | None = None


class ResearchView(BaseModel):
    """Vista web del research (ResearchModeScreen)."""
    plan_id: uuid.UUID
    business_type: str | None = None
    icp: dict[str, Any] | None = None
    pain_points: list[Any] = []
    angles: list[ResearchAngle] = []
    audience_language: list[str] = []
    angle_history: list[Any] = []  # win rate por ángulo si hay histórico
    scans_remaining: int | None = None
    export_url: str | None = None


class CampaignWizardRequest(BaseModel):
    """Briefing estructurado del wizard de creación de campaña (sustituye al chat).
    Reemplaza las preguntas del OrchestratorAgent por un formulario por pasos."""
    target_customer: str                       # audiencia / cliente objetivo
    location: str                              # país o ciudad para anunciarse
    monthly_budget: float                      # presupuesto mensual en €
    precio_base: float                         # precio del producto/servicio
    transformacion: str                        # resultado concreto que consigue el cliente
    post_conversion_action: str                # qué quiere que haga el cliente tras contactar
    garantia: str | None = None                # texto libre ("30 días", "ninguna"…)
    post_conversion_url: str | None = None     # Calendly / trial / pricing si existe
    business_description: str | None = None     # override; default desde Settings
    business_type: str | None = None            # override; default desde Settings


class ResearchGenerateRequest(BaseModel):
    """Genera un research desde la librería (sin chat ni funnel)."""
    target_customer: str  # audiencia objetivo (placeholder editable desde Settings)
    objective: str | None = None  # objetivo opcional, texto plano
    business_description: str | None = None  # override; default desde Settings
    business_type: str | None = None  # override; default desde Settings


class GenerateImagesRequest(BaseModel):
    """Genera imágenes para ángulos del research que aún no tienen. Cobra 1 escaneo.
    Si `angles` viene, genera exactamente esos; si no, los primeros `count` sin imagen."""
    angles: list[str] | None = None
    count: int = 2


class GenerateImagesResponse(BaseModel):
    status: str
    scans_remaining: int
    pending_angles: int  # ángulos que seguirán sin imagen tras esta tanda


class CreativeAsset(BaseModel):
    """Activo creativo asignado a la variante A o B."""
    # Para image_ai → todo null, lo genera CopyAgent
    # Para image_upload / video_upload / reel_upload → url + media_type
    # Para meta_post → post_id (object_story_id), url opcional (thumbnail)
    url: str | None = None
    thumbnail_url: str | None = None
    media_type: str | None = None  # image | video
    post_id: str | None = None     # object_story_id si meta_post
    width: int | None = None
    height: int | None = None


class CreativeChoiceRequest(BaseModel):
    creative_type: str  # image_ai | image_upload | video_upload | reel_upload | meta_post
    creative_a: CreativeAsset | None = None
    creative_b: CreativeAsset | None = None


class MessageMatchResponse(BaseModel):
    """Validación del hilo narrativo + políticas Meta para el panel de aprobación."""
    hook: str = ""
    warnings: list[str] = []          # message match (hook ↔ landings ↔ emails)
    policy_warnings: list[str] = []   # problemas detectados por MetaPolicyAgent
    policy_status: str | None = None  # approved | approved_with_fixes | rejected


class PublishMetaResponse(BaseModel):
    campaign_id: str
    ad_set_id: str
    ad_ids: list[str]
    meta_ads_manager_url: str


class AgentTaskResponse(BaseModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    agent_name: str
    tool_name: str
    input: dict
    output: dict | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
