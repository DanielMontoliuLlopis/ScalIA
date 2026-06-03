import json
import uuid
from typing import Any

from app.agents.base import BaseAgent

SYSTEM_PROMPT = """Eres el OrchestratorAgent de Growth OS, un sistema de marketing autónomo para cualquier tipo de negocio digital.

Tu objetivo es crear planes de marketing altamente específicos y accionables. Para eso necesitas conocer bien el negocio antes de crear el plan.

## CONTEXTO DE EMPRESA (pre-cargado)
Al inicio de cada conversación recibirás un bloque <company_profile> con los datos del negocio que el usuario ya configuró en Settings: nombre, descripción y tipo. Úsalos directamente — NO vuelvas a preguntar por esos datos si ya están disponibles. Si el bloque indica que faltan campos, pide al usuario que los configure antes de continuar.

## PROCESO OBLIGATORIO

### Paso 1 — Briefing (UNA SOLA RONDA)
Si el usuario no ha dado suficiente información en su PRIMER mensaje, usa `request_clarification` UNA sola vez con TODAS las preguntas. Solo pregunta cosas que el usuario puede saber sin conocer marketing:

1. ¿Qué hace tu producto/servicio? Descríbelo como se lo explicarías a un amigo.
2. ¿A quién va dirigido? ¿Quién es la persona que más lo necesita?
3. ¿Qué problema concreto les resuelves? ¿Qué hacían antes de encontrarte?
4. ¿Tienes ya clientes o usuarios? Si los tienes, ¿qué te dicen que más les gusta?
5. ¿Cuánto quieres gastar al mes en publicidad?
6. ¿En qué país o ciudad quieres anunciarte?
7. ¿Qué quieres que haga el cliente cuando te contacte? Por ejemplo: agendar una llamada (pega el enlace de Calendly u otra herramienta), probar el producto gratis (pega la URL del registro), ver una demo, descargar algo, o simplemente que te dejen sus datos y ya les contactas tú.
8. ¿A qué precio vendes? (solo el número, ej: 97). Si es gratis o freemium, escribe 0.
9. ¿Qué resultado concreto consigue el cliente contigo? Sé específico (ej: "ahorrar 5 horas a la semana", "conseguir 10 clientes nuevos al mes", "perder 8kg en 2 meses").
10. ¿Ofreces alguna garantía? (ej: 30 días de devolución, garantía de resultados, sin contrato). Si no tienes ninguna, escribe "ninguna".
11. ¿Quieres testear varias versiones del anuncio (A/B) o lanzar una sola versión? Por defecto lanzamos una sola — el A/B duplica el coste de generación y solo merece la pena con cierto presupuesto.

Si el <company_profile> ya tiene descripción y tipo de negocio, omite la pregunta 1 (ya la sabes) y empieza desde la 2.
Pregunta 7 es clave: si tienen un enlace (Calendly, trial, demo), que lo peguen aquí. Si no, di "no tengo" y lo gestionamos nosotros.
Pregunta 8: usa el precio para calibrar el copy y el Offer Engine — no lo preguntes en segunda ronda.
Pregunta 9: esta es la `transformacion` del Offer Engine — el hook principal de todos los copies. Es el campo más importante.
Pregunta 10: mapea a `garantia`. Si dice "ninguna" → `sin_garantia`.
Pregunta 11: si el usuario no menciona A/B explícitamente, asume `ab_testing=false` (versión única).

REGLA CRÍTICA: si en el historial ya hay un `request_clarification` previo, NO vuelvas a llamar `request_clarification`. Pasa directamente a `create_plan` con la información que tengas. INFIERE lo que falte (precio, características técnicas, testimoniales, soporte, estrategia de atracción — todo eso lo decides tú como experto). Nunca pidas detalles técnicos del producto, precio exacto, testimonios, soporte ni estrategia de marketing en una segunda ronda.

NO preguntes sobre estrategia, objetivos de marketing, tipos de campaña, KPIs, precios, testimonios, soporte ni características técnicas — eso lo decides tú como experto en base a sus respuestas.

### Paso 2 — Crear el plan
Con las respuestas del usuario, TÚ decides:
- El tipo de campaña más adecuado (validación, leads, ventas)
- Los canales y agentes a usar
- La estrategia de targeting y mensajes
- Si es un lanzamiento nuevo con poco presupuesto → validación primero
- Si tiene clientes y presupuesto → campaña de leads/ventas directa

NUNCA crees el plan sin saber qué vende y a quién.
NUNCA respondas con texto sin llamar a una tool.

## OFFER ENGINE — captura estructurada de la oferta

Usa las respuestas del briefing (preguntas 8, 9, 10) para poblar estos campos. Si el usuario los respondió, úsalos directamente. Si no los respondió en el briefing, infiere:

- `precio_base`: de la respuesta a "¿A qué precio vendes?". Si dijo 0 → 0.
- `tipo_oferta`: `evergreen` | `lanzamiento` | `descuento_limitado` | `prueba_gratuita`. Infiere según el negocio y precio.
- `urgencia`: `sin_urgencia` | `fecha_limite` | `plazas_limitadas` | `bonus_temporal`. Default: `sin_urgencia`.
- `garantia`: de la respuesta a "¿Ofreces garantía?". Mapea: "30 días" → `devolucion_X_dias`, "satisfacción" → `satisfaccion`, "resultados" → `resultados`, "ninguna" → `sin_garantia`.
- `transformacion`: de la respuesta a "¿Qué resultado concreto consigue el cliente?". Es el hook central de todos los copies — usa la frase exacta del usuario.

Incluye siempre los 5 campos en `create_plan`.

## TIPOS DE NEGOCIO
- saas: software B2B/B2C, suscripciones → copies de trial, ROI, ahorro de tiempo
- ecommerce: productos físicos, dropshipping → copies de producto, urgencia, prueba social
- services: consultoría, agencias, freelancers → copies de credibilidad, resultados, proceso
- app: apps móviles/web → copies de descarga, beneficio inmediato
- local: negocios físicos → copies de cercanía, oferta, urgencia temporal

## OBJETIVOS DE CAMPAÑA Y CÓMO TRATARLOS

### Validación de idea/producto
El usuario quiere saber si hay demanda ANTES de construir o invertir en serio.
- Presupuesto pequeño (€1-50/día) con objetivo de medir CTR e interés real
- Landing page con waitlist o formulario "quiero ser el primero en saberlo"
- La métrica de éxito es: ¿la gente hace clic? ¿deja su email?
- Copies que presentan la promesa del producto como si ya existiera ("pronto disponible")
- AdsAgent genera campaña de validación con objetivo AWARENESS o LEAD_GENERATION
- post_conversion_goal: "thank_you_only" (sin URL de acción, aún no existe el producto)
- Las métricas se monitorean desde el Dashboard (Meta Insights API), NO hay AnalyticsAgent

### Generación de leads
- Landing page con formulario cualificador
- AdsAgent con objetivo LEAD_GENERATION
- EmailAgent para nurturing de los leads captados
- Debes decidir el post_conversion_goal más adecuado según el negocio:
  * SaaS con trial activo → "free_trial" + URL del trial
  * SaaS/services que venden por llamada → "schedule_meeting" + URL de Calendly o similar
  * SaaS sin trial / en construcción → "demo_request" + URL de demo grabada si existe
  * Contenido o recurso descargable → "download" + URL del recurso
  * Comunidad o programa → "community" + URL del canal

### Ventas directas
- Landing page con CTA directo a pricing o checkout
- AdsAgent con objetivo CONVERSIONS
- campaign_type: "direct_sale" con redirect_url al checkout del cliente
- post_conversion_goal: "pricing_page" + redirect_url del cliente

## OBJETIVO POST-CONVERSIÓN (post_conversion_goal)
Valores válidos: "schedule_meeting", "free_trial", "demo_request", "download", "thank_you_only", "community", "pricing_page"

Reglas de inferencia (aplica en orden, usa la primera que aplique):
1. Si el usuario mencionó "trial", "prueba gratuita", "probar gratis", "free trial" → `free_trial` + URL del registro
2. Si pegó una URL de Calendly, "llamada", "agendar", "reservar" → `schedule_meeting` + URL Calendly
3. Si mencionó "demo", "demostración" → `demo_request` + URL demo (si existe)
4. Si mencionó "descargar", "PDF", "guía", "recurso" → `download` + URL recurso
5. Si mencionó "comunidad", "Discord", "Slack", "grupo" → `community` + URL comunidad
6. Si mencionó "pricing", "precios", "comprar", "checkout" → `pricing_page` + URL pricing
7. Si no tiene URL ni acción clara → `thank_you_only` + post_conversion_url vacío

CRÍTICO: Si el usuario dice "trial de X días", el goal es `free_trial`, NUNCA `demo_request`.
Si el usuario ha dado una URL relevante (Calendly, trial, demo), úsala como post_conversion_url.

IMPORTANTE: El post_conversion_goal se usa en:
1. La página de gracias de la landing (qué CTA aparece tras enviar el form)
2. La secuencia de emails (el primer email lleva exactamente a esa acción)

## AL CREAR EL PLAN
- Título: negocio concreto + objetivo específico.
- Descripción: estrategia concreta adaptada al negocio y objetivo, no genérica.
- Agentes disponibles ÚNICAMENTE: ResearchAgent, CopyAgent, MetaPolicyAgent, LandingAgent, LeadMagnetAgent, AdsAgent, EmailAgent, CRMAgent.
- NO inventes agentes (no existe SocialMediaAgent, ContentAgent, SEOAgent, AnalyticsAgent, etc.).
- IMPORTANTE: el plan inicial SOLO contiene 3 steps: ResearchAgent → CopyAgent → MetaPolicyAgent.
- Tras MetaPolicyAgent el plan pausa para que el usuario elija funnel_type. NO incluyas LandingAgent, LeadMagnetAgent, AdsAgent, EmailAgent, CRMAgent en el plan inicial — esos steps los añade el endpoint `/funnel-choice` automáticamente.
- Cada step DEBE tener:
  * "business_description": descripción concreta y detallada del negocio
  * "business_type": saas/ecommerce/services/app/local
  * "target_customer": perfil detallado del cliente final (edad, situación, dolor específico)
  * "description": tarea específica del step
- Exactamente 3 pasos. estimated_time realista.

Tras `create_plan`, escribe 1-2 frases confirmando que el plan está listo. Menciona brevemente que desde la sección de Campañas pueden crear un **test de oferta alternativa** (10% del presupuesto) para comparar qué transformación o garantía convierte mejor. NO repitas el contenido del plan.
Responde siempre en el idioma del usuario."""


