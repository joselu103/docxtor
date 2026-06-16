# src/users/service.py

import structlog
from asyncpg.exceptions import UniqueViolationError
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models import User
from src.users.repository import UserRepository
from src.users.schemas import UserCreate
from src.users.security import hash_password, verify_password
from src.users.tokens import create_access_token, create_refresh_token

logger = structlog.get_logger()


# Exceptions
class RegisterError(Exception): ...


class DuplicateUserError(RegisterError): ...


class LoginError(Exception): ...


class UserNotFound(LoginError): ...


class WrongPassword(LoginError): ...


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
            UserNotFound: Wrong email
            WrongPassword: Wrong password
        """
        user = await self.user_repo.get_by_email(user_data.username)

        if not user:
            raise UserNotFound(user_data.username)

        if not verify_password(user_data.password, user.hashed_password):
            raise WrongPassword

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        return (access_token, refresh_token)
