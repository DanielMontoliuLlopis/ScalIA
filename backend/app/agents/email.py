import asyncio
import json
from typing import Any

from app.agents.base import BaseAgent

SYSTEM_PROMPT = """Eres un experto en marketing de ciclo de vida para negocios digitales.
Creas secuencias de email y WhatsApp que convierten leads en clientes usando el lenguaje exacto de la audiencia.

Adapta el tono según el tipo de negocio:
- saas: educacional, ROI, casos de uso, "en X minutos puedes..."
- ecommerce: urgencia, escasez, prueba social, descuentos tiempo-limitado
- services: credibilidad, proceso claro, casos de éxito, quién eres
- app: beneficio inmediato, tutorial, hábito de uso, gamification
- local: cercanía, oferta exclusiva, urgencia temporal, reseñas

Reglas siempre:
- El PRIMER mensaje se envía inmediatamente y tiene UNA acción clara basada en el objetivo post-conversión
- Cada mensaje tiene UN solo CTA, nunca dos
- Email: sujeto con curiosity gap o promesa concreta, menos de 50 caracteres
- WhatsApp: mensajes cortos (max 160 chars), naturales, como amigo que ayuda — nunca corporativo
- Cuerpo conversacional, como si fuera de persona a persona, no corporativo
- Progresión lógica: bienvenida → valor → urgencia → oferta final
- Usa frases textuales de los pain points de la audiencia"""


POST_CONVERSION_CONFIGS: dict[str, dict] = {
    "schedule_meeting": {
        "first_email_cta": "Agenda tu sesión gratuita",
        "first_email_goal": "conseguir que agende una reunión usando el enlace proporcionado",
        "sequence_tone": "consultivo, crea expectativa de lo que se hablará en la llamada",
        "urgency_trigger": "plazas limitadas esta semana",
        "first_whatsapp_hook": "¡Tu plaza está reservada! 🎯 Agenda tu sesión aquí:",
    },
    "free_trial": {
        "first_email_cta": "Empieza tu prueba gratis",
        "first_email_goal": "conseguir que active el trial haciendo clic en el enlace",
        "sequence_tone": "educacional, muestra quick wins que puede lograr en los primeros días",
        "urgency_trigger": "el trial dura 7 días, no lo desperdicies",
        "first_whatsapp_hook": "¡Todo listo! Empieza tu prueba gratis ahora 👇",
    },
    "demo_request": {
        "first_email_cta": "Ver la demo personalizada",
        "first_email_goal": "que vea la demo grabada o confirme una demo en vivo",
        "sequence_tone": "valor de producto, muestra el antes/después de usar la herramienta",
        "urgency_trigger": "la demo revela el flujo exacto que más tiempo te ahorra",
        "first_whatsapp_hook": "Tu demo está lista 🎬 Mírala en 3 minutos:",
    },
    "download": {
        "first_email_cta": "Descargar ahora",
        "first_email_goal": "entregar el recurso prometido y crear expectativa del siguiente paso",
        "sequence_tone": "educacional, da valor inmediato del recurso descargado",
        "urgency_trigger": "implementa esto esta semana para ver resultados",
        "first_whatsapp_hook": "¡Aquí está tu recurso! Descárgalo 👇",
    },
    "thank_you_only": {
        "first_email_cta": "Cuéntame más sobre ti",
        "first_email_goal": "confirmar el registro y abrir conversación, pedir respuesta directa",
        "sequence_tone": "conversacional, cercano, preguntas que cualifican al lead",
        "urgency_trigger": "plazas de onboarding limitadas este mes",
        "first_whatsapp_hook": "¡Genial que estés aquí! Cuéntame, ¿qué buscas exactamente?",
    },
    "community": {
        "first_email_cta": "Unirme a la comunidad",
        "first_email_goal": "que se una al canal (Slack, Discord, grupo) usando el enlace",
        "sequence_tone": "comunidad y pertenencia, quiénes más están dentro, qué se comparte",
        "urgency_trigger": "esta semana se discute X tema en el canal",
        "first_whatsapp_hook": "¡Bienvenido/a! Únete a la comunidad ahora 👇",
    },
    "pricing_page": {
        "first_email_cta": "Ver planes y precios",
        "first_email_goal": "llevar al lead a la página de pricing para que elija plan",
        "sequence_tone": "comparativo, ROI claro, elimina objeciones de precio",
        "urgency_trigger": "precio especial para los primeros inscritos",
        "first_whatsapp_hook": "¡Hola! Aquí tienes nuestros planes 👇 Elige el tuyo:",
    },
}


