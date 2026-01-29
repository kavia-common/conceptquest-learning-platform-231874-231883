from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class User(Base):
    """Represents an end-user of the learning platform."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    progress: Mapped[List["Progress"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    achievements: Mapped[List["UserAchievement"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Game(Base):
    """A 5-minute micro-game definition."""

    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    concept: Mapped[str] = mapped_column(String(120), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    levels: Mapped[List["GameLevel"]] = relationship(back_populates="game", cascade="all, delete-orphan")
    syllabus_mappings: Mapped[List["SyllabusMapping"]] = relationship(back_populates="game", cascade="all, delete-orphan")


class GameLevel(Base):
    """Difficulty/level variant for a given game."""

    __tablename__ = "game_levels"
    __table_args__ = (UniqueConstraint("game_id", "difficulty", name="uq_game_level_difficulty"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..N
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    target_score: Mapped[int] = mapped_column(Integer, default=80, nullable=False)

    game: Mapped["Game"] = relationship(back_populates="levels")
    progress: Mapped[List["Progress"]] = relationship(back_populates="level")


class Progress(Base):
    """Tracks a user's progress per (game, difficulty)."""

    __tablename__ = "progress"
    __table_args__ = (UniqueConstraint("user_id", "game_id", "difficulty", name="uq_progress_user_game_diff"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True, nullable=False)

    # Denormalized to simplify queries; mirrors GameLevel.difficulty
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)

    best_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mastered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_played_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="progress")
    level: Mapped[Optional["GameLevel"]] = relationship(
        back_populates="progress",
        primaryjoin="and_(Progress.game_id==GameLevel.game_id, Progress.difficulty==GameLevel.difficulty)",
        viewonly=True,
    )


class Achievement(Base):
    """An achievement definition (badge)."""

    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)


class UserAchievement(Base):
    """Join table indicating which user has earned which achievement."""

    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id", ondelete="CASCADE"), index=True, nullable=False)
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="achievements")
    achievement: Mapped["Achievement"] = relationship()


class SyllabusMapping(Base):
    """Maps a game/concept to a syllabus standard (e.g., grade, subject, code)."""

    __tablename__ = "syllabus_mappings"
    __table_args__ = (UniqueConstraint("game_id", "standard_code", name="uq_mapping_game_standard"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True, nullable=False)

    standard_code: Mapped[str] = mapped_column(String(64), nullable=False)
    standard_label: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(64), nullable=False)
    grade_band: Mapped[str] = mapped_column(String(32), nullable=False)

    game: Mapped["Game"] = relationship(back_populates="syllabus_mappings")
