from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from biz.router.register import register_routers

app = FastAPI(
    title="Tech KG API",
    description="Backend service for the technology knowledge graph.",
    version="0.1.0",
)

register_routers(app)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_INDEX = PROJECT_ROOT / "frontend" / "index.html"


@app.get("/", include_in_schema=False)
@app.get("/binding", include_in_schema=False)
async def serve_frontend_index() -> FileResponse:
    return FileResponse(FRONTEND_INDEX)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
