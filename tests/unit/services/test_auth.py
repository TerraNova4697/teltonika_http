from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import bcrypt
import jwt
import pytest
from fastapi import HTTPException

from src.teltonika_http.config import settings
from src.teltonika_http.services.auth import (
    AuthService, TokenExpiredException, NotValidatedException, REFRESH_TOKEN_EXPIRE_DAYS,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from src.teltonika_http.infra.db.queries import UserOrm
from src.teltonika_http.infra.db.models import UserModel
from src.teltonika_http.util.dtos import CurrentUserDto

################################################################
# Test AuthService.decode_token
################################################################
def test_decode_token_success(valid_token):
    decoded = AuthService.decode_token(valid_token)
    assert decoded["sub"] == "user_1"


def test_decode_token_expired(expired_token):
    with pytest.raises(TokenExpiredException):
        AuthService.decode_token(expired_token)


def test_decode_token_invalid():
    invalid_token = "this.is.not.a.jwt"

    with pytest.raises(NotValidatedException):
        AuthService.decode_token(invalid_token)


################################################################


################################################################
# Test AuthService.__refresh_token_valid
################################################################

def test_refresh_token_valid_true(valid_token_decoded):
    with patch.object(AuthService, "decode_token", return_value=valid_token_decoded):
        result = AuthService._AuthService__refresh_token_valid("dummy_token")
        assert result is True


def test_refresh_token_valid_false_expired(expired_token_decoded):
    with patch.object(AuthService, "decode_token", return_value=expired_token_decoded):
        result = AuthService._AuthService__refresh_token_valid("dummy_token")
        assert result is False


def test_refresh_token_invalid_token():

    with patch.object(AuthService, "decode_token", side_effect=NotValidatedException):
        with pytest.raises(NotValidatedException):
            AuthService._AuthService__refresh_token_valid("bad_token")

################################################################


################################################################
# Test AuthService.create_refresh_token
################################################################

def test_create_refresh_token_returns_string():
    payload = {"sub": "user_1"}

    token = AuthService.create_refresh_token(payload)

    assert isinstance(token, str)


def test_create_refresh_token_contains_payload_and_exp(environs):
    payload = {"sub": "user_1"}
    now = datetime.now(tz=timezone.utc)

    token = AuthService.create_refresh_token(payload)

    decoded = jwt.decode(token, environs["SECRET_KEY"], algorithms=[environs["ALGORITHM"]])

    assert decoded["sub"] == "user_1"
    assert "exp" in decoded

    # exp must be in future
    exp_dt = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
    assert exp_dt > now


def test_create_refresh_token_with_custom_expires_delta(environs):
    payload = {"sub": "user_1"}
    delta = timedelta(hours=2)
    now = datetime.now(tz=timezone.utc)

    token = AuthService.create_refresh_token(payload, expires_delta=delta)

    decoded = jwt.decode(token, environs['SECRET_KEY'], algorithms=[environs['ALGORITHM']])
    exp_dt = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)

    # check, if exp ≈ now + delta (consider small tolerance - 5 seconds)
    assert abs((exp_dt - (now + delta)).total_seconds()) < 5


def test_create_refresh_token_with_default_expire_days(environs):
    payload = {"sub": "user_1"}
    now = datetime.now(tz=timezone.utc)

    token = AuthService.create_refresh_token(payload)

    decoded = jwt.decode(token, environs['SECRET_KEY'], algorithms=[environs['ALGORITHM']])
    exp_dt = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)

    expected_exp = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    # consider small tolerance - 5 seconds
    assert abs((exp_dt - expected_exp).total_seconds()) < 5
################################################################

################################################################
# Test AuthService.create_access_token
################################################################

def test_create_access_token_returns_string():
    payload = {"sub": "user_1"}

    token = AuthService.create_access_token(payload)

    assert isinstance(token, str)


def test_create_access_token_contains_payload_and_exp(environs):
    payload = {"sub": "user_1"}
    now = datetime.now(tz=timezone.utc)

    token = AuthService.create_access_token(payload)

    decoded = jwt.decode(token, environs["SECRET_KEY"], algorithms=[environs["ALGORITHM"]])

    assert decoded["sub"] == "user_1"
    assert "exp" in decoded

    # exp must be in future
    exp_dt = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
    assert exp_dt > now


