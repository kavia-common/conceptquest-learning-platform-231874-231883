from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models import Achievement, Game, GameLevel, Progress, SyllabusMapping, User, UserAchievement
from src.api.security import hash_password, verify_password


# PUBLIC_INTERFACE
async def ensure_seed_data(session: AsyncSession) -> None:
    """
    Ensure minimal seed data exists so the app is usable in preview.

    Creates:
    - A few games + levels
    - A few achievements
    - Syllabus mappings for each game

    This is idempotent (safe to call on startup).
    """
    # Games
    games_count = await session.scalar(select(func.count(Game.id)))
    if (games_count or 0) == 0:
        frac = Game(
            slug="fraction-frenzy",
            title="Fraction Frenzy",
            description="Quick-fire fraction comparisons and simplification.",
            concept="Fractions",
            active=True,
        )
        neg = Game(
            slug="negative-ninja",
            title="Negative Ninja",
            description="Navigate number lines and operations with negatives.",
            concept="Integers (Negative Numbers)",
            active=True,
        )
        sess = Game(
            slug="ratio-rally",
            title="Ratio Rally",
            description="Match ratios and scale recipes at speed.",
            concept="Ratios",
            active=True,
        )
        session.add_all([frac, neg, sess])
        await session.flush()

        def levels_for(game: Game) -> List[GameLevel]:
            return [
                GameLevel(game_id=game.id, difficulty=1, title="Warm-up", target_score=70),
                GameLevel(game_id=game.id, difficulty=2, title="Standard", target_score=80),
                GameLevel(game_id=game.id, difficulty=3, title="Challenge", target_score=90),
            ]

        session.add_all(levels_for(frac) + levels_for(neg) + levels_for(sess))

        # Syllabus mappings (sample)
        session.add_all(
            [
                SyllabusMapping(
                    game_id=frac.id,
                    standard_code="MATH.6.NS.A.1",
                    standard_label="Interpret and compute quotients of fractions.",
                    subject="Math",
                    grade_band="6",
                ),
                SyllabusMapping(
                    game_id=neg.id,
                    standard_code="MATH.6.NS.C.5",
                    standard_label="Understand positive/negative numbers on number line.",
                    subject="Math",
                    grade_band="6",
                ),
                SyllabusMapping(
                    game_id=sess.id,
                    standard_code="MATH.6.RP.A.1",
                    standard_label="Understand ratio concepts and use ratio reasoning.",
                    subject="Math",
                    grade_band="6",
                ),
            ]
        )

    # Achievements
    ach_count = await session.scalar(select(func.count(Achievement.id)))
    if (ach_count or 0) == 0:
        session.add_all(
            [
                Achievement(
                    key="first_attempt",
                    title="First Steps",
                    description="Complete your first game attempt.",
                ),
                Achievement(
                    key="first_mastery",
                    title="Mastery Unlocked",
                    description="Reach mastery in any game difficulty.",
                ),
                Achievement(
                    key="high_score_90",
                    title="90+ Club",
                    description="Score 90 or higher in a session.",
                ),
            ]
        )

    await session.commit()


