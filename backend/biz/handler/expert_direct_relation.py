"""科技专家直接关系 路由。"""

from fastapi import APIRouter, HTTPException

from application.expert_direct_relation import ExpertDirectRelationApplication
from biz.schemas.expert_direct_relation import (
    DirectRelationBuildResponse,
    DirectRelationRequest,
    DirectRelationResponse,
)

router = APIRouter(prefix="/kg-construction/expert-direct-relations")
application = ExpertDirectRelationApplication()


@router.get("")
async def describe_expert_direct_relation() -> dict[str, object]:
    return application.describe()


@router.post("/analyze", response_model=DirectRelationResponse)
async def analyze_direct_relation(
    req: DirectRelationRequest,
) -> DirectRelationResponse:
    try:
        return application.analyze(req.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/build", response_model=DirectRelationBuildResponse)
async def build_direct_relation(
    req: DirectRelationRequest,
) -> DirectRelationBuildResponse:
    try:
        return application.build(req.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
