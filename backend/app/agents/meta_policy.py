import json
from typing import Any

from app.agents.base import BaseAgent

SYSTEM_PROMPT = """Eres un experto en políticas publicitarias de Meta (Facebook/Instagram Ads) y copywriting humano.

Tienes dos misiones:

1. VALIDAR que cada copy, imagen y targeting cumple estrictamente las políticas de Meta:
   - Sin claims de salud/peso/curas milagrosas
   - Sin targeting por datos sensibles (religión, orientación sexual, salud, etc.)
   - Sin before/after físicos
   - Sin lenguaje de urgencia artificial ("¡Solo hoy!", cuenta regresiva falsa)
   - Sin promesas de ingresos garantizados
   - Sin discriminación en targeting
   - Sin claims financieros sin disclaimer
   - Sin contenido engañoso o misleading sobre el producto
   - Sin "Facebook" o "Instagram" en el texto del anuncio
   - Texto en imagen ≤ 20% del área (política legacy, aún recomendada)

2. HUMANIZAR el copy para que suene natural, como escrito por un humano:
   - Eliminar frases genéricas de IA ("En el competitivo mundo de...", "En conclusión...")
   - Variar la estructura de frases (no todas igual de largas)
   - Añadir especificidad concreta (números, nombres, detalles reales)
   - Usar contracciones y lenguaje coloquial apropiado al tono de marca
   - Eliminar adjetivos vacíos ("increíble", "revolucionario", "único")
   - Preferir verbos activos sobre sustantivos abstractos
   - El copy debe parecer escrito por alguien que conoce al cliente de verdad

Devuelve siempre JSON estructurado con los copies corregidos y un reporte de cambios."""

POLICY_RULES = [
    "No claims de salud, curas, pérdida de peso garantizada",
    "No before/after físicos o de salud",
    "No targeting por religión, salud, orientación sexual, etnia",
    "No urgencia falsa o artificial (contadores falsos)",
    "No ingresos garantizados sin disclaimer",
    "No mencionar 'Facebook' o 'Instagram' en el copy",
    "No contenido engañoso sobre el producto o servicio",
    "No claims financieros sin advertencia legal apropiada",
    "No discriminación en targeting por características protegidas",
    "Imagen con texto ≤ 20% del área visible",
    "Garantías de resultados específicos sin evidencia verificable están prohibidas",
]

# Claims de garantía que Meta considera problemáticos
GARANTIA_PROBLEMATIC_PHRASES = [
    "garantizado", "100% garantizado", "te devolvemos el dinero si no funciona",
    "resultados garantizados", "éxito garantizado",
]

GARANTIA_ALLOWED_PHRASES = {
    "sin_garantia": "",
    "satisfaccion": "Garantía de satisfacción — si no estás contento, te ayudamos.",
    "resultados": "Trabajamos contigo hasta conseguir resultados.",
    "devolucion_X_dias": "Garantía de devolución sin preguntas.",
}


