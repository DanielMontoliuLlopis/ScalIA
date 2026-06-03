"""CRMAgent — Scoring determinista de leads.

No usa LLM. Define la rúbrica de scoring que se aplicará a cada lead
capturado por las landing pages. El scoring real se ejecuta vía
`score_lead()` cuando llega un lead nuevo (router /leads).
"""
from typing import Any


class ScoringRubric:
    """Rúbrica de pesos por campo.

    Diseñada para que un form LM completo sume exactamente 100:
    - B2B/SaaS:   email(10)+nombre(5)+empresa(10)+cargo(25)+num_empleados(25)+urgencia(25) = 100
    - Services:   email(10)+nombre(5)+empresa(10)+cargo(25)+presupuesto(25)+urgencia(25) = 100
    - B2C/Local:  email(10)+nombre(5)+telefono(35)+segmentacion(25)+urgencia(25) = 100
    """

    EMAIL_VALID = 10
    NOMBRE_PRESENT = 5
    TELEFONO_PRESENT = 35   # muy cualificador en B2C/local
    EMPRESA_PRESENT = 10

    # Tamaño empresa — indica ticket potencial
    NUM_EMPLEADOS = {
        "Solo yo": 5,
        "2-10": 10,
        "11-50": 18,
        "51-200": 22,
        "200+": 25,
    }

    # Cargo — poder de decisión
    CARGO = {
        "CEO/Fundador": 25,
        "Director/VP": 20,
        "Manager": 12,
        "Técnico/Desarrollador": 6,
        "Otro": 2,
    }

    # Urgencia / intención de compra
    URGENCIA = {
        "Lo necesito ya": 25,
        "Necesito solución ya": 25,
        "En el próximo mes": 15,
        "Estoy explorando": 5,
        "Estoy investigando": 5,
    }

    # Presupuesto (services/consultoría)
    PRESUPUESTO_MIN_500 = 12
    PRESUPUESTO_MIN_2000 = 25

    # Segmentación genérica B2C (como_nos_conociste, frecuencia, etc.)
    SEGMENTACION_ALTA = 25    # respuesta que indica intención alta
    SEGMENTACION_MEDIA = 12
    SEGMENTACION_BAJA = 3


def score_lead(form_fields: list[dict], lead_data: dict, business_type: str = "saas") -> dict:
    """Calcula scoring 0-100 + segment hot/warm/cold + breakdown.

    Pesos fijos calibrados: form LM completo (email+nombre+empresa+cargo+num_empleados+urgencia) = 100.
    Leads que no rellenan campos cualificadores obtienen score bajo → cold.

    Args:
        form_fields: definición de los campos del form (de LandingPage.form_fields)
        lead_data: datos enviados por el lead (dict con email, nombre, etc.)
        business_type: saas|services|ecommerce|app|local

    Returns:
        {"score": int, "segment": str, "breakdown": dict}
    """
    breakdown: dict[str, int] = {}
    total = 0

    # Email es requerido siempre
    if lead_data.get("email"):
        breakdown["email"] = ScoringRubric.EMAIL_VALID
        total += ScoringRubric.EMAIL_VALID

    if lead_data.get("nombre"):
        breakdown["nombre"] = ScoringRubric.NOMBRE_PRESENT
        total += ScoringRubric.NOMBRE_PRESENT

    if lead_data.get("telefono"):
        breakdown["telefono"] = ScoringRubric.TELEFONO_PRESENT
        total += ScoringRubric.TELEFONO_PRESENT

    if lead_data.get("empresa"):
        breakdown["empresa"] = ScoringRubric.EMPRESA_PRESENT
        total += ScoringRubric.EMPRESA_PRESENT

    # Campos del form con extra_data
    extra = lead_data.get("extra_data", {}) or {}

    if lead_data.get("num_empleados"):
        ne_value = lead_data["num_empleados"]
        ne_score = ScoringRubric.NUM_EMPLEADOS.get(ne_value, 0)
        if ne_score:
            breakdown["num_empleados"] = ne_score
            total += ne_score

    cargo = extra.get("cargo") or extra.get("rol")
    if cargo:
        c_score = ScoringRubric.CARGO.get(cargo, 0)
        if c_score:
            breakdown["cargo"] = c_score
            total += c_score

    urgencia = extra.get("urgencia") or extra.get("principal_reto")
    if urgencia:
        u_score = ScoringRubric.URGENCIA.get(urgencia, 0)
        if u_score:
            breakdown["urgencia"] = u_score
            total += u_score

    presupuesto = extra.get("presupuesto_mensual") or extra.get("presupuesto")
    if presupuesto:
        if any(t in str(presupuesto) for t in ["2000", "5000", "10000", "+"]):
            breakdown["presupuesto"] = ScoringRubric.PRESUPUESTO_MIN_2000
            total += ScoringRubric.PRESUPUESTO_MIN_2000
        elif "500" in str(presupuesto) or "1000" in str(presupuesto):
            breakdown["presupuesto"] = ScoringRubric.PRESUPUESTO_MIN_500
            total += ScoringRubric.PRESUPUESTO_MIN_500

    # Cap a 100 — los pesos fijos están calibrados para que un form completo = 100
    final_score = min(total, 100)

    if final_score >= 70:
        segment = "hot"
    elif final_score >= 40:
        segment = "warm"
    else:
        segment = "cold"

    recommended_action = _recommend_action(final_score, segment, lead_data, extra, business_type)

    return {
        "score": final_score,
        "segment": segment,
        "breakdown": breakdown,
        "recommended_action": recommended_action,
    }


