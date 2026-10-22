"""Dependency-free provider logic and strict plan validation."""
from __future__ import annotations

from typing import Protocol


class PlanProvider(Protocol):
    name: str

    def generate(self, question: str) -> dict[str, object]: ...


def validate_plan_data(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {"title", "summary", "steps", "provider"}:
        raise ValueError("Plan has an invalid schema")
    title, summary, steps, provider = (value[k] for k in ("title", "summary", "steps", "provider"))
    if not isinstance(title, str) or not 3 <= len(title.strip()) <= 80:
        raise ValueError("Plan title is invalid")
    if not isinstance(summary, str) or not 5 <= len(summary.strip()) <= 260:
        raise ValueError("Plan summary is invalid")
    if not isinstance(steps, list) or not 2 <= len(steps) <= 5:
        raise ValueError("Plan step count is invalid")
    if any(not isinstance(step, str) or not step.strip() or len(step) > 220 for step in steps):
        raise ValueError("Plan steps are invalid")
    if provider not in {"demo", "bedrock"}:
        raise ValueError("Unknown plan provider")
    return {"title": title.strip(), "summary": summary.strip(), "steps": [s.strip() for s in steps], "provider": provider}


class DemoProvider:
    """Stable, offline examples that are never labeled as live AI."""

    name = "demo"

    def generate(self, question: str) -> dict[str, object]:
        topic = question.lower()
        if "flood" in topic:
            title, steps = "Flood preparedness starter plan", [
                "Know your local flood risk and follow official local alerts.",
                "Keep important documents in a waterproof, portable place.",
                "Never walk or drive through floodwater.",
            ]
        elif "heat" in topic:
            title, steps = "Heatwave preparedness starter plan", [
                "Find cooling options using official local sources.",
                "Check on older adults, neighbors, and people with health needs.",
                "Never leave people or pets in a parked vehicle.",
            ]
        elif "earthquake" in topic or "quake" in topic:
            title, steps = "Earthquake preparedness starter plan", [
                "Secure heavy furniture and objects that could fall.",
                "Practice Drop, Cover, and Hold On with your household.",
                "Choose safe spots away from glass in each room.",
            ]
        else:
            title, steps = "Family emergency plan starter", [
                "Choose an out-of-area contact and share the number.",
                "Agree on meeting places and learn routes from local authorities.",
                "Plan for medications, accessibility, children, and pets.",
            ]
        return validate_plan_data({
            "title": title,
            "summary": "A predetermined local demo example. Follow local authorities during an emergency.",
            "steps": steps,
            "provider": self.name,
        })
