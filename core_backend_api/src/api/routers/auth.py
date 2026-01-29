from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db import get_db_session
from src.api.repositories import authenticate_user, create_user
from src.api.schemas import ApiMessage, AuthLoginRequest, AuthSignupRequest, AuthTokenResponse
from src.api.security import create_placeholder_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=AuthTokenResponse,
    summary="Sign up (local placeholder)",
    description="Creates a user with email/password (hashed) and returns a placeholder token.",
)
async def signup(payload: AuthSignupRequest, session: AsyncSession = Depends(get_db_session)) -> AuthTokenResponse:
    """Create a local user account and return a placeholder token."""
    try:
        user = await create_user(session, payload.email, payload.display_name, payload.password)
    except Exception as e:
        # Likely unique constraint
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists") from e
    return AuthTokenResponse(token=create_placeholder_token(user.id), user_id=user.id, display_name=user.display_name)


@router.post(
    "/login",
    response_model=AuthTokenResponse,
    summary="Login (local placeholder)",
    description="Validates email/password and returns a placeholder token.",
)
async def login(payload: AuthLoginRequest, session: AsyncSession = Depends(get_db_session)) -> AuthTokenResponse:
    """Authenticate a local user and return a placeholder token."""
    user = await authenticate_user(session, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return AuthTokenResponse(token=create_placeholder_token(user.id), user_id=user.id, display_name=user.display_name)


@router.post(
    "/logout",
    response_model=ApiMessage,
    summary="Logout (no-op)",
    description="Placeholder logout endpoint for local auth mode.",
)
async def logout() -> ApiMessage:
    """Logout in placeholder auth mode (no server state)."""
    return ApiMessage(message="Logged out")
