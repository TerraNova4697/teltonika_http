from datetime import datetime, timedelta, timezone
import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import jwt
from fastapi.security import OAuth2PasswordRequestForm

from src.teltonika_http.infra.db.models import UserModel


@pytest.fixture(scope="session")
def environs():
    return {
        "POSTGRES_DB": os.environ['POSTGRES_DB'],
        "POSTGRES_USER": os.environ['POSTGRES_USER'],
        "POSTGRES_PASSWORD": os.environ['POSTGRES_PASSWORD'],

        # HTTP
        "ALGORITHM": os.environ['ALGORITHM'],
        "SECRET_KEY": os.environ['SECRET_KEY'],
        "ADMIN_TOKEN": os.environ['ADMIN_TOKEN'],
        "DEBUG": os.environ['DEBUG'],

        # Broker
        "REDIS_HOST": os.environ['REDIS_HOST'],
        "REDIS_PORT": os.environ['REDIS_PORT'],
        "REDIS_DB": os.environ['REDIS_DB'],
        "REDIS_PASSWORD": os.environ['REDIS_PASSWORD'],
    }

@pytest.fixture
def valid_token():
    payload = {
        "sub": "user_1",
        "exp": int(datetime.timestamp(datetime.now(tz=timezone.utc) + timedelta(minutes=5))),
    }
    return jwt.encode(
        payload,
        os.environ["SECRET_KEY"],
        algorithm=os.environ["ALGORITHM"],
    )


@pytest.fixture
def valid_token_decoded():
    return {
        "sub": "test@example.com",
        "id": 1,
        "exp": int(datetime.timestamp(datetime.now(tz=timezone.utc) + timedelta(minutes=5))),
    }


@pytest.fixture
async def avalid_token_decoded():
    yield {
        "sub": "user_1",
        "exp": int(datetime.timestamp(datetime.now(tz=timezone.utc) + timedelta(minutes=5))),
    }


@pytest.fixture
def expired_token():
    payload = {
        "sub": "user_1",
        "exp": int(datetime.timestamp(datetime.now(tz=timezone.utc) - timedelta(minutes=1))),
    }
    return jwt.encode(
        payload,
        os.environ["SECRET_KEY"],
        algorithm=os.environ["ALGORITHM"],
    )


@pytest.fixture
def expired_token_decoded():
    return {
        "sub": "user_1",
        "exp": int(datetime.timestamp(datetime.now(tz=timezone.utc) - timedelta(days=5))),
    }


@pytest.fixture
def form_data():
    return OAuth2PasswordRequestForm(
        username="test@example.com",
        password="password123",
        scope="",
        grant_type="password",
        client_id=None,
        client_secret=None,
    )


@pytest.fixture
def fake_user():
    return SimpleNamespace(
        id=1,
        email="test@example.com",
    )


@pytest.fixture
def token_pair():
    return "access-token", "refresh-token"


@pytest.fixture
def valid_user():
    mock_user = MagicMock(spec=UserModel)
    mock_user.hashed_password = "hashed_secret"
    mock_user.username = "user_1"
    mock_user.is_active = True
    mock_user.email = "test@example.com"
    return mock_user


@pytest.fixture
def inactive_user():
    mock_user = MagicMock(spec=UserModel)
    mock_user.hashed_password = "hashed_secret"
    mock_user.username = "user_1"
    mock_user.is_active = False
    mock_user.email = "test@example.com"
    return mock_user
