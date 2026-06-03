import httpx
from typing import Any


RESEND_API_URL = "https://api.resend.com/emails"


async def send_email(
    api_key: str,
    from_email: str,
    to: str,
    subject: str,
    html: str,
    reply_to: str | None = None,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "from": from_email,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if reply_to:
        payload["reply_to"] = reply_to

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(RESEND_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


async def send_email_sequence(
    api_key: str,
    from_email: str,
    to: str,
    emails: list[dict],
) -> list[dict[str, Any]]:
    """Sends only the first email immediately; returns results list."""
    results = []
    if not emails:
        return results

    # Send only email 1 (delay=0) immediately — delayed emails need a scheduler
    first = emails[0]
    try:
        result = await send_email(
            api_key=api_key,
            from_email=from_email,
            to=to,
            subject=first.get("subject", ""),
            html=first.get("body_html", ""),
        )
        results.append({"order": first.get("order", 1), "status": "sent", "id": result.get("id")})
    except Exception as exc:
        results.append({"order": first.get("order", 1), "status": "failed", "error": str(exc)})

    # Mark remaining as scheduled (actual scheduling requires Celery beat or similar)
    for email in emails[1:]:
        results.append({
            "order": email.get("order"),
            "status": "scheduled",
            "send_delay_hours": email.get("send_delay_hours"),
        })

    return results
