import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_active_client_account, get_current_user, hash_password
from app.database import get_db
from app.models.client_account import ClientAccount, ClientAccountMember
from app.models.user import User
from app.schemas.team import (
    InviteMemberRequest,
    TeamInfo,
    TeamMember,
    UpdateRoleRequest,
)
from app.services import permissions

router = APIRouter(prefix="/team", tags=["team"])


async def _load_account(db: AsyncSession, current_user: User) -> tuple[User, list[User]]:
    """Devuelve (owner, miembros) de la cuenta del usuario actual."""
    owner_id = permissions.account_owner_id(current_user)
    owner_res = await db.execute(select(User).where(User.id == owner_id))
    owner = owner_res.scalar_one()
    members_res = await db.execute(
        select(User).where(
            or_(User.id == owner_id, User.parent_account_id == owner_id)
        )
    )
    members = list(members_res.scalars())
    return owner, members


def _to_member(u: User) -> TeamMember:
    return TeamMember(
        id=u.id,
        email=u.email,
        full_name=u.full_name,
        role=u.role,
        is_owner=u.parent_account_id is None,
        created_at=u.created_at,
    )


@router.get("", response_model=TeamInfo)
async def list_team(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeamInfo:
    owner, members = await _load_account(db, current_user)
    return TeamInfo(
        members=[_to_member(m) for m in members],
        seats_used=len(members),
        seats_limit=permissions.tier_limit(owner, "team_seats"),
    )


@router.post("/members", response_model=TeamMember, status_code=201)
async def invite_member(
    body: InviteMemberRequest,
    current_user: User = Depends(permissions.require_action("manage_team")),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> TeamMember:
    owner, _ = await _load_account(db, current_user)

    # Tier debe incluir 'team' y tener asiento libre
    await permissions.assert_can_add_seat(db, owner)

    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email ya registrado")

    member = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
        parent_account_id=owner.id,
        # Sub-usuario hereda el tier de la cuenta para gating de features
        plan=owner.plan,
        active_campaigns_limit=owner.active_campaigns_limit,
    )
    db.add(member)
    await db.flush()

    # Dar acceso al workspace activo de inmediato.
    db.add(ClientAccountMember(
        client_account_id=client_account.id, user_id=member.id, role=body.role
    ))
    await db.commit()
    await db.refresh(member)
    return _to_member(member)


@router.patch("/members/{member_id}", response_model=TeamMember)
async def update_member_role(
    member_id: uuid.UUID,
    body: UpdateRoleRequest,
    current_user: User = Depends(permissions.require_action("manage_team")),
    db: AsyncSession = Depends(get_db),
) -> TeamMember:
    owner_id = permissions.account_owner_id(current_user)
    res = await db.execute(select(User).where(User.id == member_id))
    member = res.scalar_one_or_none()
    if not member or (member.id != owner_id and member.parent_account_id != owner_id):
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    if member.parent_account_id is None:
        raise HTTPException(status_code=400, detail="No se puede cambiar el rol del owner")

    member.role = body.role
    await db.commit()
    await db.refresh(member)
    return _to_member(member)


@router.delete("/members/{member_id}")
async def remove_member(
    member_id: uuid.UUID,
    current_user: User = Depends(permissions.require_action("manage_team")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    owner_id = permissions.account_owner_id(current_user)
    res = await db.execute(select(User).where(User.id == member_id))
    member = res.scalar_one_or_none()
    if not member or member.parent_account_id != owner_id:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    await db.delete(member)
    await db.commit()
    return {"ok": True}