# PUBLIC_INTERFACE
async def create_user(session: AsyncSession, email: str, display_name: str, password: str) -> User:
    """Create a new user."""
    user = User(email=email.lower().strip(), display_name=display_name.strip(), password_hash=hash_password(password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


# PUBLIC_INTERFACE
async def authenticate_user(session: AsyncSession, email: str, password: str) -> Optional[User]:
    """Validate email/password; return user if valid."""
    stmt: Select[Tuple[User]] = select(User).where(User.email == email.lower().strip())
    user = await session.scalar(stmt)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# PUBLIC_INTERFACE
async def list_games(session: AsyncSession) -> List[Game]:
    """Return active games with levels loaded."""
    games = (await session.scalars(select(Game).where(Game.active == True).order_by(Game.id))).all()  # noqa: E712
    # Levels are relationship-loaded lazily; for simplicity in preview, fetch per game
    for g in games:
        g.levels = (await session.scalars(select(GameLevel).where(GameLevel.game_id == g.id).order_by(GameLevel.difficulty))).all()
    return games


# PUBLIC_INTERFACE
async def record_result_and_update_progress(
    session: AsyncSession,
    user_id: int,
    game_id: int,
    difficulty: int,
    score: int,
) -> Tuple[Progress, List[str]]:
    """
    Update progress based on a submitted result and return earned achievement keys.

    Rules (minimal):
    - Increment attempts
    - Update best_score if better
    - Mark mastered if score >= target_score for that game/difficulty
    - Achievements:
      * first_attempt: if this was user's first ever attempt
      * first_mastery: if user masters any difficulty for first time
      * high_score_90: if score >= 90
    """
    earned_keys: List[str] = []

    # Ensure progress row exists
    prog = await session.scalar(
        select(Progress).where(
            and_(Progress.user_id == user_id, Progress.game_id == game_id, Progress.difficulty == difficulty)
        )
    )
    if not prog:
        prog = Progress(user_id=user_id, game_id=game_id, difficulty=difficulty, best_score=0, attempts=0, mastered=False)
        session.add(prog)
        await session.flush()

    # Determine if this is first attempt ever (across all games)
    total_attempts = await session.scalar(select(func.sum(Progress.attempts)).where(Progress.user_id == user_id))
    total_attempts = int(total_attempts or 0)

    prog.attempts += 1
    if score > prog.best_score:
        prog.best_score = score
    prog.last_played_at = datetime.utcnow()

    # Mastery check
    target = await session.scalar(
        select(GameLevel.target_score).where(and_(GameLevel.game_id == game_id, GameLevel.difficulty == difficulty))
    )
    target_score = int(target or 80)
    was_mastered = prog.mastered
    if score >= target_score:
        prog.mastered = True

    await session.flush()

    # Achievements
    if total_attempts == 0:
        earned_keys.append("first_attempt")
    if (not was_mastered) and prog.mastered:
        # Check if user already mastered any other difficulty previously
        mastered_any = await session.scalar(select(func.count(Progress.id)).where(and_(Progress.user_id == user_id, Progress.mastered == True)))  # noqa: E712
        # After flush, current mastery included, so <=1 means this is first mastery
        if int(mastered_any or 0) <= 1:
            earned_keys.append("first_mastery")
    if score >= 90:
        earned_keys.append("high_score_90")

    if earned_keys:
        # Insert missing user_achievements
        achievements = (await session.scalars(select(Achievement).where(Achievement.key.in_(earned_keys)))).all()
        for ach in achievements:
            existing = await session.scalar(
                select(UserAchievement).where(
                    and_(UserAchievement.user_id == user_id, UserAchievement.achievement_id == ach.id)
                )
            )
            if not existing:
                session.add(UserAchievement(user_id=user_id, achievement_id=ach.id))

    await session.commit()
    await session.refresh(prog)
    return prog, earned_keys


# PUBLIC_INTERFACE
async def get_progress(session: AsyncSession, user_id: int) -> List[Tuple[Progress, Game]]:
    """Return progress rows joined with game for display."""
    rows = (await session.execute(select(Progress, Game).join(Game, Progress.game_id == Game.id).where(Progress.user_id == user_id))).all()
    return rows


# PUBLIC_INTERFACE
async def get_achievements(session: AsyncSession, user_id: int) -> Tuple[List[Achievement], List[UserAchievement]]:
    """Return all achievements and the ones earned by the user."""
    all_ach = (await session.scalars(select(Achievement).order_by(Achievement.id))).all()
    earned = (await session.scalars(select(UserAchievement).where(UserAchievement.user_id == user_id))).all()
    return all_ach, earned


# PUBLIC_INTERFACE
async def query_syllabus_mappings(
    session: AsyncSession, game_id: Optional[int] = None, subject: Optional[str] = None
) -> List[Tuple[SyllabusMapping, Game]]:
    """Query syllabus mappings by optional filters."""
    stmt = select(SyllabusMapping, Game).join(Game, SyllabusMapping.game_id == Game.id)
    if game_id is not None:
        stmt = stmt.where(SyllabusMapping.game_id == game_id)
    if subject:
        stmt = stmt.where(SyllabusMapping.subject == subject)
    return (await session.execute(stmt.order_by(SyllabusMapping.id))).all()
