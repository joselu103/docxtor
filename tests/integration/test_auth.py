# tests/integration/test_auth.py

import faker
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.schemas import UserCreate, UserResponse
from tests.factories import UserFactory


async def test_register_user_ok(client: AsyncClient):
    # Given
    fake = faker.Faker()

    user_data = UserCreate(
        email=fake.email(),
        username=fake.user_name(),
        password=fake.password(),
    )

    # When
    response = await client.post(
        url="http://test/api/v1/auth/register", json=user_data.model_dump()
    )

    # Then
    assert response.status_code == 201
    UserResponse.model_validate(response.json())


@pytest.mark.parametrize(
    "repeated_user, repeated_email", [(True, False), (False, True)]
)
async def test_register_new_user_repeated_error(
    client: AsyncClient, db_session: AsyncSession, repeated_user, repeated_email
):
    # Given
    existing_user = UserFactory.build()  # password == "password"
    db_session.add(existing_user)
    await db_session.commit()

    fake = faker.Faker()
    user_data = UserCreate(
        email=existing_user.email if repeated_email else fake.email(),
        username=existing_user.username if repeated_user else fake.user_name(),
        password=fake.password(),
    )

    # When
    response = await client.post(
        url="http://test/api/v1/auth/register", json=user_data.model_dump()
    )

    # Then
    assert response.status_code == 409
    assert response.json()["detail"] == "Username or email already in use."
