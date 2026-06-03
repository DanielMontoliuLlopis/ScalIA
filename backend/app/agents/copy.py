import asyncio
import json
from typing import Any

from app.agents.base import BaseAgent

# gpt-image-1 limita a 5 imágenes/min. Limitamos la concurrencia para no
# disparar las 6 (multi_angle) a la vez y dejamos que el SDK respete el retry-after.
_IMAGE_SEMAPHORE = asyncio.Semaphore(3)
_IMAGE_MAX_RETRIES = 6
# Nº de ángulos que llevan imagen DALL-E en multi_angle (control de coste).
MAX_ANGLE_IMAGES = 2

SYSTEM_PROMPT = """Eres un experto en copywriting de performance marketing para cualquier tipo de negocio digital.
Estás especializado en Meta Ads y email marketing, con foco total en conversión.

Adapta el tono y ángulo según el tipo de negocio:
- ecommerce: urgencia, prueba social, beneficio del producto, oferta, "envío gratis", reseñas
- saas: ROI, ahorro de tiempo, prueba gratis, pain point de herramienta, comparación con competidor
- services: credibilidad, casos de éxito, proceso claro, quién eres, resultado garantizado
- app: beneficio inmediato, gratuito, fácil, descarga ahora, qué hace en 1 frase
- local: cercanía, oferta local, "cerca de ti", urgencia de tiempo, evento

Reglas siempre:
- Habla AL cliente final (no sobre el negocio, sino al comprador)
- Usa el lenguaje EXACTO que usa la audiencia en sus pain points
- Hooks que paren el scroll en el feed
- CTAs directos y específicos (no "Más info", sino "Prueba gratis 14 días")
- Score del 1-10 estimando conversión esperada
- Ordena de mayor a menor score"""