def test_create_access_token_with_custom_expires_delta(environs):
    payload = {"sub": "user_1"}
    delta = timedelta(hours=2)
    now = datetime.now(tz=timezone.utc)

    token = AuthService.create_access_token(payload, expires_delta=delta)

    decoded = jwt.decode(token, environs['SECRET_KEY'], algorithms=[environs['ALGORITHM']])
    exp_dt = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)

    # check, if exp ≈ now + delta (consider small tolerance - 5 seconds)
    assert abs((exp_dt - (now + delta)).total_seconds()) < 5


def test_create_access_token_with_default_expire_days(environs):
    payload = {"sub": "user_1"}
    now = datetime.now(tz=timezone.utc)

    token = AuthService.create_access_token(payload)

    decoded = jwt.decode(token, environs['SECRET_KEY'], algorithms=[environs['ALGORITHM']])
    exp_dt = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)

    expected_exp = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # consider small tolerance - 5 seconds
    assert abs((exp_dt - expected_exp).total_seconds()) < 5

################################################################

################################################################
# Test AuthService.verify_password
################################################################

def test_verify_password_correct():
    plain_password = "my_secret_password"
    # making hash
    hashed_password = bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()

    result = AuthService.verify_password(plain_password, hashed_password)
    assert result is True


def test_verify_password_incorrect():
    plain_password = "my_secret_password"
    wrong_password = "wrong_password"
    # making hash of the correct password
    hashed_password = bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()

    result = AuthService.verify_password(wrong_password, hashed_password)
    assert result is False


def test_verify_password_empty():
    plain_password = ""
    hashed_password = bcrypt.hashpw("".encode(), bcrypt.gensalt()).decode()

    result = AuthService.verify_password(plain_password, hashed_password)
    assert result is True


def test_verify_password_non_string_input():
    plain_password = ""
    hashed_password = bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()

    # checking empty string doesn't break logic
    result = AuthService.verify_password(plain_password, hashed_password)
    assert result is True

################################################################


################################################################
# Test AuthService.hash_password
################################################################

def test_hash_password_returns_string():
    password = "my_secret_password"
    hashed = AuthService.hash_password(password)
    assert isinstance(hashed, str)
    assert len(hashed) > 0


def test_hash_password_can_be_verified():
    password = "my_secret_password"
    hashed = AuthService.hash_password(password)

    # Checking with verify_password
    assert AuthService.verify_password(password, hashed) is True


def test_hash_password_generates_unique_hashes():
    password = "my_secret_password"
    hashed1 = AuthService.hash_password(password)
    hashed2 = AuthService.hash_password(password)

    # Hashes must be different
    assert hashed1 != hashed2

    # Both hashes validated
    assert AuthService.verify_password(password, hashed1) is True
    assert AuthService.verify_password(password, hashed2) is True
################################################################


################################################################
# Test AuthService.authenticate_user
################################################################

def test_authenticate_user_success():
    username = "testuser"
    password = "secret"

    # mock user
    mock_user = MagicMock(spec=UserModel)
    mock_user.hashed_password = "hashed_secret"
    mock_user.username = "testuser"

    with patch.object(UserOrm, "get_first", return_value=mock_user) as mock_get, \
         patch.object(AuthService, "verify_password", return_value=True) as mock_verify:
        result = AuthService.authenticate_user(username, password, db="fake_db")

        # chekc result
        assert result == mock_user

        # check calling methods
        mock_get.assert_called_once_with(session_factory="fake_db", username=username)
        mock_verify.assert_called_once_with(password, mock_user.hashed_password)


def test_authenticate_user_wrong_password():
    username = "testuser"
    password = "wrong"

    mock_user = MagicMock(spec=UserModel)
    mock_user.hashed_password = "hashed_secret"

    with patch.object(UserOrm, "get_first", return_value=mock_user), \
         patch.object(AuthService, "verify_password", return_value=False):
        result = AuthService.authenticate_user(username, password, db="fake_db")
        assert result is False


def test_authenticate_user_user_not_found():
    username = "missing"
    password = "any"

    with patch.object(UserOrm, "get_first", return_value=None):
        result = AuthService.authenticate_user(username, password, db="fake_db")
        assert result is False

