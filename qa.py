"""Quality assurance: response quality checks."""


def check_response_quality(response: str, context: str = "") -> dict:
    issues = []

    if len(response) > 500 and not any(
        kw in context.lower()
        for kw in ["explain", "detail", "full", "list", "write", "code"]
    ):
        issues.append("response_too_long")

    if response.lower().startswith("as an ai") or "language model" in response.lower():
        issues.append("breaks_character")

    if not response.strip():
        issues.append("empty_response")

    return {"issues": issues, "passed": len(issues) == 0}


def sanitize_for_tts(text: str) -> str:
    """Clean response text before sending to TTS."""
    import re
    # Remove action tags
    text = re.sub(r"\[ACTION:[^\]]+\]", "", text)
    # Remove markdown formatting
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"#{1,6}\s", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"```[\s\S]*?```", "[code block]", text)
    text = text.strip()
    return text