class OrchestratorAgent(BaseAgent):
    def __init__(
        self,
        db: Any,
        user_id: uuid.UUID,
        client_account_id: uuid.UUID,
        allow_clarification: bool = True,
        company_profile: dict | None = None,
    ) -> None:
        super().__init__()
        self.system_prompt = SYSTEM_PROMPT

        if company_profile:
            missing = company_profile.get("missing", [])
            if missing:
                profile_block = (
                    f"\n\n<company_profile>\n"
                    f"INCOMPLETO — faltan campos obligatorios: {', '.join(missing)}.\n"
                    f"Indica al usuario que debe completar su perfil de empresa en Ajustes antes de crear una campaña.\n"
                    f"No crees ningún plan hasta que esté completo.\n"
                    f"</company_profile>"
                )
            else:
                profile_block = (
                    f"\n\n<company_profile>\n"
                    f"Nombre: {company_profile.get('company_name', '')}\n"
                    f"Descripción: {company_profile.get('business_description', '')}\n"
                    f"Tipo de negocio: {company_profile.get('business_type', '')}\n"
                    f"</company_profile>"
                )
            self.system_prompt += profile_block

        if not allow_clarification:
            self.system_prompt += (
                "\n\n## BLOQUEO ACTIVO\n"
                "Ya hiciste el briefing inicial al usuario en un mensaje anterior. "
                "NO puedes pedir más aclaraciones. Llama `create_plan` AHORA con la información disponible, "
                "infiriendo lo que falte."
            )
        self.db = db
        self.user_id = user_id
        self.client_account_id = client_account_id
        self._created_plan_id: str | None = None
        self._clarification_fields: list | None = None
        clarification_tool = {
            "name": "request_clarification",
            "description": "Solicita información al usuario. Usa esta tool para hacer el briefing completo del negocio. Incluye TODAS las preguntas en un solo mensaje.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Preguntas para el usuario. Pueden ser múltiples preguntas en un solo mensaje, numeradas y claras.",
                    }
                },
                "required": ["question"],
            },
        }
        self.tools = [
            {
                "name": "create_plan",
                "description": "Crea un plan de marketing estructurado y lo guarda en la base de datos para que el usuario lo apruebe antes de ejecutarlo.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Título conciso que incluye el negocio y el objetivo principal",
                        },
                        "description": {
                            "type": "string",
                            "description": "Descripción de la estrategia general en 2-3 frases",
                        },
                        "business_description": {
                            "type": "string",
                            "description": "Descripción concreta del negocio del usuario (ej: 'tienda dropshipping de tiras nasales para mejorar el sueño'). Se inyectará en todos los pasos automáticamente.",
                        },
                        "business_type": {
                            "type": "string",
                            "enum": ["saas", "ecommerce", "services", "app", "local"],
                            "description": "Tipo de negocio detectado",
                        },
                        "target_customer": {
                            "type": "string",
                            "description": "Perfil detallado del cliente final (edad, situación, dolor específico)",
                        },
                        "post_conversion_goal": {
                            "type": "string",
                            "enum": ["schedule_meeting", "free_trial", "demo_request", "download", "thank_you_only", "community", "pricing_page"],
                            "description": "Qué debe hacer el lead tras enviar el formulario. Determina el CTA de la página de gracias y el primer email.",
                        },
                        "monthly_budget": {
                            "type": "number",
                            "description": "Presupuesto mensual en euros que indicó el usuario (número puro, ej: 30). OBLIGATORIO si el usuario lo mencionó.",
                        },
                        "post_conversion_url": {
                            "type": "string",
                            "description": "URL de la acción post-conversión (Calendly, trial, demo, etc.). Vacío si no existe.",
                        },
                        "ab_testing": {
                            "type": "boolean",
                            "description": "true si el usuario quiere testear varias versiones A/B del anuncio y landing. false (default) para lanzar una sola versión. Solo poner true si el usuario lo pidió explícitamente.",
                        },
                        "precio_base": {
                            "type": "number",
                            "description": "Precio principal del producto/servicio (número, sin símbolo). Infiere si no lo mencionó.",
                        },
                        "tipo_oferta": {
                            "type": "string",
                            "enum": ["evergreen", "lanzamiento", "descuento_limitado", "prueba_gratuita"],
                            "description": "Tipo de oferta detectado. Infiere según el negocio.",
                        },
                        "urgencia": {
                            "type": "string",
                            "enum": ["sin_urgencia", "fecha_limite", "plazas_limitadas", "bonus_temporal"],
                            "description": "Tipo de urgencia. Default: sin_urgencia.",
                        },
                        "garantia": {
                            "type": "string",
                            "enum": ["sin_garantia", "satisfaccion", "resultados", "devolucion_X_dias"],
                            "description": "Tipo de garantía. Default: sin_garantia.",
                        },
                        "transformacion": {
                            "type": "string",
                            "description": "Resultado específico que promete el negocio (ej: 'bajar 10kg en 12 semanas'). Infiere del negocio.",
                        },
                        "steps": {
                            "type": "array",
                            "description": "Pasos del plan en orden de ejecución (4-6 pasos)",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "agent": {"type": "string", "description": "Nombre del agente (ej: CopyAgent)"},
                                    "action": {"type": "string", "description": "Nombre de la acción (ej: generate_copy)"},
                                    "description": {"type": "string", "description": "Tarea específica del step, no el nombre del negocio"},
                                    "business_description": {"type": "string", "description": "Descripción concreta del negocio. OBLIGATORIO."},
                                    "business_type": {"type": "string", "enum": ["saas", "ecommerce", "services", "app", "local"]},
                                    "target_customer": {"type": "string", "description": "Perfil detallado del cliente final"},
                                    "estimated_time": {"type": "string", "description": "Tiempo estimado (ej: '2 horas')"},
                                },
                                "required": ["agent", "action", "description", "business_description", "business_type", "target_customer", "estimated_time"],
                            },
                        },
                    },
                    "required": ["title", "description", "business_description", "business_type", "target_customer", "post_conversion_goal", "steps"],
                },
            },
        ]
        if allow_clarification:
            self.tools.append(clarification_tool)

    async def tool_create_plan(self, tool_input: dict) -> str:
        from app.models.plan import Plan, PlanStatus

        business_description = tool_input.get("business_description", "")
        business_type = tool_input.get("business_type", "saas")
        target_customer = tool_input.get("target_customer", "")
        post_conversion_goal = tool_input.get("post_conversion_goal", "thank_you_only")
        post_conversion_url = tool_input.get("post_conversion_url", "")
        monthly_budget = tool_input.get("monthly_budget")
        ab_testing = bool(tool_input.get("ab_testing", False))
        precio_base = tool_input.get("precio_base")
        tipo_oferta = tool_input.get("tipo_oferta", "evergreen")
        urgencia = tool_input.get("urgencia", "sin_urgencia")
        garantia = tool_input.get("garantia", "sin_garantia")
        transformacion = tool_input.get("transformacion", "")

        steps_raw = tool_input.get("steps", [])
        steps = [
            {
                "order": i + 1,
                "agent": s.get("agent", "").removeprefix("functions."),
                "action": s.get("action", ""),
                "description": s.get("description", ""),
                "estimated_time": s.get("estimated_time", ""),
                "business_description": s.get("business_description") or business_description,
                "business_type": s.get("business_type") or business_type,
                "target_customer": s.get("target_customer") or target_customer,
                "post_conversion_goal": post_conversion_goal,
                "post_conversion_url": post_conversion_url,
                "ab_testing": ab_testing,
                "tipo_oferta": tipo_oferta,
                "urgencia": urgencia,
                "garantia": garantia,
                "transformacion": transformacion,
                **({"monthly_budget": monthly_budget} if monthly_budget is not None else {}),
                **({"precio_base": precio_base} if precio_base is not None else {}),
            }
            for i, s in enumerate(steps_raw)
        ]

        plan = Plan(
            user_id=self.user_id,
            client_account_id=self.client_account_id,
            title=tool_input.get("title", "Plan sin título"),
            description=tool_input.get("description", ""),
            steps=steps,
            status=PlanStatus.pending_approval,
            ab_testing=ab_testing,
            precio_base=precio_base,
            tipo_oferta=tipo_oferta,
            urgencia=urgencia,
            garantia=garantia,
            transformacion=transformacion,
        )
        self.db.add(plan)
        await self.db.flush()

        self._created_plan_id = str(plan.id)
        return json.dumps({"plan_id": self._created_plan_id, "status": "created"})

    async def _tool_publish_campaign_disabled(self, tool_input: dict) -> str:
        from sqlalchemy import select
        from app.models.plan import Plan
        from app.models.task import AgentTask
        from app.models.user_settings import UserSettings
        from app.tools.meta_ads import publish_campaign, MetaAdsError

        plan_id_str = tool_input.get("plan_id")

        # Find the plan
        if plan_id_str:
            import uuid as _uuid
            plan_result = await self.db.execute(
                select(Plan).where(Plan.id == _uuid.UUID(plan_id_str), Plan.user_id == self.user_id)
            )
        else:
            plan_result = await self.db.execute(
                select(Plan)
                .where(Plan.user_id == self.user_id)
                .order_by(Plan.created_at.desc())
                .limit(1)
            )
        plan = plan_result.scalar_one_or_none()
        if not plan:
            return json.dumps({"error": "No se encontró ningún plan."})

        # Get user settings
        settings_result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == self.user_id)
        )
        settings = settings_result.scalar_one_or_none()
        if not settings or not settings.meta_access_token or not settings.meta_ad_account_id:
            return json.dumps({"error": "Falta configurar Meta Access Token y Ad Account ID en Ajustes."})

        # Get AdsAgent output
        task_result = await self.db.execute(
            select(AgentTask).where(
                AgentTask.plan_id == plan.id,
                AgentTask.agent_name == "AdsAgent",
                AgentTask.status == "completed",
            )
        )
        ads_task = task_result.scalar_one_or_none()
        if not ads_task or not ads_task.output:
            return json.dumps({"error": "El AdsAgent aún no ha generado la campaña para este plan."})

        campaign_json = ads_task.output.get("campaign_json")
        if not campaign_json:
            return json.dumps({"error": "No hay campaign_json en el output del AdsAgent."})

        _objective_map = {
            "LEAD_GENERATION": "OUTCOME_LEADS",
            "CONVERSIONS": "OUTCOME_SALES",
            "TRAFFIC": "OUTCOME_TRAFFIC",
            "BRAND_AWARENESS": "OUTCOME_AWARENESS",
            "REACH": "OUTCOME_AWARENESS",
            "ENGAGEMENT": "OUTCOME_ENGAGEMENT",
            "APP_INSTALLS": "OUTCOME_APP_PROMOTION",
        }
        if "campaign" in campaign_json:
            obj = campaign_json["campaign"].get("objective", "")
            campaign_json["campaign"]["objective"] = _objective_map.get(obj, obj)

        try:
            result = await publish_campaign(
                access_token=settings.meta_access_token,
                ad_account_id=settings.meta_ad_account_id,
                campaign_json=campaign_json,
            )
        except MetaAdsError as e:
            return json.dumps({"error": f"Error Meta API: {e}"})

        return json.dumps({
            "published": True,
            "campaign_title": plan.title,
            "campaign_id": result["campaign_id"],
            "ad_set_id": result["ad_set_id"],
            "ad_ids": result["ad_ids"],
            "meta_ads_manager_url": result["meta_ads_manager_url"],
            "note": "Campaña creada en Meta en modo PAUSED. Actívala desde Meta Ads Manager cuando estés listo.",
        })

    def _parse_questions_to_fields(self, question_text: str) -> list[dict]:
        """Convierte el texto de preguntas numeradas en campos de formulario estructurados."""
        import re
        # Split tanto por saltos de línea como por números inline "2. ", "3. " etc.
        normalized = re.sub(r'\s+(\d+[.)]\s)', r'\n\1', question_text.strip())
        lines = normalized.split("\n")
        fields = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Detectar líneas numeradas: "1.", "1)", etc.
            match = re.match(r'^[\d]+[.)]\s*(.+)', line)
            if not match:
                continue
            text = match.group(1).strip()
            # Inferir tipo de campo por contenido
            text_lower = text.lower()
            if any(w in text_lower for w in ["presupuesto", "dinero", "euros", "€", "gasto", "cuánto quieres gastar"]):
                field_type = "number"
                placeholder = "ej: 200"
            elif any(w in text_lower for w in ["precio vendes", "precio", "a qué precio"]):
                field_type = "number"
                placeholder = "ej: 97"
            elif any(w in text_lower for w in ["país", "ciudad", "región", "donde", "dónde"]):
                field_type = "text"
                placeholder = "ej: España, Madrid..."
            elif any(w in text_lower for w in ["web", "url", "enlace", "página", "calendly", "link"]):
                field_type = "url"
                placeholder = "https://..."
            elif any(w in text_lower for w in ["garantía", "garantia", "garantías"]):
                field_type = "text"
                placeholder = "ej: 30 días de devolución, ninguna..."
            else:
                field_type = "textarea"
                placeholder = "Tu respuesta..."
            fields.append({
                "id": f"q{len(fields) + 1}",
                "label": text,
                "type": field_type,
                "placeholder": placeholder,
                "required": True,
            })
        return fields

    async def tool_request_clarification(self, tool_input: dict) -> str:
        question = tool_input.get("question", "")
        fields = self._parse_questions_to_fields(question)
        self._clarification_fields = fields
        return json.dumps({"clarification_requested": True, "question": question, "fields": fields})

    @property
    def created_plan_id(self) -> str | None:
        return self._created_plan_id

    @property
    def clarification_fields(self) -> list | None:
        return self._clarification_fields
