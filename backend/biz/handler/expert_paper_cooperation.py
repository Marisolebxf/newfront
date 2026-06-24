"""科技专家论文合作关系 路由。"""

from fastapi import APIRouter, HTTPException

from application.expert_paper_cooperation import ExpertPaperCooperationApplication
from biz.schemas.expert_paper_cooperation import (
    PaperCooperationBuildResponse,
    PaperCooperationRequest,
    PaperCooperationResponse,
)

router = APIRouter(prefix="/kg-construction/expert-paper-cooperation-relations")
application = ExpertPaperCooperationApplication()


@router.get("")
async def describe_expert_paper_cooperation() -> dict[str, object]:
    return application.describe()


@router.post("/analyze", response_model=PaperCooperationResponse)
async def analyze_paper_cooperation(
    req: PaperCooperationRequest,
) -> PaperCooperationResponse:
    try:
        return application.analyze(req.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/build", response_model=PaperCooperationBuildResponse)
async def build_paper_cooperation(
    req: PaperCooperationRequest,
) -> PaperCooperationBuildResponse:
    try:
        return application.build(req.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