class MetaPolicyAgent(BaseAgent):
    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("model", "gpt-4o")
        super().__init__(**kwargs)
        self.system_prompt = SYSTEM_PROMPT
        self.tools = [
            {
                "name": "validate_and_humanize_copy",
                "description": "Valida copies contra políticas Meta y los humaniza eliminando patrones de IA",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "copies": {
                            "type": "array",
                            "description": "Lista de copies a validar y humanizar",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "index": {"type": "integer"},
                                    "hook": {"type": "string"},
                                    "body": {"type": "string"},
                                    "cta": {"type": "string"},
                                    "angle": {"type": "string"},
                                },
                            },
                        },
                        "business_type": {"type": "string", "description": "Tipo de negocio"},
                        "campaign_type": {"type": "string", "description": "Tipo de campaña"},
                    },
                    "required": ["copies"],
                },
            },
            {
                "name": "validate_targeting",
                "description": "Valida que el targeting de audiencia no viola políticas Meta",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "interests": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Intereses del targeting",
                        },
                        "age_min": {"type": "integer"},
                        "age_max": {"type": "integer"},
                        "exclusions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Exclusiones de audiencia",
                        },
                    },
                    "required": ["interests"],
                },
            },
        ]

    async def tool_validate_and_humanize_copy(self, input: dict) -> str:
        copies = input.get("copies", [])
        business_type = input.get("business_type", "saas")
        campaign_type = input.get("campaign_type", "lead_gen")

        rules_text = "\n".join(f"- {r}" for r in POLICY_RULES)
        prompt = f"""Valida y humaniza estos {len(copies)} copies para Meta Ads.

Negocio: {business_type} | Campaña: {campaign_type}

POLÍTICAS A VERIFICAR:
{rules_text}

COPIES A PROCESAR:
{json.dumps(copies, ensure_ascii=False, indent=2)}

Para cada copy:
1. Detecta violaciones de política (si las hay)
2. Humaniza eliminando patrones de IA
3. Devuelve el copy corregido

Responde en JSON:
{{
  "copies": [
    {{
      "index": 0,
      "hook": "copy humanizado",
      "body": "copy humanizado",
      "cta": "copy humanizado",
      "angle": "ángulo",
      "policy_issues_found": ["lista de problemas detectados"],
      "policy_issues_fixed": ["lista de correcciones aplicadas"],
      "humanization_changes": ["cambios para sonar más humano"]
    }}
  ],
  "overall_policy_status": "approved | approved_with_fixes | rejected",
  "rejection_reason": null
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
        return response.choices[0].message.content or "{}"

    async def tool_validate_targeting(self, input: dict) -> str:
        interests = input.get("interests", [])
        age_min = input.get("age_min", 18)
        age_max = input.get("age_max", 65)
        exclusions = input.get("exclusions", [])

        PROTECTED_CATEGORIES = [
            "religion", "religión", "faith", "fe", "christianity", "islam", "judaism",
            "sexual orientation", "orientación sexual", "lgbtq", "gay", "lesbian",
            "health condition", "enfermedad", "diabetes", "cancer", "hiv",
            "race", "raza", "ethnicity", "etnia",
            "political", "político", "partido",
            "disability", "discapacidad",
        ]

        issues = []
        safe_interests = []
        for interest in interests:
            interest_lower = interest.lower()
            is_protected = any(cat in interest_lower for cat in PROTECTED_CATEGORIES)
            if is_protected:
                issues.append(f"Interés protegido eliminado: '{interest}'")
            else:
                safe_interests.append(interest)

        if age_min < 18:
            issues.append(f"age_min={age_min} no permitido. Corregido a 18.")
            age_min = 18

        result = {
            "status": "approved" if not issues else "approved_with_fixes",
            "safe_interests": safe_interests,
            "age_min": age_min,
            "age_max": age_max,
            "exclusions": exclusions,
            "issues_fixed": issues,
        }
        return json.dumps(result, ensure_ascii=False)

    def _validate_garantia(self, garantia: str, copies: list[dict]) -> dict:
        """Valida que el copy de garantía no viole políticas Meta."""
        issues: list[str] = []
        fixes: list[str] = []
        safe_phrase = GARANTIA_ALLOWED_PHRASES.get(garantia, "")

        for copy in copies:
            combined = f"{copy.get('hook', '')} {copy.get('body', '')} {copy.get('cta', '')}".lower()
            for phrase in GARANTIA_PROBLEMATIC_PHRASES:
                if phrase.lower() in combined:
                    issues.append(f"Claim problemático detectado: '{phrase}'")
                    if safe_phrase:
                        fixes.append(f"Sustituir por: '{safe_phrase}'")

        return {
            "garantia_type": garantia,
            "safe_phrase_suggested": safe_phrase,
            "issues_found": issues,
            "fixes_applied": fixes,
            "status": "ok" if not issues else "needs_review",
        }

    async def run_task(self, step: dict, context: dict | None = None) -> dict[str, Any]:
        context = context or {}
        copy_output = context.get("CopyAgent", {})
        research_output = context.get("ResearchAgent", {})

        copies = copy_output.get("copies", [])
        business_type = step.get("business_type", research_output.get("business_type", "saas"))
        campaign_type = step.get("campaign_type", "lead_gen")
        garantia = step.get("garantia", "sin_garantia") or "sin_garantia"

        if not copies:
            return {
                "status": "skipped",
                "reason": "No copies from CopyAgent",
                "validated_copies": [],
            }

        simplified_copies = [
            {
                "index": i,
                "hook": c.get("hook", ""),
                "body": c.get("body", ""),
                "cta": c.get("cta", ""),
                "angle": c.get("angle", ""),
            }
            for i, c in enumerate(copies)
        ]

        messages = [
            {
                "role": "user",
                "content": (
                    f"Valida y humaniza estos copies para Meta Ads. "
                    f"Negocio: {business_type}, campaña: {campaign_type}. "
                    f"Usa validate_and_humanize_copy con los {len(simplified_copies)} copies."
                ),
            }
        ]

        await self.run(messages, max_tokens=4096)

        copy_result_raw = await self.tool_validate_and_humanize_copy({
            "copies": simplified_copies,
            "business_type": business_type,
            "campaign_type": campaign_type,
        })
        copy_result = json.loads(copy_result_raw)

        interests = research_output.get("targeting", {}).get("interests", [])
        targeting_result_raw = await self.tool_validate_targeting({
            "interests": interests,
            "age_min": research_output.get("targeting", {}).get("age_min", 18),
            "age_max": research_output.get("targeting", {}).get("age_max", 65),
        })
        targeting_result = json.loads(targeting_result_raw)

        validated_copies_map = {c["index"]: c for c in copy_result.get("copies", [])}
        merged_copies = []
        for i, original_copy in enumerate(copies):
            validated = validated_copies_map.get(i, {})
            merged = {
                **original_copy,
                "hook": validated.get("hook", original_copy.get("hook", "")),
                "body": validated.get("body", original_copy.get("body", "")),
                "cta": validated.get("cta", original_copy.get("cta", "")),
                "policy_issues_found": validated.get("policy_issues_found", []),
                "policy_issues_fixed": validated.get("policy_issues_fixed", []),
                "humanization_changes": validated.get("humanization_changes", []),
            }
            merged_copies.append(merged)

        garantia_result = self._validate_garantia(garantia, merged_copies)

        return {
            "status": copy_result.get("overall_policy_status", "approved"),
            "rejection_reason": copy_result.get("rejection_reason"),
            "validated_copies": merged_copies,
            "targeting": targeting_result,
            "garantia_validation": garantia_result,
            "summary": {
                "copies_processed": len(merged_copies),
                "targeting_issues_fixed": len(targeting_result.get("issues_fixed", [])),
                "copy_issues_fixed": sum(
                    len(c.get("policy_issues_fixed", [])) for c in merged_copies
                ),
                "garantia_issues": len(garantia_result.get("issues_found", [])),
            },
        }
