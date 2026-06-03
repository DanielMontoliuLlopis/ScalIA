# PROMPT 3 — CopyAgent + ejecución de planes aprobados

El orquestador genera planes reales. Ahora implementa el primer agente especializado y la ejecución.

## Contexto
- Los planes se aprueban en UI correctamente
- Cuando un plan pasa a approved, Celery debe ejecutarlo
- Empezamos con CopyAgent porque no requiere APIs externas

## Lo que tienes que implementar

### backend/app/agents/copy.py
CopyAgent especializado en generar copies de marketing.

**Tools disponibles:**

**Tool: `generate_ad_copy`**
- Input: {saas_description: str, target_audience: str, pain_point: str, tone: str, variants: int}
- Output: {copies: list[{hook: str, body: str, cta: str, score: int}]}
- Implementación: llama a Claude con prompt optimizado para copies de Meta Ads
- Genera exactamente `variants` variantes, ordenadas por score estimado

**Tool: `generate_landing_copy`**
- Input: {saas_description: str, target_audience: str, main_benefit: str}
- Output: {headline: str, subheadline: str, benefits: list[str], cta: str, social_proof: str}
- Implementación: genera copy completo para landing page

**Tool: `generate_email_sequence`**
- Input: {saas_description: str, sequence_goal: str, num_emails: int}
- Output: {emails: list[{subject: str, preview: str, body: str, send_delay_days: int}]}
- Implementación: genera secuencia de emails de nurturing

System prompt: experto en copywriting de performance marketing para productos SaaS, especializado en Meta Ads y email marketing, orientado a conversión.

### backend/app/workers/execution.py
Celery task que ejecuta un plan aprobado:

```python
@celery_app.task
async def execute_plan(plan_id: str):
    # 1. Carga el plan de DB
    # 2. Cambia estado a executing
    # 3. Por cada step del plan:
    #    a. Crea AgentTask en DB con estado pending
    #    b. Según el agent del step, instancia el agente correcto
    #    c. Ejecuta el agente con el contexto del step
    #    d. Guarda output en AgentTask, cambia estado a completed/failed
    #    e. Emite WS event: {type: "task_update", task_id, status, output}
    # 4. Cuando todos los steps terminan, cambia plan a done
    # 5. Emite WS event: {type: "plan_completed", plan_id}
```

Por ahora solo CopyAgent está implementado. Si un step tiene agent distinto a "CopyAgent", guardarlo como completed con output: {status: "pending_implementation"}.

### Actualizar POST /plans/{id}/approve
Después de cambiar estado a approved:
- Encolar `execute_plan.delay(plan_id)` en Celery
- Emitir WS event: {type: "plan_approved", plan_id}

### Nuevo endpoint: GET /plans/{id}/tasks
Devuelve todas las AgentTasks de un plan con su estado y output.

### Frontend: AgentActivityFeed component
En la página /chat, debajo del ApprovalCard cuando el plan está executing/done:
- Lista de tareas del plan con estado visual
- Icono animado (spinner) para tareas en running
- Check verde para completed
- X roja para failed
- Al hacer clic en una tarea completada → modal con el output (los copies generados, etc.)
- Se actualiza en tiempo real via WebSocket

## Ejemplo de flujo completo esperado

1. Usuario aprueba el plan
2. Celery recoge el plan
3. Step 1: CopyAgent genera 5 variantes de copy para Meta Ads
4. AgentActivityFeed muestra "Generando copies... ✓ Completado"
5. Usuario puede hacer clic y ver los copies generados
6. Steps siguientes (LandingAgent, AdsAgent): "Pendiente de implementación"
7. Plan pasa a done

## Lo que NO tocar
- OrchestratorAgent (ya funciona)
- Tablas existentes (usa AgentTask.output JSONB para guardar los resultados)
- Auth