################################################################


################################################################
# Test AuthService.get_token
################################################################

def test_get_token_success(form_data, fake_user):
    db = object()

    toker_pair = ("access-token", "refresh-token")

    with patch.object(AuthService, "authenticate_user", return_value=fake_user), \
        patch.object(AuthService, "_AuthService__create_token_pair", return_value=toker_pair):

        result = AuthService.get_token(form_data, db)

        assert result == {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "token_type": "Bearer",
        }


def test_get_token_invalid_user(form_data):
    db = object()

    with patch.object(AuthService, "authenticate_user", return_value=False), \
        pytest.raises(NotValidatedException):
        AuthService.get_token(form_data, db)

################################################################


################################################################
# Test AuthService.create_token_pair
################################################################

def test_create_token_pair(token_pair):
    email = "test@example.com"
    user_id = 123

    access_token, refresh_token = token_pair

    with patch.object(AuthService, "create_access_token", return_value=access_token), \
        patch.object(AuthService, "create_refresh_token", return_value=refresh_token):

        result = AuthService._AuthService__create_token_pair(
            email=email,
            id=user_id,
        )

        assert isinstance(result, tuple)
        assert len(result) == 2

        access, refresh = result

        assert access == "access-token"
        assert refresh == "refresh-token"

################################################################

################################################################
# Test AuthService.get_current_user
################################################################

@pytest.mark.asyncio
async def test_get_current_user_success(valid_token_decoded, valid_user):
    token = "valid-token"
    db = object()

    with patch.object(AuthService, "decode_token", return_value=valid_token_decoded), \
        patch.object(UserOrm, "get_first", return_value=valid_user):

        result = await AuthService.get_current_user(token, db)

        assert isinstance(result, CurrentUserDto)
        assert result.email == "test@example.com"
        assert result.id == 1


@pytest.mark.asyncio
async def test_get_current_user_missing_claims():
    token = "invalid-token"
    db = object()

    with patch.object(AuthService, "decode_token", return_value={"sub": None, "id": None}):
        with pytest.raises(NotValidatedException):
            await AuthService.get_current_user(token, db)


@pytest.mark.asyncio
async def test_get_current_user_user_not_found(valid_token_decoded):
    token = "valid-token"
    db = object()

    with patch.object(AuthService, "decode_token", return_value=valid_token_decoded), \
        patch.object(UserOrm, "get_first", return_value=None):
        with pytest.raises(HTTPException) as exc:
            await AuthService.get_current_user(token, db)

    assert exc.value.detail == "User not found"
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_current_user_inactive_user(valid_token_decoded, inactive_user):
    token = "valid-token"
    db = object()

    with patch.object(AuthService, "decode_token", return_value=valid_token_decoded), \
        patch.object(UserOrm, "get_first", return_value=inactive_user):
        with pytest.raises(HTTPException) as exc:
            await AuthService.get_current_user(token, db)

    assert exc.value.detail == "User inactive"
    assert exc.value.status_code == 400

################################################################


################################################################
# Test AuthService.refresh
################################################################

@pytest.mark.asyncio
async def test_refresh_success(valid_token_decoded, token_pair):
    refresh_token = "valid_refresh_token"

    with patch.object(AuthService, "_AuthService__refresh_token_valid", return_value=True), \
        patch.object(AuthService, "decode_token", return_value=valid_token_decoded), \
        patch.object(AuthService, "_AuthService__create_token_pair", return_value=token_pair):

        result = await AuthService.refresh(refresh_token)

        assert result == {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
        }


@pytest.mark.asyncio
async def test_refresh_invalid_token():
    refresh_token = "expired_refresh_token"

    with patch.object(AuthService, "_AuthService__refresh_token_valid", return_value=False):
        with pytest.raises(TokenExpiredException):
            await AuthService.refresh(refresh_token)


@pytest.mark.asyncio
async def test_refresh_decode_returns_none():
    refresh_token = "valid_but_empty_payload"
    with patch.object(AuthService, "_AuthService__refresh_token_valid", return_value=True), \
        patch.object(AuthService, "decode_token", return_value=None):
        with pytest.raises(TokenExpiredException):
            await AuthService.refresh(refresh_token)
################################################################
