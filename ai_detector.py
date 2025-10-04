AI_KEYWORDS = [
    "openai", "chatgpt", "dalle", "gpt",
    "google", "gemini", "deepmind",
    "stability", "stable diffusion", "sdxl",
    "midjourney",
    "runway",
    "copilot",
    "claude", "anthropic"
]

def is_ai_generated(*values: str) -> bool:
    """
    Dado un conjunto de strings (issuer, author, claim_generator...),
    devuelve True si alguno matchea con un nombre conocido de IA.
    """
    joined = " ".join([v.lower() for v in values if v])
    for kw in AI_KEYWORDS:
        if kw in joined:
            return True
    return False
