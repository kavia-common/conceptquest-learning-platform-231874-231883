from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db import get_db_session
from src.api.repositories import get_achievements, get_progress
from src.api.schemas import AchievementsOut, AchievementOut, ProgressOut, ProgressItemOut

router = APIRouter(tags=["progress"])


@router.get(
    "/progress/{user_id}",
    response_model=ProgressOut,
    summary="Fetch progress",
    description="Returns per-game, per-difficulty progress for a user.",
)
async def fetch_progress(user_id: int, session: AsyncSession = Depends(get_db_session)) -> ProgressOut:
    """Fetch progress for the given user."""
    rows = await get_progress(session, user_id=user_id)
    items: List[ProgressItemOut] = []
    for prog, game in rows:
        items.append(
            ProgressItemOut(
                game_id=prog.game_id,
                game_slug=game.slug,
                difficulty=prog.difficulty,
                best_score=prog.best_score,
                attempts=prog.attempts,
                mastered=prog.mastered,
                last_played_at=prog.last_played_at,
            )
        )
    return ProgressOut(user_id=user_id, items=items)


@router.get(
    "/achievements/{user_id}",
    response_model=AchievementsOut,
    summary="Fetch achievements",
    description="Returns the achievement catalog with earned status for a user.",
)
async def fetch_achievements(user_id: int, session: AsyncSession = Depends(get_db_session)) -> AchievementsOut:
    """Fetch achievements for the given user."""
    all_ach, earned = await get_achievements(session, user_id=user_id)
    earned_by_id: Dict[int, datetime] = {ua.achievement_id: ua.earned_at for ua in earned}
    items = [
        AchievementOut(
            key=a.key,
            title=a.title,
            description=a.description,
            earned_at=earned_by_id.get(a.id),
        )
        for a in all_ach
    ]
    return AchievementsOut(user_id=user_id, items=items)