def _recommend_action(
    score: int,
    segment: str,
    lead_data: dict,
    extra: dict,
    business_type: str,
) -> dict:
    """Genera acción recomendada determinista en base a score + datos cualificadores."""
    has_phone = bool(lead_data.get("telefono"))
    cargo = extra.get("cargo") or extra.get("rol", "")
    urgencia = extra.get("urgencia") or extra.get("principal_reto", "")
    empresa = lead_data.get("empresa") or ""
    num_emp = lead_data.get("num_empleados") or ""

    # HOT — máxima urgencia
    if segment == "hot":
        if has_phone:
            return {
                "type": "call_now",
                "priority": "alta",
                "icon": "📞",
                "label": "Llamar ya",
                "reason": _hot_reason(cargo, urgencia, num_emp, empresa),
                "color": "red",
            }
        return {
            "type": "personal_email",
            "priority": "alta",
            "icon": "✉️",
            "label": "Email personal hoy",
            "reason": _hot_reason(cargo, urgencia, num_emp, empresa),
            "color": "red",
        }

    # WARM — secuencia automática + follow-up
    if segment == "warm":
        if has_phone:
            return {
                "type": "schedule_followup",
                "priority": "media",
                "icon": "📅",
                "label": "Agendar follow-up 3-5 días",
                "reason": f"Score {score} — interés medio. Dejar madurar con secuencia.",
                "color": "amber",
            }
        return {
            "type": "automated_nurturing",
            "priority": "media",
            "icon": "🔄",
            "label": "Continuar secuencia automática",
            "reason": f"Score {score} — sin teléfono. Que la secuencia haga su trabajo.",
            "color": "amber",
        }

    # COLD — no quemar
    return {
        "type": "low_touch",
        "priority": "baja",
        "icon": "🧊",
        "label": "Solo email #1 + observar",
        "reason": f"Score {score} — pocos campos cualificadores. Bajo encaje, no quemar contacto.",
        "color": "gray",
    }


def _hot_reason(cargo: str, urgencia: str, num_emp: str, empresa: str) -> str:
    parts: list[str] = []
    if cargo in ("CEO/Fundador", "Director/VP"):
        parts.append(f"decisor ({cargo})")
    if urgencia in ("Lo necesito ya", "Necesito solución ya"):
        parts.append("urgencia alta")
    if num_emp in ("51-200", "200+"):
        parts.append(f"empresa {num_emp} empleados")
    if empresa and not parts:
        parts.append(f"empresa identificada: {empresa}")
    if not parts:
        return "Score alto en múltiples cualificadores."
    return "Lead alto encaje: " + ", ".join(parts) + "."


