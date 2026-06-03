"""Cálculo de costes de OpenAI basado en precios públicos.

Precios (2026-05-29):
- gpt-4o: $5/1M input tokens, $15/1M output tokens
"""


# Precios por millón de tokens (en USD)
OPENAI_PRICES = {
    "gpt-4o": {
        "input": 5.00,      # $5 per 1M input tokens
        "output": 15.00,    # $15 per 1M output tokens
    },
    "gpt-4-turbo": {
        "input": 10.00,
        "output": 30.00,
    },
    "gpt-3.5-turbo": {
        "input": 0.50,
        "output": 1.50,
    },
}


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calcula coste en USD para una llamada a OpenAI.

    Args:
        model: nombre del modelo (ej: gpt-4o)
        prompt_tokens: tokens de entrada
        completion_tokens: tokens de salida

    Returns:
        coste en USD (ej: 0.001234)
    """
    if model not in OPENAI_PRICES:
        model = "gpt-4o"  # fallback

    prices = OPENAI_PRICES[model]
    input_cost = (prompt_tokens / 1_000_000) * prices["input"]
    output_cost = (completion_tokens / 1_000_000) * prices["output"]
    return input_cost + output_cost
