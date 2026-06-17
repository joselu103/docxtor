# src/users/service.py

import uuid

import structlog
from asyncpg.exceptions import UniqueViolationError
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.exceptions import (
    DuplicateUserError,
    InvalidToken,
    InvalidTokenType,
    InvalidUserID,
    UserNotFound,
    UserNotFound_,
    WrongPassword,
)
from src.users.models import User
from src.users.repository import UserRepository
from src.users.schemas import RefreshRequest, UserCreate
from src.users.security import hash_password, verify_password
from src.users.tokens import (
    JWTValidationException,
    create_access_token,
    create_refresh_token,
    decode_token,
)

logger = structlog.get_logger()

email_adapter = TypeAdapter(EmailStr)


def _is_email(value: str) -> bool:
    try:
        email_adapter.validate_python(value)
        return True
    except ValidationError:
        return False


# Services
class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register_new_user(self, user_data: UserCreate) -> User:
        """Create a new user.

        Args:
            user_data: information to create the new user.

        Returns:
            New user model.

        Raises:
            DuplicateUserError: Username or email already in use.
        """
        try:
            new_user = User(
                email=user_data.email,
                username=user_data.username,
                hashed_password=hash_password(user_data.password),
            )
            await self.user_repo.create(new_user)
            return new_user
        except IntegrityError as e:
            if isinstance(e.orig.__cause__, UniqueViolationError):
                raise DuplicateUserError("Username or email already in use")
            await logger.aexception("integrity_error")
            raise

    async def login(self, user_data: OAuth2PasswordRequestForm) -> tuple[str, str]:
        """Verify the user data and creates an access token.

        Args:
            user_data: information to log in.

        Returns:
            Access and refresh tokens

        Raises:
            UserNotFound: Wrong username/email
            WrongPassword: Wrong password
        """
        if _is_email(user_data.username):
            user = await self.user_repo.get_by_email(user_data.username)
        else:
            user = await self.user_repo.get_by_username(user_data.username)

        if not user:
            raise UserNotFound(user_data.username)

        if not verify_password(user_data.password, user.hashed_password):
            raise WrongPassword

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        return (access_token, refresh_token)

    async def refresh(self, refresh_data: RefreshRequest) -> tuple[str, str]:
        """Verify the refresh token and return it and a new access token.

        Args:
            refresh_data: contains the 'refresh_token'.

        Returns:
            New access token and same refresh token.

        Raises:
            RefreshToken: Invalid refresh token.
        """
        try:
            payload = decode_token(refresh_data.refresh_token)
        except JWTValidationException:
            raise InvalidToken(refresh_data.refresh_token)

        if payload.get("type") != "refresh":
            raise InvalidTokenType(payload.get("type"))

        try:
            user_id = uuid.UUID(payload["sub"])
        except ValueError:
            raise InvalidUserID(payload["sub"])

        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise UserNotFound_(user_id)

        access_token = create_access_token(str(user.id))
        return (access_token, refresh_data.refresh_token)
