"""科技专家直接关系 请求/响应模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class DirectRelationRequest(BaseModel):
    expertAId: str
    expertBId: str
    institution: str | None = None

    @model_validator(mode="after")
    def _validate(self):
        if self.expertAId == self.expertBId:
            raise ValueError("expertAId 和 expertBId 不能相同")
        return self


class ExpertBrief(BaseModel):
    expertId: str
    name: str
    organization: str = ""
    paperCount: int = 0
    citationCount: int = 0
    hIndex: float = 0


class RelationDetail(BaseModel):
    reasons: list[str] = Field(default_factory=list)
    relationStrength: int = 0
    institution: str = ""
    directions: list[str] = Field(default_factory=list)


class GraphNodeView(BaseModel):
    id: str
    type: str
    label: str
    subtitle: str | None = None
    x: int = 0
    y: int = 0


class GraphEdgeView(BaseModel):
    source: str
    target: str
    label: str = ""


class DirectRelationResponse(BaseModel):
    status: str = "success"
    expertA: ExpertBrief
    expertB: ExpertBrief
    relation: RelationDetail
    graphNodes: list[GraphNodeView] = Field(default_factory=list)
    graphEdges: list[GraphEdgeView] = Field(default_factory=list)


class DirectRelationBuildResponse(BaseModel):
    status: str = "success"
    edgeId: str | None = None
    relationStrength: int = 0
    reasons: list[str] = Field(default_factory=list)
    message: str = ""