_STATUS_SCORE_BONUS: dict[str, int] = {
    "contacted": 5,
    "showed_up": 20,
    "closed": 30,
    "lost": -10,
}


def rescore_on_status_change(
    lead_data: dict,
    form_fields: list[dict],
    new_status: str,
    business_type: str = "saas",
) -> dict:
    """Re-calculates score when lead_status changes.

    Applies a pipeline-stage bonus/penalty on top of the base form score.
    Returns same shape as score_lead().
    """
    base = score_lead(form_fields, lead_data, business_type)
    bonus = _STATUS_SCORE_BONUS.get(new_status, 0)
    new_score = max(0, min(100, base["score"] + bonus))

    if new_score >= 70:
        segment = "hot"
    elif new_score >= 40:
        segment = "warm"
    else:
        segment = "cold"

    return {
        "score": new_score,
        "segment": segment,
        "breakdown": {**base["breakdown"], "status_bonus": bonus},
        "recommended_action": _recommend_action(new_score, segment, lead_data, lead_data.get("extra_data", {}), business_type),
    }


class CRMAgent:
    """Agent stub que devuelve la rúbrica activa para mostrar al usuario.

    El scoring se ejecuta sin LLM via `score_lead()` cuando llega un lead.
    """

    def __init__(self, **kwargs) -> None:
        # Acepta user_id/plan_id/agent_name del worker; no usa LLM.
        self.user_id = kwargs.get("user_id")
        self.plan_id = kwargs.get("plan_id")
        self.agent_name = kwargs.get("agent_name", "CRMAgent")

    async def run_task(self, step: dict, context: dict | None = None) -> dict[str, Any]:
        context = context or {}
        business_type = step.get("business_type", "saas")
        landing = context.get("LandingAgent", {})

        # Detectar campos del form para construir la rúbrica aplicable
        variant_a = landing.get("variant_a", {})
        form_fields = variant_a.get("form_fields", [])
        field_names = [f.get("name") for f in form_fields if f.get("name")]

        applicable_rules: list[dict] = []
        applicable_rules.append({"field": "email", "max_points": ScoringRubric.EMAIL_VALID})
        applicable_rules.append({"field": "nombre", "max_points": ScoringRubric.NOMBRE_PRESENT})

        if "telefono" in field_names:
            applicable_rules.append({"field": "telefono", "max_points": ScoringRubric.TELEFONO_PRESENT})
        if "empresa" in field_names:
            applicable_rules.append({"field": "empresa", "max_points": ScoringRubric.EMPRESA_PRESENT})
        if "num_empleados" in field_names:
            applicable_rules.append({
                "field": "num_empleados",
                "max_points": max(ScoringRubric.NUM_EMPLEADOS.values()),
                "weights": ScoringRubric.NUM_EMPLEADOS,
            })
        if "cargo" in field_names or "rol" in field_names:
            applicable_rules.append({
                "field": "cargo",
                "max_points": max(ScoringRubric.CARGO.values()),
                "weights": ScoringRubric.CARGO,
            })
        if "urgencia" in field_names or "principal_reto" in field_names:
            applicable_rules.append({
                "field": "urgencia",
                "max_points": max(ScoringRubric.URGENCIA.values()),
                "weights": ScoringRubric.URGENCIA,
            })
        if "presupuesto_mensual" in field_names or "presupuesto" in field_names:
            applicable_rules.append({
                "field": "presupuesto",
                "max_points": ScoringRubric.PRESUPUESTO_MIN_2000,
            })

        max_possible = min(sum(r["max_points"] for r in applicable_rules), 100)

        return {
            "business_type": business_type,
            "rubric": applicable_rules,
            "max_possible_score": max_possible,
            "segments": {
                "hot": ">= 70 puntos — contactar manualmente en 24h",
                "warm": "40-69 puntos — secuencia de email completa",
                "cold": "< 40 puntos — solo email #1 + lead magnet",
            },
            "form_fields_detected": field_names,
        }
