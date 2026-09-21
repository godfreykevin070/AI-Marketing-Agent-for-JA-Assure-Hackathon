from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.agents.graph import run_content_pipeline
from app.db import get_db
from app.models import ContentAsset
from app.schemas import AssetOut, GenerateRequest, GenerateResponse
from app.deps import get_current_user

router = APIRouter(prefix="/content", tags=["content"], dependencies=[Depends(get_current_user)])


@router.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest, db: Session = Depends(get_db)) -> GenerateResponse:
    """Run the full The Brain pipeline: research → content → localise → video →
    compliance → persist into the pending-review queue."""
    result = run_content_pipeline(db, request)
    asset_ids = result.get("asset_ids", [])

    assets: list[ContentAsset] = []
    if asset_ids:
        assets = list(
            db.execute(select(ContentAsset).where(ContentAsset.id.in_(asset_ids)))
            .scalars()
            .all()
        )
        order = {aid: i for i, aid in enumerate(asset_ids)}
        assets.sort(key=lambda a: order.get(a.id, 0))

    return GenerateResponse(
        run_id=result.get("run_id", ""),
        assets=[AssetOut.model_validate(a) for a in assets],
        research=result.get("research"),
        errors=result.get("errors", []),
    )


@router.get("/assets", response_model=list[AssetOut])
def list_assets(
    db: Session = Depends(get_db),
    status: str | None = Query(default=None),
    brand: str | None = Query(default=None),
    platform: str | None = Query(default=None),
    language: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[AssetOut]:
    stmt = select(ContentAsset).order_by(desc(ContentAsset.created_at)).limit(limit)
    if status:
        stmt = stmt.where(ContentAsset.status == status)
    if brand:
        stmt = stmt.where(ContentAsset.brand == brand)
    if platform:
        stmt = stmt.where(ContentAsset.platform == platform)
    if language:
        stmt = stmt.where(ContentAsset.language == language)

    assets = list(db.execute(stmt).scalars().all())
    return [AssetOut.model_validate(a) for a in assets]


@router.get("/assets/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: str, db: Session = Depends(get_db)) -> AssetOut:
    asset = db.get(ContentAsset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return AssetOut.model_validate(asset)