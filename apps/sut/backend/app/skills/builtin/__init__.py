"""Builtin skills. Importing this package registers every module below."""

from . import (  # noqa: F401
    api_case_generate,
    api_diagnose,
    api_run,
    api_scenario_generate,
    case_batch,
    case_generate,
    case_list,
    case_update,
    kb_create,
    kb_document_add,
    kb_list,
    kb_search,
    project_list,
    requirement_analyze,
    requirement_chat,
    requirement_plan,
    ui_case_generate,
    ui_run,
)
