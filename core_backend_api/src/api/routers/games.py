from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db import get_db_session
from src.api.repositories import list_games, record_result_and_update_progress
from src.api.schemas import GameOut, StartSessionRequest, StartSessionResponse, SubmitResultRequest

router = APIRouter(prefix="/games", tags=["games"])


@router.get(
    "",
    response_model=List[GameOut],
    summary="List games",
    description="Returns the available micro-games and their difficulty levels.",
)
async def get_games(session: AsyncSession = Depends(get_db_session)) -> List[GameOut]:
    """List available games."""
    games = await list_games(session)
    return [
        GameOut(
            id=g.id,
            slug=g.slug,
            title=g.title,
            description=g.description,
            concept=g.concept,
            levels=[{"difficulty": lv.difficulty, "title": lv.title, "target_score": lv.target_score} for lv in g.levels],
        )
        for g in games
    ]


@router.post(
    "/start",
    response_model=StartSessionResponse,
    summary="Start game session",
    description="Creates a mock session id for a user/game/difficulty selection.",
)
async def start_session(payload: StartSessionRequest) -> StartSessionResponse:
    """Start a mock game session."""
    return StartSessionResponse(
        session_id=str(uuid.uuid4()),
        started_at=datetime.utcnow(),
        game_id=payload.game_id,
        difficulty=payload.difficulty,
    )


@router.post(
    "/submit",
    summary="Submit game result",
    description="Submits a result and updates progress + achievements.",
)
async def submit_result(payload: SubmitResultRequest, session: AsyncSession = Depends(get_db_session)) -> dict:
    """Submit result and return updated progress snapshot + earned achievements."""
    prog, earned = await record_result_and_update_progress(
        session=session,
        user_id=payload.user_id,
        game_id=payload.game_id,
        difficulty=payload.difficulty,
        score=payload.score,
    )
    return {
        "progress": {
            "user_id": payload.user_id,
            "game_id": payload.game_id,
            "difficulty": payload.difficulty,
            "best_score": prog.best_score,
            "attempts": prog.attempts,
            "mastered": prog.mastered,
            "last_played_at": prog.last_played_at,
        },
        "earned_achievements": earned,
    }
