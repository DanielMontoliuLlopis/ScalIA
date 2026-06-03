from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.database import get_db
from app.models.client_account import ClientAccount
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.closers import closer_by_ref_code
from app.services.owner import apply_owner_overrides, is_owner

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        phone=body.phone,
        business_type=body.business_type,
        plan="canceled",
        role="owner",
        active_campaigns_limit=0,
    )

    if is_owner(body.email):
        apply_owner_overrides(user)

    # Atribución a closer vía link referido (/?ref=CODE)
    closer = await closer_by_ref_code(db, body.ref_code)
    if closer:
        user.closer_id = closer.id

    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Workspace por defecto: toda cuenta arranca con un client_account.
    client_account = ClientAccount(
        owner_id=user.id,
        name=body.full_name or body.email,
        business_type=body.business_type,
    )
    db.add(client_account)
    await db.commit()

    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/me/features")
async def my_features(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Qué puede hacer el usuario según su plan. El frontend bloquea con upsell
    las funciones no incluidas (no las esconde)."""
    from app.services import permissions

    # Reinicio perezoso: si el ciclo expiró (o nunca se inicializó) el saldo
    # de escaneos se fija al tope del plan. Sin esto un plan recién activado
    # mostraría 0 escaneos hasta el primer consume_scan.
    before = current_user.scans_remaining, current_user.scans_reset_at
    permissions._maybe_reset_scans(current_user)
    if (current_user.scans_remaining, current_user.scans_reset_at) != before:
        await db.commit()

    tier = permissions.tier_of(current_user)
    return {
        "plan": tier,
        "research_only": permissions.is_research_only(current_user),
        "features": sorted(permissions.TIER_FEATURES.get(tier, set())),
        "limits": permissions.TIER_LIMITS.get(tier, {}),
        "scans_remaining": current_user.scans_remaining,
        "scans_per_month": permissions.scans_per_month(current_user),
        "scans_reset_at": current_user.scans_reset_at,
        "is_founder": current_user.is_founder,
        "is_superadmin": current_user.is_superadmin,
    }
