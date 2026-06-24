"""科技专家论文合作关系 请求/响应模型。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class PaperCooperationRequest(BaseModel):
    dataSource: str = "knowledge_graph"
    expertAId: str
    expertBId: str
    startTime: str | None = None
    endTime: str | None = None

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


class CooperationTimeRange(BaseModel):
    startYear: int = 0
    endYear: int = 0
    displayText: str = ""


class StructuredResult(BaseModel):
    authorList: list[str] = Field(default_factory=list)
    authorUnits: list[str] = Field(default_factory=list)
    paperTopics: list[str] = Field(default_factory=list)
    cooperationPaperCount: int = 0
    journalLevelCount: dict[str, int] = Field(default_factory=dict)
    conferenceLevelCount: dict[str, int] = Field(default_factory=dict)
    cooperationFrequency: int = 0
    academicImpactScore: float = 0
    citation: dict[str, int] = Field(default_factory=dict)
    cooperationTimeRange: CooperationTimeRange = Field(default_factory=CooperationTimeRange)
    stableTeamName: str | None = None
    stableTeamMembers: list[str] = Field(default_factory=list)
    coreCollaborators: list[str] = Field(default_factory=list)
    sharedContribution: list[str] = Field(default_factory=list)
    representativePapers: list[str] = Field(default_factory=list)


class GraphNodeView(BaseModel):
    id: str
    type: str
    label: str
    subtitle: str | None = None
    x: int = 0
    y: int = 0
    items: list[str] = Field(default_factory=list)


class GraphEdgeView(BaseModel):
    source: str
    target: str
    label: str = ""


class PaperCooperationResponse(BaseModel):
    status: str = "success"
    expertA: ExpertBrief
    expertB: ExpertBrief
    structuredResult: StructuredResult
    graphNodes: list[GraphNodeView] = Field(default_factory=list)
    graphEdges: list[GraphEdgeView] = Field(default_factory=list)


class PaperCooperationBuildResponse(BaseModel):
    status: str = "success"
    edgeId: str | None = None
    paperCount: int = 0
    message: str = ""
