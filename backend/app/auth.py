import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User

bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_closer_token(closer_id: uuid.UUID) -> str:
    """Token para el portal del closer. `typ=closer` lo distingue de los de usuario."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(closer_id), "typ": "closer", "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


async def get_active_client_account(
    x_client_account_id: str | None = Header(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resuelve el workspace (ClientAccount) sobre el que opera la petición.

    - Si llega el header `X-Client-Account-Id`: valida que el usuario sea owner
      del workspace o esté listado en `client_account_members`.
    - Si no llega: devuelve el primer workspace del owner de la cuenta.
    """
    from app.models.client_account import ClientAccount, ClientAccountMember

    owner_id = current_user.parent_account_id or current_user.id

    if x_client_account_id:
        try:
            ca_id = uuid.UUID(x_client_account_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="X-Client-Account-Id inválido")

        result = await db.execute(select(ClientAccount).where(ClientAccount.id == ca_id))
        ca = result.scalar_one_or_none()
        if ca is None:
            raise HTTPException(status_code=404, detail="Workspace no encontrado")

        if ca.owner_id != owner_id:
            mem = await db.execute(
                select(ClientAccountMember).where(
                    ClientAccountMember.client_account_id == ca_id,
                    ClientAccountMember.user_id == current_user.id,
                )
            )
            if mem.scalar_one_or_none() is None:
                raise HTTPException(status_code=403, detail="Sin acceso a este workspace")
        return ca

    # Sin header: workspace por defecto (el más antiguo del owner).
    result = await db.execute(
        select(ClientAccount)
        .where(ClientAccount.owner_id == owner_id)
        .order_by(ClientAccount.created_at.asc())
        .limit(1)
    )
    ca = result.scalar_one_or_none()
    if ca is None:
        raise HTTPException(status_code=500, detail="La cuenta no tiene ningún workspace")
    return ca


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency: exige superadmin de plataforma. 403 en caso contrario.

    No basta con `role=admin` (eso es admin DENTRO de una cuenta). El panel
    de plataforma requiere `is_superadmin`.
    """
    if not current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido a administradores de la plataforma",
        )
    return current_user


async def get_current_closer(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Dependency: resuelve el Closer autenticado a partir de un token `typ=closer`."""
    from app.models.closer import Closer  # import local para evitar ciclos

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de closer inválido o caducado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("typ") != "closer":
            raise credentials_exception
        closer_id: str = payload.get("sub")
        if closer_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(Closer).where(Closer.id == uuid.UUID(closer_id)))
    closer = result.scalar_one_or_none()
    if closer is None or not closer.is_active:
        raise credentials_exception
    return closer
