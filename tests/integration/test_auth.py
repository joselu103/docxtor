# tests/integration/test_auth.py

import faker
from httpx import AsyncClient

from src.users.schemas import UserCreate, UserResponse


async def test_register_user(client: AsyncClient):
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
