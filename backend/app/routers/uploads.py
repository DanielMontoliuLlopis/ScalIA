import asyncio

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_active_client_account, get_current_user
from app.database import get_db
from app.models.client_account import ClientAccount
from app.models.user import User
from app.models.user_settings import UserSettings
from app.tools.cloudinary_upload import upload_file_bytes
from app.tools.meta_ads import META_API_VERSION

router = APIRouter(prefix="/uploads", tags=["uploads"])


IMAGE_MIME = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
VIDEO_MIME = {"video/mp4", "video/quicktime", "video/webm"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024   # 10 MB
MAX_VIDEO_BYTES = 100 * 1024 * 1024  # 100 MB


@router.post("/creative")
async def upload_creative(
    file: UploadFile = File(...),
    kind: str = Form("image"),  # image | video
    current_user: User = Depends(get_current_user),
) -> dict:
    if kind not in {"image", "video"}:
        raise HTTPException(status_code=422, detail="kind debe ser image o video")

    content_type = (file.content_type or "").lower()
    valid_mimes = IMAGE_MIME if kind == "image" else VIDEO_MIME
    if content_type not in valid_mimes:
        raise HTTPException(status_code=415, detail=f"Tipo no soportado: {content_type}")

    max_bytes = MAX_IMAGE_BYTES if kind == "image" else MAX_VIDEO_BYTES
    data = await file.read()
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"Archivo > {max_bytes // (1024 * 1024)} MB")

    folder = f"growthOS/user-uploads/{current_user.id}"
    result = await asyncio.to_thread(upload_file_bytes, data, kind, folder)
    if not result or not result.get("url"):
        raise HTTPException(status_code=502, detail="Error subiendo a Cloudinary")

    return {
        "url": result["url"],
        "thumbnail_url": result.get("thumbnail_url"),
        "media_type": kind,
        "width": result.get("width"),
        "height": result.get("height"),
        "bytes": result.get("bytes"),
    }


@router.get("/meta/page-posts")
async def list_meta_page_posts(
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> dict:
    settings_result = await db.execute(
        select(UserSettings).where(UserSettings.client_account_id == client_account.id)
    )
    us = settings_result.scalar_one_or_none()
    if not us or not us.meta_access_token or not us.meta_page_id:
        raise HTTPException(status_code=400, detail="Falta meta_access_token o meta_page_id en Settings")

    fields = "id,message,created_time,full_picture,permalink_url,attachments{media_type}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"https://graph.facebook.com/{META_API_VERSION}/{us.meta_page_id}/posts",
                params={
                    "fields": fields,
                    "limit": 25,
                    "access_token": us.meta_access_token,
                },
            )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Error red Meta API: {e}")

    if r.status_code != 200:
        try:
            err = r.json().get("error", {}).get("message", r.text[:300])
        except Exception:
            err = r.text[:300]
        raise HTTPException(status_code=502, detail=f"Meta API ({r.status_code}): {err}")

    try:
        payload = r.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Meta API devolvió respuesta no-JSON")

    posts = []
    for p in payload.get("data", []):
        attachments = (p.get("attachments") or {}).get("data", []) or []
        media_type = attachments[0].get("media_type") if attachments else "status"
        posts.append({
            "post_id": p.get("id"),
            "message": (p.get("message") or "")[:200],
            "created_time": p.get("created_time"),
            "thumbnail_url": p.get("full_picture"),
            "permalink_url": p.get("permalink_url"),
            "media_type": media_type,
        })

    return {"posts": posts}
