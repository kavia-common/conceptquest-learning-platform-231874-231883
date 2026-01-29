from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.db import _get_engine
from src.api.models import Base
from src.api.repositories import ensure_seed_data
from src.api.routers.auth import router as auth_router
from src.api.routers.games import router as games_router
from src.api.routers.progress import router as progress_router
from src.api.routers.syllabus import router as syllabus_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    App lifespan hook:
    - create tables (create_all fallback; migrations can be added later)
    - seed minimal data so UI works end-to-end in preview
    """
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed data using a session
    # Import here to avoid import cycles
    from src.api.db import get_db_session  # pylint: disable=import-outside-toplevel

    async for session in get_db_session():
        await ensure_seed_data(session)
        break

    yield


openapi_tags = [
    {"name": "system", "description": "Health and operational endpoints."},
    {"name": "auth", "description": "Local placeholder authentication."},
    {"name": "games", "description": "Game catalog and session/result APIs."},
    {"name": "progress", "description": "Progress and achievement tracking."},
    {"name": "syllabus", "description": "Syllabus standards mapping queries."},
]

app = FastAPI(
    title="Concept Quest Learning Platform API",
    description=(
        "Backend for 5-minute concept games, progress tracking, achievements, and syllabus mapping.\n\n"
        "Auth is placeholder/local for preview. Provide POSTGRES_URL to connect to Postgres."
    ),
    version="0.1.0",
    openapi_tags=openapi_tags,
    lifespan=lifespan,
)

# CORS: allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",  # keep permissive for preview; tighten in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/",
    tags=["system"],
    summary="Health check",
    description="Simple healthcheck endpoint.",
)
def health_check():
    """Return a basic health response."""
    return {"message": "Healthy"}


@app.get(
    "/docs/help",
    tags=["system"],
    summary="API usage help",
    description="Quick links and usage notes for the preview system.",
)
def docs_help():
    """Help endpoint for quick discovery in preview."""
    return {
        "docs": "/docs",
        "openapi": "/openapi.json",
        "notes": [
            "Use /auth/signup and /auth/login to obtain a placeholder token.",
            "Use /games to list games, /games/start to start a mock session, /games/submit to submit results.",
            "Use /progress/{user_id} and /achievements/{user_id} to view user state.",
            "Use /syllabus/mappings to query standards mappings.",
        ],
    }


# Routers
app.include_router(auth_router)
app.include_router(games_router)
app.include_router(progress_router)
app.include_router(syllabus_router)
