import asyncio
import json
import uuid
from typing import Optional

from openai import AsyncOpenAI, RateLimitError


def _to_openai_tools(tools: list[dict]) -> list[dict]:
    result = []
    for t in tools:
        function_def = {
            "name": t["name"],
            "description": t.get("description", ""),
            "parameters": t.get("input_schema", t.get("parameters", {"type": "object", "properties": {}})),
        }
        result.append({"type": "function", "function": function_def})
    return result


class BaseAgent:
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        user_id: Optional[uuid.UUID] = None,
        plan_id: Optional[uuid.UUID] = None,
        agent_name: str = "BaseAgent",
    ) -> None:
        self.client = AsyncOpenAI()
        self.model = model
        self.tools: list[dict] = []
        self.system_prompt: str = ""
        self.user_id = user_id
        self.plan_id = plan_id
        self.agent_name = agent_name

    async def run(self, messages: list[dict], max_tokens: int = 2048) -> str:
        conversation = [{"role": "system", "content": self.system_prompt}] + list(messages)
        openai_tools = _to_openai_tools(self.tools) if self.tools else []
        total_prompt_tokens = 0
        total_completion_tokens = 0

        while True:
            kwargs: dict = {"model": self.model, "max_tokens": max_tokens, "messages": conversation}
            if openai_tools:
                kwargs["tools"] = openai_tools
                # Primera llamada fuerza tool use; en iteraciones siguientes deja elegir
                if len(conversation) <= len(messages) + 1:
                    kwargs["tool_choice"] = "required"

            for attempt in range(3):
                try:
                    response = await self.client.chat.completions.create(**kwargs)
                    break
                except RateLimitError:
                    if attempt == 2:
                        raise
                    await asyncio.sleep(2 ** attempt)

            # Rastrear tokens
            if response.usage:
                total_prompt_tokens += response.usage.prompt_tokens
                total_completion_tokens += response.usage.completion_tokens

            message = response.choices[0].message

            if message.tool_calls:
                conversation.append(message)

                for tc in message.tool_calls:
                    try:
                        tool_input = json.loads(tc.function.arguments)
                        result = await self.execute_tool(tc.function.name, tool_input)
                    except Exception as exc:
                        result = f"Error ejecutando {tc.function.name}: {exc}"

                    conversation.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })
                continue

            # Registrar uso en DB (sincrónico, desde worker Celery)
            if self.user_id:
                self._log_usage(total_prompt_tokens, total_completion_tokens)

            return message.content or ""

    def _log_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Registra uso de tokens en DB (llamado desde worker Celery, contexto síncrono)."""
        if not self.user_id:
            return
        try:
            from app.services.openai_costs import calculate_cost
            from app.workers.execution import _get_session
            from app.models.api_usage import ApiUsage

            session = _get_session()
            cost = calculate_cost(self.model, prompt_tokens, completion_tokens)
            usage = ApiUsage(
                user_id=self.user_id,
                plan_id=self.plan_id,
                model=self.model,
                agent_name=self.agent_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=cost,
            )
            session.add(usage)
            session.commit()
            session.close()
        except Exception:
            # Silenciar errores de logging para no romper agentes
            pass

    async def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        method = getattr(self, f"tool_{tool_name}", None)
        if method is None:
            return f"Tool desconocida: {tool_name}"
        return await method(tool_input)
