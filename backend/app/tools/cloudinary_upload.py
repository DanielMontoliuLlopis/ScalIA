import base64
import io

import cloudinary
import cloudinary.uploader

from app.config import settings


def _configure():
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


def upload_pdf_bytes(pdf_bytes: bytes, folder: str = "growthOS/lead-magnets", public_id: str | None = None) -> str | None:
    """Sube un PDF a Cloudinary y devuelve la URL permanente."""
    if not settings.CLOUDINARY_API_SECRET:
        return None
    try:
        _configure()
        kwargs = {
            "folder": folder,
            "resource_type": "raw",
            "format": "pdf",
        }
        if public_id:
            kwargs["public_id"] = public_id
        result = cloudinary.uploader.upload(
            io.BytesIO(pdf_bytes),
            **kwargs,
        )
        return result.get("secure_url", "")
    except Exception as e:
        print(f"[Cloudinary] PDF upload error: {e}")
        return None


def upload_file_bytes(
    data: bytes,
    resource_type: str = "image",
    folder: str = "growthOS/uploads",
) -> dict | None:
    """Sube bytes (imagen o video) a Cloudinary y devuelve dict con url + metadata."""
    if not settings.CLOUDINARY_API_SECRET:
        return None
    try:
        _configure()
        result = cloudinary.uploader.upload(
            io.BytesIO(data),
            folder=folder,
            resource_type=resource_type,  # image | video | raw
        )
        url = result.get("secure_url", "")
        if resource_type == "image" and url and "/upload/" in url:
            url = url.replace("/upload/", "/upload/q_auto,f_auto/")
        return {
            "url": url,
            "thumbnail_url": result.get("secure_url", "").replace(".mp4", ".jpg") if resource_type == "video" else url,
            "width": result.get("width"),
            "height": result.get("height"),
            "duration": result.get("duration"),
            "bytes": result.get("bytes"),
            "format": result.get("format"),
        }
    except Exception as e:
        print(f"[Cloudinary] File upload error: {e}")
        return None


def upload_base64_image(b64_data_url: str, folder: str = "growthOS/ads") -> str | None:
    """Sube una imagen base64 a Cloudinary y devuelve la URL permanente."""
    if not settings.CLOUDINARY_API_SECRET:
        return None
    try:
        _configure()
        # Extraer solo el base64 si viene con prefijo data:image/...;base64,
        if "," in b64_data_url:
            b64_data = b64_data_url.split(",", 1)[1]
        else:
            b64_data = b64_data_url

        image_bytes = base64.b64decode(b64_data)
        result = cloudinary.uploader.upload(
            io.BytesIO(image_bytes),
            folder=folder,
            resource_type="image",
        )
        # Aplicar optimización en la URL directamente
        url = result.get("secure_url", "")
        # Insertar transformación automática en la URL
        if url and "/upload/" in url:
            url = url.replace("/upload/", "/upload/q_auto,f_auto/")
        return url
    except Exception as e:
        print(f"[Cloudinary] Upload error: {e}")
        return None