class CopyAgent(BaseAgent):
    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("model", "gpt-4o")
        super().__init__(**kwargs)
        self.system_prompt = SYSTEM_PROMPT

    def _build_research_context(self, context: dict) -> str:
        """Formatea el output del ResearchAgent como contexto para el prompt."""
        if not context:
            return ""

        lines = ["\n--- CONTEXTO DE INVESTIGACIÓN ---"]

        if context.get("key_insight"):
            lines.append(f"Key insight: {context['key_insight']}")

        pain_points = context.get("pain_points", [])
        if pain_points:
            lines.append("\nPain points reales de la audiencia:")
            for pp in pain_points[:4]:
                lines.append(f'  • "{pp.get("phrase", "")}" ({pp.get("frequency", "")} frecuencia)')
                if pp.get("insight"):
                    lines.append(f'    → {pp["insight"]}')

        audience_language = context.get("audience_language", [])
        if audience_language:
            quoted = ", ".join(f'"{p}"' for p in audience_language[:6])
            lines.append(f"\nFrases textuales de la audiencia: {quoted}")

        copy_angles = context.get("copy_angles", [])
        if copy_angles:
            lines.append("\nÁngulos de copy sugeridos:")
            for angle in copy_angles[:3]:
                lines.append(f'  • {angle.get("angle", "")}: "{angle.get("hook_example", "")}"')

        competitors = context.get("competitors", [])
        if competitors:
            lines.append("\nCompetidores a diferenciarse:")
            for c in competitors[:3]:
                lines.append(f'  • {c.get("name", "")}: debilidad = {c.get("weakness", "")}')

        lines.append("--- FIN CONTEXTO ---\n")
        return "\n".join(lines)

    async def _generate_ad_copy(self, saas: str, audience: str, description: str, context: dict, step: dict | None = None) -> dict:
        research_ctx = self._build_research_context(context)
        business_type = (step or {}).get("business_type", "saas")
        target_customer = (step or {}).get("target_customer", audience)

        tone_guide = {
            "ecommerce": "urgente, directo al beneficio del producto, prueba social, oferta",
            "saas": "profesional, ROI-focused, pain point de herramienta",
            "services": "credible, casos de éxito, proceso claro",
            "app": "simple, beneficio inmediato, descarga fácil",
            "local": "cercano, oferta local, urgencia",
        }.get(business_type, "profesional y cercano")

        prompt = f"""Genera 5 variantes de copy para Meta Ads.
{research_ctx}
Negocio: {saas}
Tipo de negocio: {business_type}
Cliente objetivo: {target_customer}
Tono: {tone_guide}
Objetivo: {description}

IMPORTANTE: El copy debe hablar DIRECTAMENTE al cliente final ({target_customer}), no sobre el negocio.
Usa las frases textuales de los pain points cuando las tengas.
Para ecommerce: habla del PRODUCTO y sus beneficios, no de la tienda.

Devuelve SOLO JSON:
{{
  "copies": [
    {{
      "hook": "primera línea que para el scroll (usa lenguaje de la audiencia)",
      "body": "desarrollo del mensaje (2-3 frases)",
      "cta": "texto del botón",
      "score": 8,
      "angle": "ángulo usado (ej: pain point, social proof, curiosidad)"
    }}
  ]
}}
Ordena de mayor a menor score."""

        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=2048,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        return json.loads(response.choices[0].message.content or "{}")

    # Los 6 ángulos canónicos del ResearchAgent
    ANGLES = ["dolor", "aspiracion", "miedo_urgencia", "social_proof", "curiosidad", "credibilidad"]
    ANGLE_GUIDE = {
        "dolor": "el problema/dolor concreto que sufre la audiencia, agitándolo",
        "aspiracion": "la aspiración/deseo y la vida mejor tras la transformación",
        "miedo_urgencia": "el miedo a perder la oportunidad y la urgencia de actuar ya",
        "social_proof": "prueba social: otros como él ya lo lograron, testimonios, números",
        "curiosidad": "curiosidad/intriga, un mecanismo o secreto inesperado",
        "credibilidad": "credibilidad/autoridad: por qué confiar, método probado, datos",
    }

    async def _generate_multi_angle_copies(
        self, saas: str, audience: str, description: str, context: dict, step: dict | None, num_angles: int
    ) -> dict:
        """Modo Multi-Angle: 1 copy + 1 imagen DALL-E propia por cada ángulo.
        Cada ángulo es un paquete texto+imagen coherente (no variantes A/B de uno)."""
        research_ctx = self._build_research_context(context)
        business_type = (step or {}).get("business_type", "saas")
        target_customer = (step or {}).get("target_customer", audience)

        # Feedback loop: priorizar ángulos con buen histórico (win rate) para este
        # business_type; luego los sugeridos por el research; luego los canónicos.
        priority = [a for a in (step or {}).get("priority_angles", []) if a in self.ANGLES]
        suggested = [a.get("angle") for a in context.get("copy_angles", []) if a.get("angle")]
        ordered: list[str] = []
        for source in (priority, [a for a in suggested if a in self.ANGLES], self.ANGLES):
            for a in source:
                if a not in ordered:
                    ordered.append(a)
        chosen = ordered[: max(2, min(num_angles, 6))]

        # Solo los 2 primeros ángulos (mayor prioridad) llevan imagen DALL-E:
        # gpt-image-1 en calidad alta es caro (~$0,17/img). El resto va sin imagen.
        with_image = set(chosen[:MAX_ANGLE_IMAGES])

        async def _one(angle: str) -> dict:
            guide = self.ANGLE_GUIDE.get(angle, "")
            prompt = f"""Genera UN copy de Meta Ads para el ÁNGULO "{angle}".
{research_ctx}
Negocio: {saas}
Tipo de negocio: {business_type}
Cliente objetivo: {target_customer}
Objetivo: {description}
Enfoque del ángulo: {guide}

El copy debe partir EXCLUSIVAMENTE de este ángulo. Habla DIRECTO al cliente final.
Devuelve SOLO JSON:
{{
  "hook": "primera línea que para el scroll, alineada al ángulo {angle}",
  "body": "2-3 frases desarrollando el ángulo",
  "cta": "texto del botón",
  "score": 8,
  "angle": "{angle}"
}}"""
            try:
                resp = await self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=700,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                )
                copy = json.loads(resp.choices[0].message.content or "{}")
            except Exception as e:
                print(f"[CopyAgent] multi_angle copy error ({angle}): {e}")
                copy = {"hook": "", "body": "", "cta": "Más info", "score": 5}
            copy["angle"] = angle
            # Imagen propia del ángulo (solo los 2 prioritarios; el resto sin imagen)
            if angle in with_image:
                copy["image_url"] = await self._generate_image_for_angle(copy, saas, audience, business_type, angle)
            else:
                copy["image_url"] = None
            return copy

        copies = await asyncio.gather(*[_one(a) for a in chosen])
        return {
            "copies": list(copies),
            "ab_mode": "multi_angle",
            "ab_testing": False,
            "creative_type": "image_ai",
        }

    async def _generate_image_for_angle(
        self, copy: dict, saas: str, audience: str, business_type: str, angle: str
    ) -> str | None:
        """Imagen DALL-E coherente con el ángulo concreto (no compartida entre ángulos)."""
        mood = {
            "dolor": "tense, problem-aware, before-state, muted tones conveying frustration",
            "aspiracion": "bright, aspirational, after-state, success and lifestyle",
            "miedo_urgencia": "high-contrast, urgent, countdown/scarcity feeling",
            "social_proof": "people, testimonials, community, trust badges, ratings",
            "curiosidad": "intriguing, mysterious, unexpected visual metaphor",
            "credibilidad": "authoritative, data, clean professional, expert/credentials",
        }.get(angle, "clean modern")
        image_prompt = f"""Professional Meta Ad creative for a {business_type} business.
Product: {saas}
Target: {audience}
Marketing angle: {angle} — {self.ANGLE_GUIDE.get(angle, '')}
Ad message: {copy.get('hook', '')} — {copy.get('body', '')}

Visual mood for this angle: {mood}.
Style: clean, modern, scroll-stopping. Square (1:1) for Facebook/Instagram feed.
NO text that says 'ad' or 'sponsored'."""
        try:
            async with _IMAGE_SEMAPHORE:
                response = await self.client.with_options(
                    max_retries=_IMAGE_MAX_RETRIES
                ).images.generate(
                    model="gpt-image-1", prompt=image_prompt, size="1024x1024", n=1,
                    quality="high",
                )
            img = response.data[0]
            from app.tools.cloudinary_upload import upload_base64_image
            if hasattr(img, "b64_json") and img.b64_json:
                b64_url = f"data:image/png;base64,{img.b64_json}"
                loop = asyncio.get_event_loop()
                permanent_url = await loop.run_in_executor(None, upload_base64_image, b64_url)
                return permanent_url or b64_url
            return img.url
        except Exception as e:
            print(f"[CopyAgent] angle image error ({angle}): {e}")
            return None

    async def _generate_landing_copy(self, saas: str, audience: str, description: str, context: dict) -> dict:
        research_ctx = self._build_research_context(context)
        prompt = f"""Genera copy completo para una landing page.
{research_ctx}
SaaS: {saas}
Audiencia: {audience}
Objetivo: {description}

Devuelve SOLO JSON:
{{
  "headline": "titular principal (máx 8 palabras, usa lenguaje de la audiencia)",
  "subheadline": "subtítulo explicativo (1 frase)",
  "benefits": ["beneficio 1", "beneficio 2", "beneficio 3", "beneficio 4"],
  "cta": "texto del botón principal",
  "social_proof": "frase de prueba social realista"
}}"""

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1024,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        return json.loads(response.choices[0].message.content or "{}")

    async def _generate_email_sequence(self, saas: str, description: str, context: dict) -> dict:
        research_ctx = self._build_research_context(context)
        prompt = f"""Genera una secuencia de 3 emails de nurturing.
{research_ctx}
SaaS: {saas}
Objetivo: {description}

Devuelve SOLO JSON:
{{
  "emails": [
    {{
      "subject": "asunto con curiosity gap",
      "preview": "texto preview (50 chars máx)",
      "body": "cuerpo conversacional con un solo CTA",
      "send_delay_days": 0
    }}
  ]
}}"""

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=2000,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        return json.loads(response.choices[0].message.content or "{}")

    async def _generate_dco_assets(
        self, saas: str, audience: str, description: str, context: dict, copies: list[dict]
    ) -> dict:
        """Genera múltiples titulares/textos/descripciones/imágenes para creatividad
        dinámica (DCO). Meta combina automáticamente los assets para hallar la mejor
        mezcla — más potente que un único creativo estático."""
        research_ctx = self._build_research_context(context)
        top = copies[0] if copies else {}
        prompt = f"""Genera assets para un anuncio de CREATIVIDAD DINÁMICA (DCO) de Meta.
Meta combinará automáticamente titulares, textos e imágenes para encontrar la mejor mezcla,
así que cada variante debe ser autónoma y con un ángulo DISTINTO.
{research_ctx}
Negocio: {saas}
Audiencia: {audience}
Objetivo: {description}
Hook base: {top.get('hook', '')}

Devuelve SOLO JSON con MÚLTIPLES variantes:
{{
  "titles": ["titular corto ≤40 caracteres", "... 4-5 variantes con ángulos distintos"],
  "bodies": ["texto principal de 1-3 frases", "... 4-5 variantes"],
  "descriptions": ["descripción ≤60 caracteres", "... 2-3 variantes"]
}}
Usa el lenguaje real de la audiencia. No repitas el mismo ángulo."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                max_tokens=1500,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            data = json.loads(response.choices[0].message.content or "{}")
        except Exception as e:
            print(f"[CopyAgent] DCO text error: {e}")
            data = {}

        # Imágenes: generamos varias desde los mejores copies para que Meta las combine
        img_sources = (copies[:3] or [top]) if (copies or top) else []
        image_urls: list[str] = []
        if img_sources:
            image_tasks = [self._generate_image_for_copy(c, saas, audience) for c in img_sources]
            results = await asyncio.gather(*image_tasks)
            image_urls = [u for u in results if u]

        return {
            "titles": [t for t in data.get("titles", []) if t][:5],
            "bodies": [b for b in data.get("bodies", []) if b][:5],
            "descriptions": [d for d in data.get("descriptions", []) if d][:3],
            "images": image_urls[:10],
        }

    async def _generate_image_for_copy(self, copy: dict, saas: str, audience: str) -> str | None:
        """Genera imagen con DALL-E para un copy. Devuelve URL o None si falla."""
        try:
            image_prompt = f"""Professional Meta Ad creative for a SaaS product.
