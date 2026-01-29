from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db import get_db_session
from src.api.repositories import query_syllabus_mappings
from src.api.schemas import SyllabusMappingsOut, SyllabusMappingOut

router = APIRouter(prefix="/syllabus", tags=["syllabus"])


@router.get(
    "/mappings",
    response_model=SyllabusMappingsOut,
    summary="Query syllabus mappings",
    description="Query syllabus mappings by game_id and/or subject.",
)
async def get_mappings(
    game_id: Optional[int] = Query(None, description="Filter by game ID."),
    subject: Optional[str] = Query(None, description="Filter by subject (exact match)."),
    session: AsyncSession = Depends(get_db_session),
) -> SyllabusMappingsOut:
    """Return syllabus mappings."""
    rows = await query_syllabus_mappings(session, game_id=game_id, subject=subject)
    return SyllabusMappingsOut(
        items=[
            SyllabusMappingOut(
                game_id=m.game_id,
                game_slug=g.slug,
                standard_code=m.standard_code,
                standard_label=m.standard_label,
                subject=m.subject,
                grade_band=m.grade_band,
            )
            for m, g in rows
        ]
    )
