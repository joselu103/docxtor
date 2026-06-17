# src/users/router.py

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.engine import get_db, transaction
from src.users.exceptions import DuplicateUserError, LoginError, RefreshError
from src.users.schemas import RefreshRequest, TokenResponse, UserCreate, UserResponse
from src.users.service import UserService

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["auth"])


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserService:
    return UserService(session)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_service: Annotated[UserService, Depends(get_user_service)],
    user_data: UserCreate,
) -> UserResponse:
    """Create new user with email, username and password.

    Returns:
        New user data.

    Raises:
        HTTPException(409): Username or email already in use.
    """
    try:
        async with transaction(user_service.session):
            new_user = await user_service.register_new_user(user_data)
            return UserResponse.model_validate(new_user)

    except DuplicateUserError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Username or email already in use."
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    user_service: Annotated[UserService, Depends(get_user_service)],
    user_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    """Login user with email and password.

    Returns:
        Access and Refresh tokens.

    Raises:
        HTTPException(401): Wrong email or password.
    """
    try:
        access_token, refresh_token = await user_service.login(user_data)
        return TokenResponse(
            access_token=access_token, refresh_token=refresh_token, token_type="bearer"
        )
    except LoginError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong email or password.")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_user(
    user_service: Annotated[UserService, Depends(get_user_service)],
    refresh_data: RefreshRequest,
) -> TokenResponse:
    """Attempt to obtain a new access token with a refresh token.

    Returns:
        Access and Refresh tokens.

    Raises:
        HTTPException(401): Refresh token invalid or revoked
    """
    try:
        access_token, refresh_token = await user_service.refresh(refresh_data)
        return TokenResponse(
            access_token=access_token, refresh_token=refresh_token, token_type="bearer"
        )
    except RefreshError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Refresh token invalid or revoked"
        )
