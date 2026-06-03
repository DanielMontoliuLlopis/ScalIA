# PROMPT 2 — OrchestratorAgent real con Claude Tool Use

El scaffold está funcionando. Ahora reemplaza el mock del orquestador por el agente real.

## Contexto
- El flujo de aprobación en UI ya funciona
- POST /chat/message es el endpoint que vamos a modificar
- No tocar nada de frontend ni de auth

## Lo que tienes que implementar

### backend/app/agents/base.py
Clase base para todos los agentes:
```python
class BaseAgent:
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.AsyncAnthropic()
        self.model = model
        self.tools: list[dict] = []
        self.system_prompt: str = ""
    
    async def run(self, messages: list[dict], max_tokens: int = 4096) -> str:
        # loop de tool use: llama a Claude, ejecuta tools, repite hasta text final
        # captura errores de tools y los reporta como tool_result con error
        ...
    
    async def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        # dispatch a los métodos de la subclase
        ...
```

### backend/app/agents/orchestrator.py
OrchestratorAgent con estas tools (que NO ejecutan nada real, solo construyen el plan):

**Tool: `analyze_intent`**
- Input: {message: str}
- Output: {intent: str, saas_description: str, budget: str, goal: str}
- Implementación: llamada interna a Claude con prompt específico para extraer intención

**Tool: `create_plan`**
- Input: {title: str, description: str, steps: list[{agent: str, action: str, description: str, estimated_time: str}]}
- Output: {plan_id: str}
- Implementación: guarda el plan en DB con estado pending_approval, emite WS event

**Tool: `request_clarification`**
- Input: {question: str}
- Output: {clarification_requested: true}
- Implementación: solo devuelve la pregunta para que el router la envíe al usuario

System prompt del orquestador:
- Es el coordinador de un sistema de marketing agentico
- Su trabajo es entender qué quiere el usuario y crear un plan concreto y ejecutable
- El plan debe ser específico: qué agente hace qué, en qué orden, con qué objetivo
- Si falta información crítica (¿qué SaaS? ¿qué presupuesto?) debe preguntar
- Nunca inventar presupuestos ni datos que el usuario no ha dado
- El plan debe ser aprobado por el usuario antes de ejecutarse — dejar esto claro en la respuesta

### Actualizar POST /chat/message
1. Guarda mensaje del usuario
2. Construye el historial de mensajes del chat para este usuario (últimos 20)
3. Ejecuta OrchestratorAgent.run() con ese historial
4. Si el agente llamó create_plan → el plan ya está en DB, devolver respuesta con plan_id
5. Si el agente llamó request_clarification → devolver la pregunta como mensaje normal
6. Guardar respuesta del assistant en chat_messages
7. Devolver {message: str, plan_id: str | null}

## Ejemplo de flujo esperado

Usuario: "Quiero conseguir leads para mi SaaS de facturación para freelancers, tengo €200/mes"

Orchestrator:
1. Llama analyze_intent → extrae intent=lead_generation, saas=facturación freelancers, budget=200€/mes
2. Llama create_plan con pasos:
   - ResearchAgent: analizar audiencia freelancers en Meta, identificar pain points
   - CopyAgent: generar 5 variantes de copy para anuncio Meta
   - LandingAgent: crear landing page orientada a freelancers
   - AdsAgent: crear campaña Meta con €200/mes, segmentación freelancers España
   - EmailAgent: secuencia de 3 emails para leads que dejen email en landing
3. Devuelve: "He preparado un plan con 5 pasos para conseguir leads. Revísalo y apruébalo cuando estés listo."

## Lo que NO tocar
- Frontend (ya funciona con el plan_id)
- Tablas de DB (no añadir columnas sin migración)
- Auth
- Celery (la ejecución real viene en el siguiente prompt)
