# tests/integration/test_auth.py

import uuid
from datetime import datetime, timedelta, timezone

import faker
import jwt
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.settings.settings import get_settings
from src.users.schemas import TokenResponse, UserCreate, UserResponse
from src.users.tokens import create_refresh_token
from tests.factories import UserFactory


# /auth/register
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


async def test_register_repeated_user(client: AsyncClient, db_session: AsyncSession):
    # Given
    existing_user = UserFactory.build()  # password == "password"
    db_session.add(existing_user)
    await db_session.commit()

    fake = faker.Faker()
    user_data = UserCreate(
        email=fake.email(),
        username=existing_user.username,
        password=fake.password(),
    )

    # When
    response = await client.post(
        url="http://test/api/v1/auth/register", json=user_data.model_dump()
    )

    # Then
    assert response.status_code == 409
    assert response.json()["detail"] == "Username or email already in use."


async def test_register_repeated_email(client: AsyncClient, db_session: AsyncSession):
    # Given
    existing_user = UserFactory.build()  # password == "password"
    db_session.add(existing_user)
    await db_session.commit()

    fake = faker.Faker()
    user_data = UserCreate(
        email=existing_user.email,
        username=fake.user_name(),
        password=fake.password(),
    )

    # When
    response = await client.post(
        url="http://test/api/v1/auth/register", json=user_data.model_dump()
    )

    # Then
    assert response.status_code == 409
    assert response.json()["detail"] == "Username or email already in use."


# /auth/login
async def test_login_ok(client: AsyncClient, db_session: AsyncSession):
    # Given
    user = UserFactory.build()  # password == "password"
    db_session.add(user)
    await db_session.commit()

    login_data = {"username": user.email, "password": "password"}

    # When
    response = await client.post(url="http://test/api/v1/auth/login", data=login_data)

    # Then
    assert response.status_code == 200
    TokenResponse.model_validate(response.json())
    assert response.json()["access_token"]


async def test_login_wrong_email(client: AsyncClient, db_session: AsyncSession):
    # Given
    user = UserFactory.build()  # password == "password"
    db_session.add(user)
    await db_session.commit()

    login_data = {
        "username": "test@test.com",
        "password": "password",
    }

    # When
    response = await client.post(url="http://test/api/v1/auth/login", data=login_data)

    # Then
    assert response.status_code == 401
    assert "access_token" not in response.json()


async def test_login_wrong_password(client: AsyncClient, db_session: AsyncSession):
    # Given
    user = UserFactory.build()  # password == "password"
    db_session.add(user)
    await db_session.commit()

    login_data = {
        "username": user.email,
        "password": "wrong_password",
    }

    # When
    response = await client.post(url="http://test/api/v1/auth/login", data=login_data)

    # Then
    assert response.status_code == 401
    assert "access_token" not in response.json()


# /auth/refresh
async def test_refresh_ok(client: AsyncClient, db_session: AsyncSession):
    # Given
    user = UserFactory.build()  # password == "password"
    db_session.add(user)
    await db_session.commit()

    refresh_token = create_refresh_token(subject=str(user.id))

    refresh_data = {"refresh_token": refresh_token}

    # When
    response = await client.post(
        url="http://test/api/v1/auth/refresh", json=refresh_data
    )

    # Then
    assert response.status_code == 200
    TokenResponse.model_validate(response.json())
    assert response.json()["access_token"]


def make_refresh_jwt(
    subject: str, expired: bool = False, token_type: str = "refresh"
) -> str:
    settings = get_settings()
    return jwt.encode(
        payload={
            "sub": subject,
            "exp": datetime.now(timezone.utc) + timedelta(days=-1 if expired else 1),
            "type": token_type,
        },
        key=settings.secret_key.get_secret_value(),
        algorithm="HS256",
    )


async def test_refresh_invalid_token(client: AsyncClient):
    # Given
    refresh_token = "invalid-refresh-token"
    refresh_data = {"refresh_token": refresh_token}

    # When
    response = await client.post(
        url="http://test/api/v1/auth/refresh", json=refresh_data
    )

    # Then
    assert response.status_code == 401
    assert "access_token" not in response.json()


async def test_refresh_invalid_type(client: AsyncClient, db_session: AsyncSession):
    # Given
    user = UserFactory.build()  # password == "password"
    db_session.add(user)
    await db_session.commit()

    refresh_token = make_refresh_jwt(subject=str(user.id), token_type="invalid-type")
    refresh_data = {"refresh_token": refresh_token}

    # When
    response = await client.post(
        url="http://test/api/v1/auth/refresh", json=refresh_data
    )

    # Then
    assert response.status_code == 401
    assert "access_token" not in response.json()


async def test_refresh_invalid_user_id(client: AsyncClient, db_session: AsyncSession):
    # Given
    user = UserFactory.build()  # password == "password"
    db_session.add(user)
    await db_session.commit()

    refresh_token = make_refresh_jwt(subject="invalid-user-id")
    refresh_data = {"refresh_token": refresh_token}

    # When
    response = await client.post(
        url="http://test/api/v1/auth/refresh", json=refresh_data
    )

    # Then
    assert response.status_code == 401
    assert "access_token" not in response.json()


async def test_refresh_user_not_found(client: AsyncClient):
    # Given
    refresh_token = make_refresh_jwt(subject=str(uuid.uuid4()))
    refresh_data = {"refresh_token": refresh_token}

    # When
    response = await client.post(
        url="http://test/api/v1/auth/refresh", json=refresh_data
    )

    # Then
    assert response.status_code == 401
    assert "access_token" not in response.json()


async def test_refresh_expired_token(
    client: AsyncClient,
    db_session: AsyncSession,
):
    # Given
    user = UserFactory.build()  # password == "password"
    db_session.add(user)
    await db_session.commit()

    refresh_token = make_refresh_jwt(subject=str(user.id), expired=True)
    refresh_data = {"refresh_token": refresh_token}

    # When
    response = await client.post(
        url="http://test/api/v1/auth/refresh", json=refresh_data
    )

    # Then
    assert response.status_code == 401
    assert "access_token" not in response.json()
