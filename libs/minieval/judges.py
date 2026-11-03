"""Judge implementations: deterministic mock and optional DeepSeek."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Protocol

import httpx

from .dataset import EvalCase
from .metrics import score_case


class Judge(Protocol):
    name: str

    def score(self, case: EvalCase) -> dict[str, float]:
        ...


class MockJudge:
    name = "mock"

    def score(self, case: EvalCase) -> dict[str, float]:
        return score_case(case)


class DeepSeekJudge:
    name = "deepseek"

    def __init__(self, api_key: str | None = None, model: str = "deepseek-chat") -> None:
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.model = model
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not set")

    def _ask(self, case: EvalCase) -> dict[str, float]:
        prompt = (
            "你是 LLM 评测裁判。只返回 JSON，不要解释。\n"
            "给下面的回答打分，每项 0 到 1，保留两位小数：\n"
            "answer_relevance（回答是否切题）、faithfulness（回答是否忠于上下文）、"
            "correctness（回答是否覆盖参考答案）。\n\n"
            f"问题：{case.input}\n"
            f"回答：{case.actual_output}\n"
            f"参考答案：{case.expected_output}\n"
            f"上下文：{' '.join(case.context)}\n\n"
            'JSON 格式：{"answer_relevance":0.0,"faithfulness":0.0,"correctness":0.0}'
        )
        response = httpx.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "response_format": {"type": "json_object"},
            },
            timeout=30,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        content = re.sub(r"^```json\s*|\s*```$", "", content.strip())
        data = json.loads(content)
        return {
            "answer_relevance": float(data.get("answer_relevance", 0)),
            "faithfulness": float(data.get("faithfulness", 0)),
            "correctness": float(data.get("correctness", 0)),
        }

    def score(self, case: EvalCase) -> dict[str, float]:
        judged = self._ask(case)
        deterministic = score_case(case)
        values = {
            "answer_relevance": judged["answer_relevance"],
            "faithfulness": judged["faithfulness"],
            "context_precision": deterministic["context_precision"],
            "context_recall": deterministic["context_recall"],
            "correctness": judged["correctness"],
        }
        values["overall"] = round(sum(values.values()) / len(values), 4)
        return {key: round(value, 4) for key, value in values.items()}


def get_judge(name: str) -> Judge:
    if name == "mock":
        return MockJudge()
    if name == "deepseek":
        return DeepSeekJudge()
    raise ValueError(f"unknown judge: {name}")