Product: {saas}
Target: {audience}
Ad message: {copy.get('hook', '')} — {copy.get('body', '')}

Style: Clean, modern, minimal design. White background with one accent color.
Include: Bold headline text overlay, professional lifestyle photo or abstract graphic.
NO text that says 'ad' or 'sponsored'. Photorealistic or flat design illustration.
Aspect ratio: square (1:1), suitable for Facebook/Instagram feed."""

            async with _IMAGE_SEMAPHORE:
                response = await self.client.with_options(
                    max_retries=_IMAGE_MAX_RETRIES
                ).images.generate(
                    model="gpt-image-1",
                    prompt=image_prompt,
                    size="1024x1024",
                    n=1,
                    quality="high",
                )
            img = response.data[0]

            # Subir a Cloudinary para URL permanente
            from app.tools.cloudinary_upload import upload_base64_image
            import asyncio

            if hasattr(img, "b64_json") and img.b64_json:
                b64_url = f"data:image/png;base64,{img.b64_json}"
                # Cloudinary upload es síncrono — lo ejecutamos en thread pool
                loop = asyncio.get_event_loop()
                permanent_url = await loop.run_in_executor(
                    None, upload_base64_image, b64_url
                )
                return permanent_url or b64_url
            return img.url
        except Exception as e:
            print(f"[CopyAgent] Image error: {e}")
            return None

    async def run_task(self, step: dict, context: dict | None = None) -> dict[str, Any]:
        """Ejecuta un step del plan con contexto acumulado de agentes anteriores."""
        action = step.get("action", "")
        description = step.get("description", "")
        # Soportar tanto business_description (nuevo) como saas_description (legacy)
        saas = step.get("business_description") or step.get("saas_description", description)
        audience = step.get("target_customer") or step.get("target_audience", "audiencia objetivo")
        research_ctx = context or {}

        # Inferir tipo de tool por nombre de acción
        action_lower = action.lower()
        if any(w in action_lower for w in ["email", "sequence", "nurtur"]):
            tool_name = "email"
        elif any(w in action_lower for w in ["landing", "page"]):
            tool_name = "landing"
        else:
            tool_name = "ad_copy"

        if tool_name == "ad_copy":
            creative_type = step.get("creative_type") or "image_ai"
            creative_a = step.get("creative_a") or {}
            creative_b = step.get("creative_b") or {}
            ab_testing = bool(step.get("ab_testing", False))
            ab_mode = step.get("ab_mode") or "ab_classic"

            # ── Modo Multi-Angle: 1 copy + 1 imagen propia por ángulo ──────────
            if ab_mode == "multi_angle":
                num_angles = int(step.get("num_angles") or 3)
                return await self._generate_multi_angle_copies(
                    saas, audience, description, research_ctx, step, num_angles
                )

            # ── Modo DCO: el usuario eligió DCO en el CreativeChoiceSelector ────
            # En DCO no generamos variantes de copy para selección — directamente
            # producimos los assets múltiples (titulares/textos/imágenes) que Meta
            # combinará automáticamente. El panel de aprobación muestra un preview
            # de esos assets, no un selector de variantes.
            if creative_type == "dco":
                # Necesitamos un copy base como contexto para los assets
                base = await self._generate_ad_copy(saas, audience, description, research_ctx, step)
                base_copies = base.get("copies", [])
                dco_assets = await self._generate_dco_assets(
                    saas, audience, description, research_ctx, base_copies
                )
                return {
                    "creative_type": "dco",
                    "dco_assets": dco_assets,
                    "copies": base_copies[:1],  # referencia interna, no se usa para selección
                    "ab_testing": False,
                }

            result = await self._generate_ad_copy(saas, audience, description, research_ctx, step)
            copies = result.get("copies", [])
            num_variants = 2 if ab_testing else 1

            if copies and creative_type == "image_ai":
                tasks = [
                    self._generate_image_for_copy(copies[i], saas, audience)
                    for i in range(min(num_variants, len(copies)))
                ]
                image_urls = await asyncio.gather(*tasks)
                for i, url in enumerate(image_urls):
                    if url:
                        copies[i]["image_url"] = url
            elif copies:
                user_assets = [creative_a, creative_b][:num_variants]
                for i in range(min(num_variants, len(copies))):
                    asset = user_assets[i] if i < len(user_assets) else {}
                    if not asset:
                        continue
                    if asset.get("url"):
                        copies[i]["image_url"] = asset["url"]
                    if asset.get("thumbnail_url"):
                        copies[i]["thumbnail_url"] = asset["thumbnail_url"]
                    if asset.get("post_id"):
                        copies[i]["meta_post_id"] = asset["post_id"]
                    copies[i]["media_type"] = asset.get("media_type") or (
                        "video" if creative_type in {"video_upload", "reel_upload"} else "image"
                    )
                    copies[i]["creative_source"] = creative_type

            result["copies"] = copies
            result["creative_type"] = creative_type
            result["ab_testing"] = ab_testing
            return result

        if tool_name == "landing":
            return await self._generate_landing_copy(saas, audience, description, research_ctx)

        if tool_name == "email":
            return await self._generate_email_sequence(saas, description, research_ctx)

        return {"status": "pending_implementation", "action": action}
