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
    "gpt-4o-mini": {
        "input": 0.15,      # $0.15 per 1M input tokens
        "output": 0.60,     # $0.60 per 1M output tokens
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

# Precios por imagen generada (en USD), aprox. para 1024x1024
IMAGE_PRICES = {
    "gpt-image-1": {
        "low": 0.011,
        "medium": 0.042,
        "high": 0.167,
        "auto": 0.042,
    },
    "dall-e-3": {
        "standard": 0.040,
        "hd": 0.080,
    },
    "dall-e-2": {
        "standard": 0.020,
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


def calculate_image_cost(model: str, quality: str | None = None, n: int = 1) -> float:
    """Calcula coste en USD para una generación de imágenes (DALL-E / gpt-image-1).

    Args:
        model: nombre del modelo (ej: gpt-image-1, dall-e-3)
        quality: calidad solicitada (low/medium/high/auto, standard/hd)
        n: número de imágenes generadas

    Returns:
        coste en USD
    """
    table = IMAGE_PRICES.get(model)
    if not table:
        table = IMAGE_PRICES["gpt-image-1"]  # fallback
    q = (quality or "auto").lower()
    per_image = table.get(q)
    if per_image is None:
        per_image = next(iter(table.values()))
    return per_image * max(1, n or 1)
