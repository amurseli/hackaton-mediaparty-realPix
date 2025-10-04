AI_KEYWORDS = [
    "openai", "chatgpt", "dalle", "gpt",
    "google", "gemini", "deepmind",
    "stability", "stable diffusion", "sdxl",
    "midjourney",
    "runway",
    "copilot",
    "claude", "anthropic"
]

def is_ai_generated(*values: str, action_tools: list[str] = None) -> bool:
    """
    Dado un conjunto de strings (issuer, claim_generator, título, etc.)
    y opcionalmente una lista de tools de acciones, devuelve True si
    alguno matchea con un nombre conocido de IA o si alguna tool indica IA.
    """
    # Revisamos issuer, claim_generator, título, etc.
    joined = " ".join([v.lower() for v in values if v])
    for kw in AI_KEYWORDS:
        if kw in joined:
            return True

    # Revisamos herramientas de las acciones
    if action_tools:
        for tool in action_tools:
            if "generative" in tool.lower():
                return True

    return False
