import httpx

WHATSAPP_API_VERSION = "v19.0"
WHATSAPP_BASE_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}"


async def send_whatsapp_text(
    access_token: str,
    phone_number_id: str,
    to_phone: str,
    message: str,
) -> dict:
    """Send a plain text WhatsApp message via Meta Cloud API."""
    url = f"{WHATSAPP_BASE_URL}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone,
        "type": "text",
        "text": {"preview_url": False, "body": message},
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
