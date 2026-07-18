def adapt_style(current_style: str, feedback: str) -> str:
    rules = {
        "too short": "detailed",
        "too long": "concise",
        "too formal": "casual",
        "too casual": "formal"
    }
    return rules.get(feedback.lower(), current_style)
