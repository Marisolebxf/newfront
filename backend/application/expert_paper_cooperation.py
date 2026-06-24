"""科技专家论文合作关系 编排层。"""

from __future__ import annotations

from typing import Any

from service.expert_paper_cooperation import ExpertPaperCooperationService


class ExpertPaperCooperationApplication:
    def __init__(self) -> None:
        self._service = ExpertPaperCooperationService()

    def describe(self) -> dict[str, object]:
        return self._service.describe()

    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._service.analyze(payload)

    def build(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._service.build(payload)
