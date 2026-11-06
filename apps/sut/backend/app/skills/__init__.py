"""Skill package: the pluggable test-capability layer."""

from .registry import (  # noqa: F401
    Skill,
    SkillError,
    all_skills,
    get,
    list_skills,
    register,
    run_skill,
)
from . import builtin  # noqa: F401  (registers builtin skills)
