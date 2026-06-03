import asyncio
import json
from typing import Any

from app.agents.base import BaseAgent

SYSTEM_PROMPT = """Eres un experto en diseño de landing pages de alta conversión para productos SaaS.
Tu trabajo es generar el contenido completo de dos variantes A/B de una landing page.

Variante A: ángulo emocional — conecta con el pain point, usa el lenguaje de la audiencia
Variante B: ángulo racional — destaca beneficios concretos, métricas, features

Para los campos del formulario: analiza el tipo de SaaS y el objetivo de la campaña para
decidir qué información necesitas para cualificar bien al lead. Un SaaS B2B enterprise
necesita empresa y número de empleados. Un SaaS B2C solo necesita email y nombre.
Sé inteligente — no pidas más campos de los necesarios (cada campo extra reduce conversión)."""

PALETTES = {
    "indigo":  {"primary": "#6366f1", "secondary": "#e0e7ff"},
    "emerald": {"primary": "#10b981", "secondary": "#d1fae5"},
    "violet":  {"primary": "#8b5cf6", "secondary": "#ede9fe"},
    "sky":     {"primary": "#0ea5e9", "secondary": "#e0f2fe"},
    "rose":    {"primary": "#f43f5e", "secondary": "#ffe4e6"},
    "amber":   {"primary": "#f59e0b", "secondary": "#fef3c7"},
    "cyan":    {"primary": "#06b6d4", "secondary": "#cffafe"},
    "slate":   {"primary": "#475569", "secondary": "#f1f5f9"},
    "orange":  {"primary": "#f97316", "secondary": "#ffedd5"},
    "teal":    {"primary": "#14b8a6", "secondary": "#ccfbf1"},
}


def select_template(
    business_type: str,
    tipo_oferta: str,
    funnel_type: str | None,
    landing_subtype: str | None,
) -> str:
    if landing_subtype == "lm":
        return "lead_magnet_clean"
    if business_type == "saas" and tipo_oferta == "prueba_gratuita":
        return "saas_trial"
    if business_type == "saas":
        return "saas_demo"
    if business_type == "services" and tipo_oferta in ("lanzamiento", "descuento_limitado"):
        return "services_launch"
    if business_type == "services":
        return "services_call"
    if business_type == "ecommerce":
        return "ecommerce_product"
    if business_type == "app":
        return "app_download"
    if business_type == "local":
        return "local_offer"
    return "services_call"


