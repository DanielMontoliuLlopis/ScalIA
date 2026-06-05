import asyncio
import json
import uuid
from typing import Optional

from openai import AsyncOpenAI, RateLimitError


class _CompletionsProxy:
    """Intercepta chat.completions.create para registrar uso de tokens."""

    def __init__(self, inner, agent: "BaseAgent") -> None:
        self._inner = inner
        self._agent = agent

    async def create(self, **kwargs):
        response = await self._inner.create(**kwargs)
        try:
            usage = getattr(response, "usage", None)
            if usage:
                self._agent._record_chat(
                    kwargs.get("model") or self._agent.model,
                    usage.prompt_tokens,
                    usage.completion_tokens,
                )
        except Exception:
            pass
        return response


class _ChatProxy:
    def __init__(self, inner, agent: "BaseAgent") -> None:
        self.completions = _CompletionsProxy(inner.completions, agent)


class _ImagesProxy:
    """Intercepta images.generate para registrar coste por imagen (DALL-E / gpt-image-1)."""

    def __init__(self, inner, agent: "BaseAgent") -> None:
        self._inner = inner
        self._agent = agent

    async def generate(self, **kwargs):
        response = await self._inner.generate(**kwargs)
        try:
            n = kwargs.get("n", 1)
            data = getattr(response, "data", None)
            if data:
                n = len(data)
            self._agent._record_image(
                kwargs.get("model") or "gpt-image-1",
                kwargs.get("quality"),
                n,
            )
        except Exception:
            pass
        return response


class _UsageTrackingClient:
    """Envuelve AsyncOpenAI para registrar uso en cada llamada (chat + imágenes).

    Captura tanto las llamadas vía run() como las directas de cada agente, de modo
    que TODAS las llamadas a la IA quedan en api_usage (incl. DALL-E/gpt-image-1).
    """

    def __init__(self, agent: "BaseAgent", inner: Optional[AsyncOpenAI] = None) -> None:
        self._agent = agent
        self._client = inner if inner is not None else AsyncOpenAI()
        self.chat = _ChatProxy(self._client.chat, agent)
        self.images = _ImagesProxy(self._client.images, agent)

    def with_options(self, **kwargs):
        return _UsageTrackingClient(self._agent, self._client.with_options(**kwargs))

    def __getattr__(self, name):
        # Delegar cualquier otro atributo al cliente real
        return getattr(self._client, name)


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
        self.client = _UsageTrackingClient(self)
        self.model = model
        self.tools: list[dict] = []
        self.system_prompt: str = ""
        self.user_id = user_id
        self.plan_id = plan_id
        self.agent_name = agent_name

    async def run(self, messages: list[dict], max_tokens: int = 2048) -> str:
        conversation = [{"role": "system", "content": self.system_prompt}] + list(messages)
        openai_tools = _to_openai_tools(self.tools) if self.tools else []

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

            # El uso se registra en _CompletionsProxy (no duplicar aquí).
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

            return message.content or ""

    def _record_chat(self, model: str, prompt_tokens: int, completion_tokens: int) -> None:
        """Registra uso de tokens de una llamada de chat en api_usage."""
        if not self.user_id:
            return
        from app.services.openai_costs import calculate_cost

        self._write_usage(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=calculate_cost(model, prompt_tokens, completion_tokens),
        )

    def _record_image(self, model: str, quality: str | None, n: int) -> None:
        """Registra coste de una generación de imágenes en api_usage."""
        if not self.user_id:
            return
        from app.services.openai_costs import calculate_image_cost

        self._write_usage(
            model=model,
            prompt_tokens=0,
            completion_tokens=0,
            cost=calculate_image_cost(model, quality, n),
        )

    def _write_usage(self, model: str, prompt_tokens: int, completion_tokens: int, cost: float) -> None:
        """Inserta una fila en api_usage (contexto síncrono, desde worker Celery)."""
        if not self.user_id:
            return
        try:
            from app.workers.execution import _get_session
            from app.models.api_usage import ApiUsage

            session = _get_session()
            usage = ApiUsage(
                user_id=self.user_id,
                plan_id=self.plan_id,
                model=model,
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
