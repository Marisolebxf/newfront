"""科技专家直接关系 编排层。"""

from __future__ import annotations

from typing import Any

from service.expert_direct_relation import ExpertDirectRelationService


class ExpertDirectRelationApplication:
    def __init__(self) -> None:
        self._service = ExpertDirectRelationService()

    def describe(self) -> dict[str, object]:
        return self._service.describe()

    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._service.analyze(payload)

    def build(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._service.build(payload)

    def get_relation_response(
        self,
        data_source: str = "all",
        expert_a_id: str | None = None,
        expert_b_id: str | None = None,
        institution: str | None = None,
        relation_type: str = "direct",
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict[str, object]:
        """兼容 binding 路由的一跳/两跳/三跳查询。"""
        if not expert_a_id or not expert_b_id:
            return {"status": "error", "message": "需要 expertAId 和 expertBId"}
        result = self._service.analyze({
            "expertAId": expert_a_id,
            "expertBId": expert_b_id,
        })
        result["relationType"] = relation_type
        return result
