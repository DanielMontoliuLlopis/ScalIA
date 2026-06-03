import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.client_account import ClientAccount, ClientAccountMember
from app.models.user import User
from app.schemas.client_account import (
    AddMemberRequest,
    ClientAccountCreate,
    ClientAccountResponse,
    ClientAccountUpdate,
    ClientMemberResponse,
)
from app.services import permissions

router = APIRouter(prefix="/client-accounts", tags=["client-accounts"])


async def _owned_account(db: AsyncSession, current_user: User, ca_id: uuid.UUID) -> ClientAccount:
    """Carga un workspace verificando que el usuario actual sea su owner."""
    owner_id = permissions.account_owner_id(current_user)
    res = await db.execute(select(ClientAccount).where(ClientAccount.id == ca_id))
    ca = res.scalar_one_or_none()
    if ca is None or ca.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Workspace no encontrado")
    return ca


@router.get("", response_model=list[ClientAccountResponse])
async def list_client_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ClientAccount]:
    """Workspaces accesibles: los del owner + aquellos en los que el usuario es miembro."""
    owner_id = permissions.account_owner_id(current_user)
    member_ca_ids = select(ClientAccountMember.client_account_id).where(
        ClientAccountMember.user_id == current_user.id
    )
    res = await db.execute(
        select(ClientAccount)
        .where(
            or_(
                ClientAccount.owner_id == owner_id,
                ClientAccount.id.in_(member_ca_ids),
            )
        )
        .order_by(ClientAccount.created_at.asc())
    )
    return list(res.scalars())


@router.post("", response_model=ClientAccountResponse, status_code=201)
async def create_client_account(
    body: ClientAccountCreate,
    current_user: User = Depends(permissions.require_action("manage_team")),
    db: AsyncSession = Depends(get_db),
) -> ClientAccount:
    await permissions.assert_can_create_client_account(db, current_user)
    owner_id = permissions.account_owner_id(current_user)
    ca = ClientAccount(
        owner_id=owner_id,
        name=body.name,
        business_type=body.business_type,
        logo_url=body.logo_url,
        color_palette=body.color_palette,
    )
    db.add(ca)
    await db.commit()
    await db.refresh(ca)
    return ca


@router.patch("/{ca_id}", response_model=ClientAccountResponse)
async def update_client_account(
    ca_id: uuid.UUID,
    body: ClientAccountUpdate,
    current_user: User = Depends(permissions.require_action("manage_team")),
    db: AsyncSession = Depends(get_db),
) -> ClientAccount:
    ca = await _owned_account(db, current_user, ca_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(ca, field, value)
    await db.commit()
    await db.refresh(ca)
    return ca


@router.delete("/{ca_id}")
async def delete_client_account(
    ca_id: uuid.UUID,
    current_user: User = Depends(permissions.require_action("manage_team")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    ca = await _owned_account(db, current_user, ca_id)
    # No permitir borrar el último workspace de la cuenta.
    owner_id = permissions.account_owner_id(current_user)
    count = await permissions.count_client_accounts(db, owner_id)
    if count <= 1:
        raise HTTPException(status_code=400, detail="No puedes borrar tu único workspace")
    await db.delete(ca)
    await db.commit()
    return {"ok": True}


@router.get("/{ca_id}/members", response_model=list[ClientMemberResponse])
async def list_members(
    ca_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ClientMemberResponse]:
    await _owned_account(db, current_user, ca_id)
    res = await db.execute(
        select(ClientAccountMember, User)
        .join(User, User.id == ClientAccountMember.user_id)
        .where(ClientAccountMember.client_account_id == ca_id)
    )
    return [
        ClientMemberResponse(user_id=u.id, email=u.email, full_name=u.full_name, role=m.role)
        for m, u in res.all()
    ]


@router.post("/{ca_id}/members", response_model=ClientMemberResponse, status_code=201)
async def add_member(
    ca_id: uuid.UUID,
    body: AddMemberRequest,
    current_user: User = Depends(permissions.require_action("manage_team")),
    db: AsyncSession = Depends(get_db),
) -> ClientMemberResponse:
    await _owned_account(db, current_user, ca_id)
    owner_id = permissions.account_owner_id(current_user)

    # El usuario a asignar debe pertenecer a la cuenta (owner o sub-usuario).
    res = await db.execute(select(User).where(User.id == body.user_id))
    target = res.scalar_one_or_none()
    if not target or (target.id != owner_id and target.parent_account_id != owner_id):
        raise HTTPException(status_code=404, detail="Usuario no pertenece a la cuenta")

    existing = await db.execute(
        select(ClientAccountMember).where(
            ClientAccountMember.client_account_id == ca_id,
            ClientAccountMember.user_id == body.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El usuario ya es miembro del workspace")

    member = ClientAccountMember(
        client_account_id=ca_id, user_id=body.user_id, role=body.role
    )
    db.add(member)
    await db.commit()
    return ClientMemberResponse(
        user_id=target.id, email=target.email, full_name=target.full_name, role=body.role
    )


@router.delete("/{ca_id}/members/{user_id}")
async def remove_member(
    ca_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(permissions.require_action("manage_team")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await _owned_account(db, current_user, ca_id)
    res = await db.execute(
        select(ClientAccountMember).where(
            ClientAccountMember.client_account_id == ca_id,
            ClientAccountMember.user_id == user_id,
        )
    )
    member = res.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    await db.delete(member)
    await db.commit()
    return {"ok": True}
