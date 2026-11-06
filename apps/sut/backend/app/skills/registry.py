"""Skill registry — the extension point for every test capability.

A skill is a named, schema-described, runnable unit. Pages call skills through
``POST /api/platform/skills/{id}/run`` instead of hard-coding behaviour, so a new
capability only needs one registration to show up in the UI.

Design rules
------------
* Builtin skills live in ``app/skills/builtin/`` and register themselves on import.
* External skills (pulled from GitHub / the skills catalog) live in
  ``app/skills/external/`` and register through the same ``register()`` call.
* ``list_skills()`` returns only enabled skills; each carries enough metadata
  (id / name / category / input schema) for a generic frontend to render it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


class SkillError(Exception):
    """Raised when a skill cannot run (bad input, missing dependency, ...)."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass
class Skill:
    id: str
    name: str
    category: str
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    handler: Callable[[dict[str, Any], dict[str, Any]], Any] | None = None
    version: str = "0.1.0"
    enabled: bool = True
    source: str = "builtin"  # builtin | external

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "version": self.version,
            "enabled": self.enabled,
            "source": self.source,
        }


_REGISTRY: dict[str, Skill] = {}


def register(skill: Skill) -> Skill:
    """Register (or replace) a skill by id."""
    if not skill.id:
        raise ValueError("skill id is required")
    if skill.handler is None:
        raise ValueError(f"skill {skill.id!r} has no handler")
    _REGISTRY[skill.id] = skill
    return skill


def get(skill_id: str) -> Skill | None:
    return _REGISTRY.get(skill_id)


def all_skills() -> list[Skill]:
    return sorted(_REGISTRY.values(), key=lambda s: (s.category, s.id))


def list_skills(category: str | None = None, include_disabled: bool = False) -> list[Skill]:
    items = all_skills()
    if category:
        items = [s for s in items if s.category == category]
    if not include_disabled:
        items = [s for s in items if s.enabled]
    return items


def run_skill(skill_id: str, payload: dict[str, Any], ctx: dict[str, Any] | None = None) -> Any:
    skill = get(skill_id)
    if skill is None:
        raise SkillError(f"skill {skill_id!r} not found", status_code=404)
    if not skill.enabled:
        raise SkillError(f"skill {skill_id!r} is disabled", status_code=409)
    if not isinstance(payload, dict):
        raise SkillError("payload must be a JSON object")
    assert skill.handler is not None
    return skill.handler(payload, ctx or {})
