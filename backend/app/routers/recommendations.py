import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_active_client_account, get_current_user
from app.database import get_db
from app.models.client_account import ClientAccount
from app.models.plan import Plan
from app.models.recommendation import Recommendation
from app.models.user import User
from app.services import permissions

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class RecommendationResponse(BaseModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    type: str
    reasoning: str
    action_payload: dict
    status: str
    applied_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationStatusUpdate(BaseModel):
    status: str  # approved | rejected


@router.get("/campaigns/{plan_id}", response_model=list[RecommendationResponse])
async def get_campaign_recommendations(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> list[RecommendationResponse]:
    plan = (await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    result = await db.execute(
        select(Recommendation)
        .where(Recommendation.plan_id == plan_id)
        .order_by(Recommendation.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{recommendation_id}/approve", response_model=RecommendationResponse)
async def approve_recommendation(
    recommendation_id: uuid.UUID,
    current_user: User = Depends(permissions.require_feature("optimization")),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    rec = (await db.execute(
        select(Recommendation).where(
            Recommendation.id == recommendation_id,
            Recommendation.client_account_id == client_account.id,
        )
    )).scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.status != "pending":
        raise HTTPException(status_code=400, detail=f"Recomendación ya está en estado '{rec.status}'")

    rec.status = "approved"
    rec.applied_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(rec)
    return rec


@router.post("/{recommendation_id}/reject", response_model=RecommendationResponse)
async def reject_recommendation(
    recommendation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    rec = (await db.execute(
        select(Recommendation).where(
            Recommendation.id == recommendation_id,
            Recommendation.client_account_id == client_account.id,
        )
    )).scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    rec.status = "rejected"
    await db.commit()
    await db.refresh(rec)
    return rec


@router.post("/campaigns/{plan_id}/trigger", response_model=dict)
async def trigger_optimization(
    plan_id: uuid.UUID,
    current_user: User = Depends(permissions.require_feature("optimization")),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Dispara análisis de optimización manualmente para una campaña."""
    plan = (await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    from app.workers.optimization_tasks import run_optimization_for_plan
    task = run_optimization_for_plan.delay(str(plan_id), str(current_user.id))
    return {"task_id": task.id, "status": "queued"}
