"""Multi-step task planning with clarifying questions."""
import os
import anthropic


_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
    return _client


def generate_plan(goal: str, context: str = "") -> dict:
    """Generate a step-by-step plan for a goal. Returns {steps, questions, summary}."""
    system = (
        "You are a planning assistant. Given a goal, produce a JSON response with:\n"
        '{"steps": [...], "questions": [...], "summary": "..."}\n'
        "steps: ordered list of action steps\n"
        "questions: clarifying questions if the goal is ambiguous (empty list if clear)\n"
        "summary: one sentence description of the plan\n"
        "Be concise. Steps should be specific and actionable."
    )
    prompt = f"Goal: {goal}"
    if context:
        prompt += f"\nContext: {context}"

    try:
        response = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        text = response.content[0].text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception:
        pass

    return {
        "steps": [f"Work on: {goal}"],
        "questions": [],
        "summary": f"Plan to accomplish: {goal}",
    }


def format_plan_for_speech(plan: dict) -> str:
    summary = plan.get("summary", "")
    steps = plan.get("steps", [])
    questions = plan.get("questions", [])

    if questions:
        q_text = " ".join(questions[:2])
        return f"Before I plan this, I need a bit more detail. {q_text}"

    if not steps:
        return summary or "I've noted that down, sir."

    step_text = "; ".join(f"Step {i+1}: {s}" for i, s in enumerate(steps[:4]))
    return f"{summary} Here's the plan: {step_text}."
