from __future__ import annotations

from app.models.schemas import Action, ActionType


class Planner:
    """Very small deterministic planner for MVP and low token usage."""

    def make_plan(self, goal: str, explicit_steps: list[Action] | None = None) -> list[Action]:
        if explicit_steps:
            return explicit_steps

        lower = goal.lower()
        # Minimal heuristic templates
        if "wikipedia" in lower and "search" in lower:
            return [
                Action(type=ActionType.navigate, args={"url": "https://www.wikipedia.org"}),
                Action(type=ActionType.type, args={"selector": "input#searchInput", "text": "Artificial intelligence"}),
                Action(type=ActionType.click, args={"selector": "button[type='submit']"}),
                Action(type=ActionType.extract_text, args={"selector": "#firstHeading"}),
                Action(type=ActionType.save_json, args={"path": "results/wikipedia_heading.json"}),
            ]

        return [
            Action(type=ActionType.navigate, args={"url": "https://example.com"}),
            Action(type=ActionType.extract_text, args={"selector": "h1"}),
            Action(type=ActionType.save_json, args={"path": "results/default_result.json"}),
        ]