class LandingAgent(BaseAgent):
    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("model", "gpt-4o-mini")
        super().__init__(**kwargs)
        self.system_prompt = SYSTEM_PROMPT

    def _get_colors(self, palette: str) -> dict:
        return PALETTES.get(palette, PALETTES["indigo"])

    def _build_context(self, research: dict, copy: dict) -> str:
        lines = []
        if research.get("key_insight"):
            lines.append(f"Key insight: {research['key_insight']}")
        pain_points = research.get("pain_points", [])
        if pain_points:
            lines.append("Pain points: " + " | ".join(f'"{p["phrase"]}"' for p in pain_points[:3]))
        audience_lang = research.get("audience_language", [])
        if audience_lang:
            lines.append("Lenguaje audiencia: " + ", ".join(f'"{p}"' for p in audience_lang[:5]))
        if copy.get("headline"):
            lines.append(f"Headline copy generado: {copy['headline']}")
        if copy.get("benefits"):
            lines.append("Benefits copy: " + " | ".join(copy["benefits"][:4]))
        return "\n".join(lines)

    async def _generate_variant(
        self,
        variant: str,
        saas: str,
        audience: str,
        campaign_type: str,
        context_str: str,
        landing_subtype: str = "lm",
        sale_type: str | None = None,
        redirect_url: str | None = None,
        offer_context: str = "",
    ) -> dict:
        if variant == "a":
            angle = "ÁNGULO EMOCIONAL (variante A)"
            angle_rules = """REGLAS VARIANTE A — EMOCIONAL:
- Headline: habla del DOLOR o FRUSTRACIÓN, no del producto. Ej: "Deja de perder horas en X"
- Subheadline: empatiza con la situación actual del usuario antes de mencionar la solución
- Benefits: formula cada beneficio como alivio de un pain point concreto ("Por fin podrás...", "Nunca más tendrás que...")
- CTA: orientado a transformación ("Quiero dejar de X", "Empieza a Y hoy")
- Tono: conversacional, cercano, como si lo escribiera alguien que vivió el mismo problema
- PROHIBIDO: números, porcentajes, features técnicas, comparaciones de precio"""
        else:
            angle = "ÁNGULO RACIONAL (variante B)"
            angle_rules = """REGLAS VARIANTE B — RACIONAL:
- Headline: promesa concreta con número o métrica. Ej: "Reduce X en un 40% en 2 semanas"
- Subheadline: explica el mecanismo — cómo funciona en 1 frase clara
- Benefits: cada beneficio con métrica o resultado medible ("Ahorra X horas/semana", "Aumenta X en un Y%")
- CTA: orientado a acción de bajo compromiso ("Prueba gratis 14 días", "Ver demo de 3 min")
- Tono: directo, concreto, basado en evidencia, sin metáforas ni lenguaje emocional
- PROHIBIDO: palabras emocionales ("frustración", "por fin", "sueño"), lenguaje vago sin datos"""

        # Subtype sale: landing de venta SIN form, CTA → redirect_url (Calendly o pago)
        if landing_subtype == "sale":
            sale_label = "agendar una llamada (Calendly)" if sale_type == "call" else "comprar/pagar"
            form_instruction = f"""Esta es una LANDING DE VENTA propia (subtype=sale). NO incluyas form_fields (array vacío []).
El CTA debe llevar a: {sale_label} ({redirect_url or 'URL externa'}).
Headlines y benefits deben enfocarse en la transformación final, no en captar lead.
El usuario ya ha sido nutrido por email/whatsapp — esta página cierra la venta.
cta_text debe ser explícito sobre la acción ({"Reservar mi llamada" if sale_type == "call" else "Comprar ahora"})."""
        elif campaign_type == "direct_sale":
            form_instruction = "NO incluyas form_fields (array vacío []) — es venta directa, el CTA lleva al pricing del cliente."
        elif campaign_type == "validation":
            form_instruction = """Es una campaña de VALIDACIÓN de idea. El formulario debe ser ultra simple (solo email, máximo nombre).
El CTA debe ser tipo 'Quiero ser el primero en saberlo' o 'Apúntame a la lista de espera'.
La landing presenta la PROMESA del producto como si estuviera próximo a lanzarse.
form_fields: solo email obligatorio."""
        else:
            form_instruction = f"""Genera el formulario cualificador para leads de "{saas}".

REGLA: Incluye SIEMPRE entre 3 y 5 campos. Nunca menos de 3.

Campos obligatorios siempre:
- email (type: email, required: true)
- nombre (type: text, required: true)

Campos adicionales según el tipo de negocio (elige los más relevantes hasta completar 4-5 campos):
- B2B / SaaS empresa: "empresa" (text), "cargo" (select, opciones: "CEO/Fundador", "Director/VP", "Manager", "Técnico/Desarrollador", "Otro"), "num_empleados" (select, opciones: "Solo yo", "2-10", "11-50", "51-200", "200+"), "principal_reto" (radio, opciones cortas relevantes al producto)
- B2C / ecommerce / app: "telefono" (tel, required: false), "como_nos_conociste" (select, opciones: "Redes sociales", "Google", "Recomendación", "Otro"), pregunta de segmentación clave (radio o select, ej: "¿Con qué frecuencia usas X?")
- Services / consultoría: "empresa" (text), "cargo" (select), "presupuesto_mensual" (select con rangos realistas), "urgencia" (radio, opciones: "Necesito solución ya", "En el próximo mes", "Estoy investigando")
- Local: "telefono" (tel, required: true), "cuando_visitar" (select, opciones horarias/días), "como_nos_conociste" (select)

Tipo "radio" es para máximo 3-4 opciones cortas que el usuario elige con un click (estilo pill/chip). Úsalo para preguntas de intención, urgencia o segmentación.

Formato exacto de cada campo:
{{"name": "campo", "label": "Etiqueta visible", "type": "email|text|tel|number|select|radio", "required": true|false, "placeholder": "texto de ayuda", "options": ["opción 1", "opción 2"], "helper": "texto de ayuda opcional"}}
Los campos "options" y "helper" solo se incluyen cuando son necesarios."""

        offer_block = f"\nOFERTA:\n{offer_context}\n" if offer_context else ""
        prompt = f"""Genera la variante {variant.upper()} de una landing page.

SaaS: {saas}
Audiencia: {audience}
Tipo de campaña: {campaign_type}
{angle}
{offer_block}

{angle_rules}

Contexto de investigación y copy previo:
{context_str}

{form_instruction}

Devuelve SOLO JSON con esta estructura exacta:
{{
  "headline": "titular principal (máx 8 palabras, impactante)",
  "subheadline": "subtítulo que amplía el headline (1 frase, máx 15 palabras)",
  "benefits": ["beneficio concreto 1", "beneficio concreto 2", "beneficio concreto 3", "beneficio concreto 4"],
  "cta_text": "texto del botón principal (máx 5 palabras)",
  "social_proof": "frase de prueba social creíble",
  "form_fields": [
    {{"name": "nombre", "label": "Nombre", "type": "text", "required": true, "placeholder": "Tu nombre"}},
    {{"name": "email", "label": "Email", "type": "email", "required": true, "placeholder": "tu@empresa.com"}},
    {{"name": "empresa", "label": "Empresa", "type": "text", "required": false, "placeholder": "Nombre de tu empresa"}},
    {{"name": "cargo", "label": "Tu rol", "type": "select", "required": false, "placeholder": "Selecciona tu cargo", "options": ["CEO/Fundador", "Director/VP", "Manager", "Técnico/Desarrollador", "Otro"]}},
    {{"name": "num_empleados", "label": "Tamaño del equipo", "type": "select", "required": false, "placeholder": "Selecciona", "options": ["Solo yo", "2-10", "11-50", "51-200", "200+"]}},
    {{"name": "urgencia", "label": "¿Cuándo necesitas una solución?", "type": "radio", "required": false, "options": ["Lo necesito ya", "En el próximo mes", "Estoy explorando"]}}
  ]
}}"""

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1500,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        return json.loads(response.choices[0].message.content or "{}")

    async def _generate_sale_content(
        self,
        variant: str,
        saas: str,
        audience: str,
        sale_type: str | None,
        context_str: str,
        offer_context: str = "",
    ) -> dict:
        """Genera bloques extra de una landing de venta (sale subtype).

        Diferencia por sale_type:
        - payment: precio + garantía + urgencia + testimonios + objeciones (venta completa)
        - call:    autoridad + proceso + testimonios + objeciones (página puente sin precio)
        """
        is_payment = sale_type == "payment"
        cta_action = "Comprar ahora" if is_payment else "Reservar mi llamada"

        if is_payment:
            blocks_spec = """BLOQUES OBLIGATORIOS (sale_type=payment):

1. "value_props" — 3 propuestas de valor para el primer scroll. Cada una con:
   {"icon_hint": "una palabra clave (ej: clock, shield, chart)", "title": "máx 5 palabras", "text": "1 frase concreta"}

2. "social_proof_logos" — array de 4-6 strings con nombres ficticios o tipos de empresa/cliente plausibles (ej: "TechStartup", "Agencia Madrid", "Ecommerce Pro"). Si no procede, array vacío.

3. "testimonials" — 3 testimonios CREÍBLES (no inventes números absurdos):
   {"name": "nombre real plausible", "role": "cargo + tipo empresa", "quote": "1-2 frases en lenguaje natural, sin marketing speak", "result": "métrica concreta opcional o null"}

4. "objections" — 4 objeciones reales del público + respuesta directa:
   {"question": "duda en primera persona", "answer": "respuesta honesta máx 2 frases"}
   Ejemplos de objeciones reales: precio, tiempo de implementación, soporte, comparación con alternativas, riesgo.

5. "urgency" — escasez creíble (NO falsa cuenta atrás):
   {"headline": "frase corta", "subtext": "razón concreta", "deadline_hint": "string informal o null"}
   Solo usa urgencia si tiene sentido (cohorte limitada, precio sube en X, plazas para onboarding). Si no, deja headline vacío.

6. "guarantee" — garantía que reduce riesgo:
   {"headline": "ej: Garantía 30 días", "text": "qué cubre, cómo se solicita, 1-2 frases"}

7. "pricing" — precio CON contexto de valor:
   {"price": "ej: 97€/mes o desde 990€", "billing_note": "string opcional (ej: facturación anual)", "includes": ["item 1", "item 2", "item 3", "item 4"], "value_anchor": "frase que ancla valor (ej: 'Equivale a 1 hora de un consultor')", "comparison": "frase opcional comparando con coste de no hacerlo"}

8. "cta_repeat" — variantes del mismo CTA principal para repetir en distintos puntos:
   {"hero": "texto botón hero", "mid": "texto botón medio (tras testimonios)", "final": "texto botón final (tras pricing/garantía)"}
   Todos deben llevar a la MISMA acción ({cta_action}). Solo varía el wording.

9. "closing_line" — última frase antes del CTA final. Empuja sin presionar."""
        else:
            blocks_spec = """BLOQUES OBLIGATORIOS (sale_type=call):

Esta es una página PUENTE: no se vende producto, se agenda una llamada. NO incluyas precio ni urgencia falsa.

1. "value_props" — 3 propuestas de valor para el primer scroll:
   {"icon_hint": "clock|shield|chart|target|users", "title": "máx 5 palabras", "text": "1 frase concreta sobre el RESULTADO"}

2. "social_proof_logos" — 4-6 strings con tipos de cliente plausibles. Vacío si no procede.

3. "testimonials" — 3 testimonios creíbles enfocados en RESULTADOS tras trabajar contigo:
   {"name": "nombre plausible", "role": "cargo + empresa", "quote": "1-2 frases naturales", "result": "métrica concreta o null"}

4. "objections" — 4 objeciones típicas antes de agendar una llamada:
   {"question": "duda en primera persona", "answer": "respuesta honesta máx 2 frases"}
   Ejemplos: "¿es una llamada de venta?", "no tengo tiempo", "no sé si es para mí", "qué pasa si no encaja".

5. "process" — los 3-4 pasos del proceso tras agendar (transparencia, reduce fricción):
   {"step": número, "title": "máx 4 palabras", "text": "1 frase"}
   Ej: "1. Reservas hueco", "2. Cuestionario corto", "3. Llamada 30 min", "4. Plan personalizado o no encajamos".

6. "authority" — bloque de credibilidad (quién está al otro lado):
   {"headline": "frase corta", "bullets": ["credencial 1", "credencial 2", "credencial 3"]}

7. "guarantee" — promesa de la llamada (NO garantía de producto):
   {"headline": "ej: Llamada sin compromiso", "text": "qué se llevan SÍ o SÍ tras la llamada (auditoría, plan, claridad). 1-2 frases."}

8. "cta_repeat" — variantes del mismo CTA para repetir:
   {"hero": "texto botón hero", "mid": "texto medio", "final": "texto final"}
   Todos llevan a agendar llamada. Solo varía wording.

9. "closing_line" — última frase antes del CTA final. Sin presión."""

        if is_payment:
            json_template = (
                '{\n'
                '  "value_props": [{"icon_hint": "...", "title": "...", "text": "..."}],\n'
                '  "social_proof_logos": ["..."],\n'
                '  "testimonials": [{"name": "...", "role": "...", "quote": "...", "result": null}],\n'
                '  "objections": [{"question": "...", "answer": "..."}],\n'
                '  "urgency": {"headline": "...", "subtext": "...", "deadline_hint": null},\n'
                '  "guarantee": {"headline": "...", "text": "..."},\n'
                '  "pricing": {"price": "...", "billing_note": null, "includes": ["..."], "value_anchor": "...", "comparison": null},\n'
                '  "cta_repeat": {"hero": "...", "mid": "...", "final": "..."},\n'
                '  "closing_line": "..."\n'
                '}'
            )
        else:
            json_template = (
                '{\n'
                '  "value_props": [{"icon_hint": "...", "title": "...", "text": "..."}],\n'
                '  "social_proof_logos": ["..."],\n'
                '  "testimonials": [{"name": "...", "role": "...", "quote": "...", "result": null}],\n'
                '  "objections": [{"question": "...", "answer": "..."}],\n'
                '  "process": [{"step": 1, "title": "...", "text": "..."}],\n'
                '  "authority": {"headline": "...", "bullets": ["..."]},\n'
                '  "guarantee": {"headline": "...", "text": "..."},\n'
                '  "cta_repeat": {"hero": "...", "mid": "...", "final": "..."},\n'
                '  "closing_line": "..."\n'
                '}'
            )

        sale_label = "pago directo" if is_payment else "llamada de consultoría"
        offer_block = f"\nOFERTA Y HILO NARRATIVO:\n{offer_context}\n" if offer_context else ""
        prompt = f"""Genera los bloques de una LANDING DE VENTA (subtype=sale, variante {variant.upper()}).

REGLA CRÍTICA DE MESSAGE MATCH:
Esta landing es el destino final de un usuario que ya vio el anuncio y recibió emails de nurturing.
El headline H1 DEBE retomar el hook exacto del anuncio (ver "Hook del anuncio" en el contexto).
No parafrasees el hook — úsalo literalmente o con mínima adaptación.
El precio, garantía y urgencia deben aparecer de forma prominente para cerrar la venta.

Negocio: {saas}
Audiencia: {audience}
Tipo de cierre: {sale_type or 'desconocido'} ({sale_label})
CTA principal: {cta_action}
{offer_block}
Contexto de investigación y copy previo:
{context_str}

REGLAS GENERALES:
- Nada inventado fuera de lo plausible. Testimonios y empresas deben sonar reales, no genéricos.
- Cero relleno corporativo. Si una frase no aporta, fuera.
- Lenguaje en la voz de la audiencia (mira "Lenguaje audiencia" del contexto).
- Si un bloque no tiene sentido para este negocio, devuelve estructura vacía pero coherente.

{blocks_spec}

Devuelve SOLO JSON con esta estructura exacta:
{json_template}"""

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=2500,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        return json.loads(response.choices[0].message.content or "{}")

    async def run_task(self, step: dict, context: dict | None = None) -> dict[str, Any]:
        context = context or {}
        research = context.get("ResearchAgent", {})
        copy = context.get("CopyAgent", {})

        description = step.get("description", "")
        saas = step.get("business_description") or step.get("saas_description", description)
        audience = step.get("target_customer") or step.get("target_audience", "audiencia objetivo")
        campaign_type = step.get("campaign_type", "lead_gen")
        landing_subtype = step.get("landing_subtype", "lm")
        sale_type = step.get("sale_type")
        redirect_url = step.get("redirect_url")
        palette = step.get("color_palette", "indigo")
        colors = self._get_colors(palette)
        ab_testing = bool(step.get("ab_testing", False))
        context_str = self._build_context(research, copy)

        # Offer Engine fields
        business_type = step.get("business_type", "services")
        funnel_type = step.get("funnel_type")
        tipo_oferta = step.get("tipo_oferta", "evergreen")
        urgencia = step.get("urgencia", "sin_urgencia")
        garantia = step.get("garantia", "sin_garantia")
        transformacion = step.get("transformacion", "")
        precio_base = step.get("precio_base")

        template_id = select_template(business_type, tipo_oferta, funnel_type, landing_subtype)

        offer_parts = []
        # Extraer hook principal del CopyAgent para narrative thread
        hook: str = ""
        copies = copy.get("copies", [])
        if copies and isinstance(copies, list) and len(copies) > 0:
            hook = copies[0].get("hook", "")
        if hook:
            offer_parts.append(f"Hook del anuncio (narrative thread): {hook}")
        if transformacion:
            offer_parts.append(f"Transformación prometida: {transformacion}")
        if precio_base:
            offer_parts.append(f"Precio base: {precio_base}")
        if tipo_oferta and tipo_oferta != "evergreen":
            offer_parts.append(f"Tipo de oferta: {tipo_oferta}")
        if urgencia and urgencia != "sin_urgencia":
            offer_parts.append(f"Urgencia: {urgencia} — usa esto en el copy del CTA y subheadline")
        if garantia and garantia != "sin_garantia":
            offer_parts.append(f"Garantía: {garantia} — menciona en benefits o cerca del CTA")
        offer_context = "\n".join(offer_parts)

        # Extraer hero image del CopyAgent si existe (copies ya extraído arriba)
        hero_image_url: str | None = None
        if copies and isinstance(copies, list) and len(copies) > 0:
            hero_image_url = copies[0].get("image_url")

        # Generar variantes (A siempre; B solo si ab_testing)
        tasks = [
            self._generate_variant("a", saas, audience, campaign_type, context_str,
                                   landing_subtype, sale_type, redirect_url, offer_context),
        ]
        if ab_testing:
            tasks.append(
                self._generate_variant("b", saas, audience, campaign_type, context_str,
                                       landing_subtype, sale_type, redirect_url, offer_context)
            )
        if landing_subtype == "sale":
            tasks.append(self._generate_sale_content("a", saas, audience, sale_type, context_str, offer_context))
            if ab_testing:
                tasks.append(self._generate_sale_content("b", saas, audience, sale_type, context_str, offer_context))

        results = await asyncio.gather(*tasks)
        idx = 0
        variant_a = results[idx]; idx += 1
        variant_b = results[idx] if ab_testing else None
        if ab_testing:
            idx += 1
        sale_a = results[idx] if landing_subtype == "sale" else None
        if landing_subtype == "sale":
            idx += 1
        sale_b = results[idx] if landing_subtype == "sale" and ab_testing else None

        output: dict[str, Any] = {
            "variant_a": {
                **variant_a,
                "colors": colors,
                "hero_image_url": hero_image_url,
                "sale_content": sale_a,
            },
            "campaign_type": campaign_type,
            "landing_subtype": landing_subtype,
            "sale_type": sale_type,
            "palette": palette,
            "ab_testing": ab_testing,
            "template_id": template_id,
        }
        if ab_testing and variant_b is not None:
            output["variant_b"] = {
                **variant_b,
                "colors": colors,
                "hero_image_url": hero_image_url,
                "sale_content": sale_b,
            }
        return output
