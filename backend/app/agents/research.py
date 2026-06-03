import json
from typing import Any

import httpx

from app.agents.base import BaseAgent
from app.config import settings
from app.tools.brave_search import brave_search
from app.tools.meta_ads import META_API_VERSION

SYSTEM_PROMPT = """Eres un experto en investigación de mercado para cualquier tipo de negocio digital.
Tu trabajo es analizar audiencias, competidores y pain points reales del CLIENTE FINAL para crear campañas de marketing efectivas.

Cuando analices resultados de búsqueda:
- Extrae frases textuales que usa el CLIENTE FINAL (no el dueño del negocio) para describir sus problemas
- Para ecommerce: el cliente es el COMPRADOR del producto, no la tienda
- Identifica los competidores más relevantes y sus propuestas de valor
- Detecta ángulos de copy accionables basados en frustraciones y deseos reales
- Prioriza insights específicos, no genéricos
- Responde siempre en el mismo idioma del input"""


class ResearchAgent(BaseAgent):
    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("model", "gpt-4o")
        super().__init__(**kwargs)
        self.system_prompt = SYSTEM_PROMPT

    async def _search_and_format(self, query: str) -> str:
        """Ejecuta búsqueda y formatea resultados para el LLM."""
        results = await brave_search(query, count=8)
        if not results:
            return f"Sin resultados para: {query}"

        lines = [f"=== Búsqueda: {query} ==="]
        for r in results:
            tag = "[FORO]" if r["type"] == "discussion" else "[WEB]"
            lines.append(f"{tag} {r['title']}")
            lines.append(f"  {r['description']}")
            for snippet in r.get("extra_snippets", [])[:2]:
                lines.append(f"  → {snippet}")
        return "\n".join(lines)

    async def _generate_queries(self, business_context: str, business_type: str = "saas") -> list[str]:
        """Usa GPT para generar 3 queries de búsqueda relevantes para el negocio real."""
        angle_map = {
            "ecommerce": ["problemas quejas clientes compradores reddit", "alternativas comparativa comprar", "reseñas opiniones compradores"],
            "saas": ["problemas quejas usuarios software reddit", "alternativas comparativa herramientas", "reseñas opiniones usuarios"],
            "services": ["problemas quejas clientes servicio reddit", "mejores proveedores comparativa", "reseñas opiniones clientes"],
            "app": ["problemas quejas usuarios app reddit", "mejores apps alternativas comparativa", "reseñas opiniones usuarios app"],
            "local": ["problemas quejas clientes locales reddit", "mejores opciones cerca comparativa", "reseñas opiniones locales"],
        }
        angles = angle_map.get(business_type, angle_map["saas"])

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=300,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Eres un experto en investigación de mercado y SEO."},
                {"role": "user", "content": f"""Genera 3 queries de búsqueda en español para investigar este negocio:

Negocio: "{business_context}"
Tipo: {business_type}

Ángulos a cubrir:
1. {angles[0]}
2. {angles[1]}
3. {angles[2]}

REGLA CRÍTICA: Las queries deben ser sobre el PRODUCTO/SERVICIO real que vende este negocio, visto desde la perspectiva del CLIENTE FINAL que lo compra. NO sobre cómo el negocio hace marketing.

Ejemplo correcto para "tienda dropshipping tiras nasales": "tiras nasales ronquidos opiniones reddit"
Ejemplo incorrecto: "dropshipping marketing estrategias"

Devuelve JSON: {{"queries": ["query1", "query2", "query3"]}}"""},
            ],
        )
        data = json.loads(response.choices[0].message.content or "{}")
        return data.get("queries", [business_context])

    async def _describe_image(self, url: str, variant: str) -> str:
        """GPT-4o Vision: describe imagen / thumbnail para guiar ángulos de copy."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                max_tokens=250,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": (
                            f"Describe esta imagen/thumbnail (variante {variant}) que se usará como creativo de anuncio Meta. "
                            "En 3-4 frases: qué muestra, tono visual/emocional (luminoso/oscuro, alegre/serio), "
                            "elementos clave (personas, producto, texto sobreimpreso, contexto). "
                            "Sé concreto, esto va a guiar el copywriting."
                        )},
                        {"type": "image_url", "image_url": {"url": url}},
                    ],
                }],
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[Vision error variante {variant}: {e}]"

    async def _fetch_meta_post(self, post_id: str, access_token: str) -> dict:
        """Lee mensaje + media de un post existente vía Meta Graph API."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"https://graph.facebook.com/{META_API_VERSION}/{post_id}",
                    params={
                        "fields": "message,full_picture,permalink_url,created_time,attachments{media_type,title,description}",
                        "access_token": access_token,
                    },
                )
                if r.status_code != 200:
                    return {"error": r.text}
                return r.json()
        except Exception as e:
            return {"error": str(e)}

    async def _analyze_creative(self, step: dict[str, Any]) -> str:
        """Analiza el creativo elegido por el usuario y devuelve bloque de contexto."""
        creative_type = step.get("creative_type") or "image_ai"
        if creative_type == "image_ai":
            return ""

        creative_a = step.get("creative_a") or {}
        creative_b = step.get("creative_b") or {}
        meta_token = step.get("meta_access_token")

        lines = [f"\n--- ANÁLISIS DE CREATIVO ({creative_type}) ---"]

        if creative_type == "meta_post":
            for label, asset in (("A", creative_a), ("B", creative_b)):
                post_id = asset.get("post_id")
                if not post_id or not meta_token:
                    lines.append(f"[{label}] Sin post_id o sin token Meta")
                    continue
                post = await self._fetch_meta_post(post_id, meta_token)
                if post.get("error"):
                    lines.append(f"[{label}] Error Meta API: {post['error']}")
                    continue
                msg = (post.get("message") or "").strip()[:400]
                pic = post.get("full_picture")
                lines.append(f"[Variante {label}] Caption original del post:")
                lines.append(f'  "{msg}"' if msg else "  (sin caption)")
                if pic:
                    desc = await self._describe_image(pic, label)
                    lines.append(f"  Visual: {desc}")
        else:
            # image_upload / video_upload / reel_upload → Vision en URL o thumbnail
            for label, asset in (("A", creative_a), ("B", creative_b)):
                visual_url = asset.get("url") if creative_type == "image_upload" else (
                    asset.get("thumbnail_url") or asset.get("url")
                )
                if not visual_url:
                    lines.append(f"[{label}] Sin URL para analizar")
                    continue
                if creative_type in {"video_upload", "reel_upload"}:
                    fmt = "Reel vertical 9:16" if creative_type == "reel_upload" else "Video horizontal/cuadrado"
                    lines.append(f"[Variante {label}] {fmt} subido. Análisis del thumbnail:")
                else:
                    lines.append(f"[Variante {label}] Imagen subida. Análisis:")
                desc = await self._describe_image(visual_url, label)
                lines.append(f"  {desc}")

        lines.append("--- FIN ANÁLISIS CREATIVO ---\n")
        lines.append(
            "IMPORTANTE: los pain_points, audience_language y copy_angles deben alinearse "
            "con el tono y contenido visual de estos creativos para que el copy resultante "
            "se sienta coherente con lo que el usuario verá."
        )
        return "\n".join(lines)

    async def run_task(self, step: dict[str, Any]) -> dict[str, Any]:
        description = step.get("description", "")
        # Soportar tanto business_description (nuevo) como saas_description (legacy)
        business_context = (
            step.get("business_description")
            or step.get("saas_description")
            or description
        )
        target_customer = step.get("target_customer", "")
        business_type = step.get("business_type", "saas")

        # Enriquecer el contexto con el cliente objetivo si existe
        if target_customer and target_customer not in business_context:
            business_context = f"{business_context} dirigido a {target_customer}"

        # Generar queries inteligentes con GPT basadas en el negocio real
        queries = await self._generate_queries(business_context, business_type)

        # Ejecutar las 3 búsquedas
        search_results = []
        for query in queries:
            result = await self._search_and_format(query)
            search_results.append(result)

        combined = "\n\n".join(search_results)

        # Si no hay key de Brave, avisar pero continuar con conocimiento del modelo
        if not settings.BRAVE_API_KEY:
            combined = f"[Sin Brave API — usando conocimiento interno del modelo]\nTema: {business_context}"

        # Si el usuario ya eligió creativo, analizarlo con Vision / Meta API
        creative_context = await self._analyze_creative(step)

        # Analizar con OpenAI y estructurar el output
        prompt = f"""Analiza estos resultados de búsqueda sobre: "{business_context}"

{combined}
{creative_context}

Extrae y devuelve SOLO un JSON con esta estructura:
{{
  "pain_points": [
    {{"phrase": "frase textual que usa la audiencia", "frequency": "alta/media/baja", "insight": "qué revela esto para el copy"}}
  ],
  "competitors": [
    {{"name": "nombre", "value_prop": "propuesta de valor", "weakness": "punto débil detectado"}}
  ],
  "audience_language": ["expresión 1 que usa la audiencia", "expresión 2", "expresión 3"],
  "icp": {{
    "demographics": "descripción demográfica del cliente ideal (edad, rol, situación)",
    "psychographics": "valores, motivaciones, estilo de vida, identidad del cliente ideal",
    "behaviors": ["comportamiento clave 1", "comportamiento clave 2", "comportamiento clave 3"],
    "objections": ["objeción principal 1", "objeción principal 2", "objeción principal 3"],
    "trigger_events": ["evento que dispara la búsqueda de solución 1", "evento 2"]
  }},
  "copy_angles": [
    {{"angle": "dolor", "rationale": "por qué funciona para esta audiencia", "hook_example": "ejemplo de hook concreto"}},
    {{"angle": "aspiracion", "rationale": "...", "hook_example": "..."}},
    {{"angle": "miedo_urgencia", "rationale": "...", "hook_example": "..."}},
    {{"angle": "social_proof", "rationale": "...", "hook_example": "..."}},
    {{"angle": "curiosidad", "rationale": "...", "hook_example": "..."}},
    {{"angle": "credibilidad", "rationale": "...", "hook_example": "..."}}
  ],
  "key_insight": "el insight más importante para la campaña en 2 frases",
  "title": "título corto (4-7 palabras) que resuma este research concreto: audiencia + dolor/ángulo principal, NO genérico (ej: 'Freelancers saturados que odian facturar', no 'Research de SaaS')"
}}

Sé específico y accionable. Usa frases reales de los resultados cuando puedas.
Para el ICP: infiere del contexto del negocio y los resultados, no inventes datos.
Para copy_angles: cada ángulo debe tener un hook_example único y concreto para este negocio."""

        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=2048,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
        )

        content = response.choices[0].message.content or "{}"
        result = json.loads(content)
        result["queries_used"] = queries
        result["has_real_data"] = bool(settings.BRAVE_API_KEY)
        result["creative_type_analyzed"] = step.get("creative_type") or "image_ai"
        result["creative_context"] = creative_context or None
        return result
