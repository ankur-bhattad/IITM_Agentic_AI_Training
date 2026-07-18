def build_prompt(query: str, style: str) -> str:
    return f"You are an assistant. Please answer in a {style} style.\nQuestion: {query}"
