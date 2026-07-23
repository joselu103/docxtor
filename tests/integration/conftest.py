import faker
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.engine import transaction
from src.users.models import User
from src.users.repository import UserRepository
from src.users.security import hash_password
from src.users.tokens import create_access_token


@pytest.fixture
async def access_token(db_session: AsyncSession) -> str:
    user_repo = UserRepository(db_session)

    fake = faker.Faker()
    username = fake.user_name()
    email = fake.email()
    password = fake.password()

    async with transaction(db_session):
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
        )
        await user_repo.create(user)

    return create_access_token(str(user.id))
