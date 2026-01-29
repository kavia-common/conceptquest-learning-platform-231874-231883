from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ApiMessage(BaseModel):
    """Generic message response."""
    message: str = Field(..., description="Human-readable message.")


class AuthSignupRequest(BaseModel):
    email: str = Field(..., description="User email (unique).")
    display_name: str = Field(..., description="Display name for the user.")
    password: str = Field(..., description="Password (stored as hash).")


class AuthLoginRequest(BaseModel):
    email: str = Field(..., description="User email.")
    password: str = Field(..., description="User password.")


class AuthTokenResponse(BaseModel):
    token: str = Field(..., description="Placeholder auth token (not JWT).")
    user_id: int = Field(..., description="User ID associated with the token.")
    display_name: str = Field(..., description="User display name.")


class GameLevelOut(BaseModel):
    difficulty: int = Field(..., description="Difficulty level (1..N).")
    title: str = Field(..., description="Level title.")
    target_score: int = Field(..., description="Score required to be considered mastery.")


class GameOut(BaseModel):
    id: int = Field(..., description="Game ID.")
    slug: str = Field(..., description="Stable slug for the game.")
    title: str = Field(..., description="Display title.")
    description: str = Field(..., description="Game description.")
    concept: str = Field(..., description="The single concept taught by this game.")
    levels: List[GameLevelOut] = Field(default_factory=list, description="Available difficulty levels.")


class StartSessionRequest(BaseModel):
    user_id: int = Field(..., description="User starting a session.")
    game_id: int = Field(..., description="Game being played.")
    difficulty: int = Field(1, ge=1, description="Difficulty being played.")


class StartSessionResponse(BaseModel):
    session_id: str = Field(..., description="Server-generated session identifier.")
    started_at: datetime = Field(..., description="UTC time session started.")
    game_id: int = Field(..., description="Game being played.")
    difficulty: int = Field(..., description="Difficulty being played.")


class SubmitResultRequest(BaseModel):
    user_id: int = Field(..., description="User submitting result.")
    game_id: int = Field(..., description="Game played.")
    difficulty: int = Field(1, ge=1, description="Difficulty played.")
    score: int = Field(..., ge=0, le=100, description="Score achieved (0..100).")
    duration_seconds: int = Field(..., ge=0, le=3600, description="Duration in seconds.")


class ProgressItemOut(BaseModel):
    game_id: int = Field(..., description="Game ID.")
    game_slug: str = Field(..., description="Game slug.")
    difficulty: int = Field(..., description="Difficulty.")
    best_score: int = Field(..., description="Best score achieved.")
    attempts: int = Field(..., description="Number of attempts.")
    mastered: bool = Field(..., description="Whether mastery achieved at this difficulty.")
    last_played_at: Optional[datetime] = Field(None, description="When last played.")


class ProgressOut(BaseModel):
    user_id: int = Field(..., description="User ID.")
    items: List[ProgressItemOut] = Field(default_factory=list, description="Progress entries.")


class AchievementOut(BaseModel):
    key: str = Field(..., description="Achievement key.")
    title: str = Field(..., description="Achievement title.")
    description: str = Field(..., description="Achievement description.")
    earned_at: Optional[datetime] = Field(None, description="When earned (if earned).")


class AchievementsOut(BaseModel):
    user_id: int = Field(..., description="User ID.")
    items: List[AchievementOut] = Field(default_factory=list, description="Achievements earned/unearned.")


class SyllabusMappingOut(BaseModel):
    game_id: int = Field(..., description="Game ID.")
    game_slug: str = Field(..., description="Game slug.")
    standard_code: str = Field(..., description="Standard code.")
    standard_label: str = Field(..., description="Standard label.")
    subject: str = Field(..., description="Subject (e.g., Math).")
    grade_band: str = Field(..., description="Grade band (e.g., 6-8).")


class SyllabusMappingsOut(BaseModel):
    items: List[SyllabusMappingOut] = Field(default_factory=list, description="Syllabus mappings.")
