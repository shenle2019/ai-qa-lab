"""Dataset model and JSONL loader."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EvalCase:
    id: str
    input: str
    actual_output: str
    expected_output: str
    context: list[str] = field(default_factory=list)
    baseline_output: str | None = None


def load_jsonl(path: str | Path) -> list[EvalCase]:
    cases: list[EvalCase] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            cases.append(
                EvalCase(
                    id=str(item.get("id", len(cases) + 1)),
                    input=item["input"],
                    actual_output=item["actual_output"],
                    expected_output=item["expected_output"],
                    context=list(item.get("context", [])),
                    baseline_output=item.get("baseline_output"),
                )
            )
    return cases