class EmailAgent(BaseAgent):
    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("model", "gpt-4o")
        super().__init__(**kwargs)
        self.system_prompt = SYSTEM_PROMPT

    def _build_context(self, research: dict, copy: dict) -> str:
        lines = []
        if research.get("key_insight"):
            lines.append(f"Key insight: {research['key_insight']}")
        pain_points = research.get("pain_points", [])
        if pain_points:
            lines.append("Pain points reales:")
            for pp in pain_points[:4]:
                lines.append(f'  • "{pp.get("phrase", "")}"')
        audience_lang = research.get("audience_language", [])
        if audience_lang:
            lines.append("Frases textuales de la audiencia: " + ", ".join(f'"{p}"' for p in audience_lang[:6]))
        copies = copy.get("copies", [])
        if copies:
            top = copies[0]
            lines.append(f"Hook del anuncio (narrative thread): {top.get('hook', '')}")
            lines.append(f"Ángulo principal: {top.get('angle', '')}")
        return "\n".join(lines)

    async def _generate_sequence(
        self,
        business: str,
        business_type: str,
        audience: str,
        campaign_type: str,
        post_conversion_goal: str,
        post_conversion_url: str,
        context_str: str,
        funnel_type: str | None = None,
        sale_type: str | None = None,
        redirect_url: str | None = None,
        lead_magnet_url: str | None = None,
        sale_landing_url: str | None = None,
    ) -> dict:
        goal_config = POST_CONVERSION_CONFIGS.get(
            post_conversion_goal, POST_CONVERSION_CONFIGS["thank_you_only"]
        )

        num_emails = 3 if campaign_type == "validation" else 5

        # Determinar URL principal del CTA según funnel_type
        # - landing_lm_direct: emails 2-5 apuntan a sale_landing_url (landing venta propia)
        # - landing_lm: emails 2-5 apuntan a redirect_url (Calendly/pago externo)
        # - landing_direct/instant_form: usar post_conversion_url
        if funnel_type == "landing_lm_direct" and sale_landing_url:
            primary_cta_url = sale_landing_url
        elif funnel_type == "landing_lm" and redirect_url:
            primary_cta_url = redirect_url
        else:
            primary_cta_url = post_conversion_url

        sale_label = ""
        if sale_type == "call":
            sale_label = "agendar una llamada"
        elif sale_type == "payment":
            sale_label = "completar la compra"

        lm_instruction = ""
        if lead_magnet_url:
            lm_instruction = f"""
EMAIL #1 ESPECIAL — ENTREGA EL LEAD MAGNET:
El primer email DEBE entregar el PDF del lead magnet. Incluye un link de descarga directa al PDF.
URL del PDF: {lead_magnet_url}
El CTA principal del email #1 debe ser "Descargar el PDF" (NO el CTA genérico {goal_config['first_email_cta']}).
En el cuerpo, presenta el PDF como el primer regalo + adelanta que en los próximos días enviarás más valor."""

        url_instruction = (
            f"URL principal de los emails 2-{num_emails}: {primary_cta_url}"
            + (f" ({sale_label})" if sale_label else "")
            if primary_cta_url
            else "No hay URL específica — usa un CTA genérico y descriptivo."
        )

        prompt = f"""Genera una secuencia de {num_emails} emails de nurturing post-lead.

NEGOCIO: {business}
TIPO: {business_type}
AUDIENCIA: {audience}
TIPO DE CAMPAÑA: {campaign_type}
FUNNEL_TYPE: {funnel_type or "n/a"}
SALE_TYPE: {sale_type or "n/a"}
OBJETIVO POST-CONVERSIÓN: {post_conversion_goal}
CTA DEL PRIMER EMAIL: "{goal_config['first_email_cta']}"
OBJETIVO DEL PRIMER EMAIL: {goal_config['first_email_goal']}
TONO DE LA SECUENCIA: {goal_config['sequence_tone']}
TRIGGER DE URGENCIA A USAR: {goal_config['urgency_trigger']}
{url_instruction}
{lm_instruction}

REGLA DE NARRATIVE THREAD (message match):
El lead llegó porque un anuncio hizo una promesa específica (ver "Hook del anuncio" en contexto).
TODOS los emails deben mantener coherencia con ese hook. Reglas:
- Email #1: referencia explícitamente el hook del anuncio ("como prometimos...")
- Emails #2-#4: desarrollan el MECANISMO o el MÉTODO detrás de esa promesa
- Email #5: retoma el hook original para cerrar el ciclo narrativo antes de la urgencia final
No cambies el tema ni introduces ángulos nuevos que no estén en el hook original.

CONTEXTO DE INVESTIGACIÓN:
{context_str}

ESTRUCTURA OBLIGATORIA:
- Email 1 (delay 0h): Bienvenida inmediata + CTA principal → {goal_config['first_email_cta']}
- Email 2 (delay 1 día): Valor puro — da el insight más valioso para la audiencia, sin pedir nada
- Email 3 (delay 3 días): Caso de éxito o prueba social relacionada con su pain point principal
{"- Email 4 (delay 6 días): Objeción más común + cómo la resuelves (precio, tiempo, esfuerzo)" if num_emails >= 4 else ""}
{"- Email 5 (delay 10 días): Urgencia final — oferta, deadline, o consecuencia de no actuar" if num_emails >= 5 else ""}

Devuelve SOLO JSON:
{{
  "post_conversion_goal": "{post_conversion_goal}",
  "post_conversion_url": "{post_conversion_url}",
  "emails": [
    {{
      "order": 1,
      "send_delay_hours": 0,
      "subject": "asunto con curiosity gap o promesa directa (max 50 chars)",
      "preview_text": "texto preview del email (max 90 chars)",
      "body_html": "cuerpo completo en HTML simple (solo p, strong, a, br tags). Conversacional, no corporativo. UN solo CTA.",
      "cta_text": "texto del botón CTA",
      "cta_url": "{primary_cta_url if primary_cta_url else 'https://PLACEHOLDER'}",
      "goal": "qué debe hacer el lector al terminar de leer"
    }}
  ]
}}"""

        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=4096,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        return json.loads(response.choices[0].message.content or "{}")

    async def _generate_whatsapp_sequence(
        self,
        business: str,
        business_type: str,
        audience: str,
        campaign_type: str,
        post_conversion_goal: str,
        post_conversion_url: str,
        context_str: str,
        funnel_type: str | None = None,
        sale_type: str | None = None,
        redirect_url: str | None = None,
        lead_magnet_url: str | None = None,
        sale_landing_url: str | None = None,
    ) -> dict:
        goal_config = POST_CONVERSION_CONFIGS.get(
            post_conversion_goal, POST_CONVERSION_CONFIGS["thank_you_only"]
        )

        num_msgs = 3 if campaign_type == "validation" else 5

        if funnel_type == "landing_lm_direct" and sale_landing_url:
            primary_cta_url = sale_landing_url
        elif funnel_type == "landing_lm" and redirect_url:
            primary_cta_url = redirect_url
        else:
            primary_cta_url = post_conversion_url

        lm_extra = f"\nLEAD MAGNET URL: {lead_magnet_url} (mensaje #1 debe entregar este enlace)" if lead_magnet_url else ""

        url_instruction = (
            f"El enlace principal (mensajes 2-{num_msgs}) es: {primary_cta_url}"
            if primary_cta_url
            else "No hay URL específica — usa un CTA genérico."
        ) + lm_extra

        prompt = f"""Genera una secuencia de {num_msgs} mensajes de WhatsApp de nurturing post-lead.

NEGOCIO: {business}
TIPO: {business_type}
AUDIENCIA: {audience}
OBJETIVO POST-CONVERSIÓN: {post_conversion_goal}
HOOK DEL PRIMER MENSAJE: "{goal_config['first_whatsapp_hook']}"
TONO: {goal_config['sequence_tone']}
TRIGGER DE URGENCIA: {goal_config['urgency_trigger']}
{url_instruction}

REGLAS CRÍTICAS PARA WHATSAPP:
- Máximo 160 caracteres por mensaje
- Lenguaje natural, como un amigo — nunca corporativo
- Emojis permitidos (1-2 por mensaje, no abusar)
- Si hay URL, ponerla al final del mensaje
- Sin saludos formales ("Estimado/a", "Le informamos que...")
- Directo, conversacional, con una sola idea por mensaje

ESTRUCTURA OBLIGATORIA:
- Msg 1 (delay 0h): Bienvenida + enlace de acción inmediata
- Msg 2 (delay 1 día): Tip o insight de valor sin pedir nada
- Msg 3 (delay 3 días): Prueba social o resultado concreto
{"- Msg 4 (delay 6 días): Respuesta a la objeción más común" if num_msgs >= 4 else ""}
{"- Msg 5 (delay 10 días): Urgencia final — cierre o consecuencia" if num_msgs >= 5 else ""}

Devuelve SOLO JSON:
{{
  "post_conversion_goal": "{post_conversion_goal}",
  "messages": [
    {{
      "order": 1,
      "send_delay_hours": 0,
      "text": "mensaje completo (max 160 chars, incluye URL si aplica)",
      "goal": "qué debe hacer el lead al leer este mensaje"
    }}
  ]
}}"""

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

    async def _generate_thanks_page_content(
        self,
        business: str,
        post_conversion_goal: str,
        post_conversion_url: str,
    ) -> dict:
        goal_config = POST_CONVERSION_CONFIGS.get(
            post_conversion_goal, POST_CONVERSION_CONFIGS["thank_you_only"]
        )

        prompt = f"""Genera el contenido de una página de "Gracias" que aparece tras enviar el formulario.

Negocio: {business}
Objetivo post-conversión: {post_conversion_goal}
CTA principal: {goal_config['first_email_cta']}
URL del CTA: {post_conversion_url or "PLACEHOLDER"}

La página debe:
1. Confirmar que recibieron los datos (entusiasmo, no corporativo)
2. Decirles exactamente qué pasa ahora (expectativa clara)
3. Presentar UNA acción adicional de alto valor basada en el objetivo post-conversión
4. Ser concisa — menos es más

Devuelve SOLO JSON:
{{
  "headline": "Titular de confirmación (entusiasta, max 6 palabras)",
  "subheadline": "Qué pasa ahora — explica el siguiente paso esperado (1 frase)",
  "next_step_title": "Título del bloque de acción adicional",
  "next_step_description": "Descripción de por qué hacer esta acción ahora (1-2 frases, usa el lenguaje de la audiencia)",
  "next_step_cta_text": "{goal_config['first_email_cta']}",
  "next_step_cta_url": "{post_conversion_url or 'PLACEHOLDER'}",
  "ps_text": "Posdata opcional — algo que genere curiosidad o expectativa del primer email"
}}"""

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=800,
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
        landing = context.get("LandingAgent", {})
        lead_magnet = context.get("LeadMagnetAgent", {})

        business = step.get("business_description") or step.get("saas_description", "")
        business_type = step.get("business_type", "saas")
        audience = step.get("target_customer") or step.get("target_audience", "audiencia objetivo")
        campaign_type = step.get("campaign_type", "lead_gen")
        post_conversion_goal = step.get("post_conversion_goal", "thank_you_only")
        post_conversion_url = step.get("post_conversion_url", "")
        funnel_type = step.get("funnel_type")
        sale_type = step.get("sale_type")
        redirect_url = step.get("redirect_url")
        frontend_url = step.get("frontend_url", "")

        lead_magnet_url = lead_magnet.get("pdf_url")

        # Construir URL de landing de venta (subtype=sale) si existe (landing_lm_direct)
        sale_landing_url: str | None = None
        by_subtype = landing.get("by_subtype", {})
        sale_data = by_subtype.get("sale") if isinstance(by_subtype, dict) else None
        if sale_data:
            sale_ids = sale_data.get("landing_ids", {})
            if sale_ids.get("a"):
                base = frontend_url or "https://app.growthOS.io"
                sale_landing_url = f"{base}/landing/{sale_ids['a']}"

        context_str = self._build_context(research, copy)

        sequence_task = self._generate_sequence(
            business=business,
            business_type=business_type,
            audience=audience,
            campaign_type=campaign_type,
            post_conversion_goal=post_conversion_goal,
            post_conversion_url=post_conversion_url,
            context_str=context_str,
            funnel_type=funnel_type,
            sale_type=sale_type,
            redirect_url=redirect_url,
            lead_magnet_url=lead_magnet_url,
            sale_landing_url=sale_landing_url,
        )

        whatsapp_task = self._generate_whatsapp_sequence(
            business=business,
            business_type=business_type,
            audience=audience,
            campaign_type=campaign_type,
            post_conversion_goal=post_conversion_goal,
            post_conversion_url=post_conversion_url,
            context_str=context_str,
            funnel_type=funnel_type,
            sale_type=sale_type,
            redirect_url=redirect_url,
            lead_magnet_url=lead_magnet_url,
            sale_landing_url=sale_landing_url,
        )

        thanks_task = self._generate_thanks_page_content(
            business=business,
            post_conversion_goal=post_conversion_goal,
            post_conversion_url=post_conversion_url,
        )

        sequence_result, whatsapp_result, thanks_result = await asyncio.gather(
            sequence_task, whatsapp_task, thanks_task
        )

        return {
            "email_sequence": sequence_result,
            "whatsapp_sequence": whatsapp_result,
            "thanks_page": thanks_result,
            "post_conversion_goal": post_conversion_goal,
            "post_conversion_url": post_conversion_url,
            "funnel_type": funnel_type,
            "sale_type": sale_type,
            "lead_magnet_url": lead_magnet_url,
            "sale_landing_url": sale_landing_url,
        }
