import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated
from typing_extensions import Doc

import bcrypt
import jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException
from fastapi.param_functions import Form

from src.teltonika_http.infra.db.models import UserModel
from src.teltonika_http.util.dependencies import db_dep
from src.teltonika_http.infra.db.queries import UserOrm
from src.teltonika_http.util.dtos import UserDto, CurrentUserDto
from src.teltonika_http import config
from src.teltonika_http.util.exceptions import AppError

logger = logging.getLogger(__name__)

ALGORITHM = config.settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
oauth2_dep = Annotated[str, Depends(oauth2_scheme)]


class OAuth2RefreshTokenRequestForm:

    def __init__(
        self,
        *,
        refresh_token: Annotated[
            str,
            Form(
                alias="refresh_token",
                description="Use refresh_token to obtain new access token.",
            ),
            Doc(
                """
                Use refresh_token to obtain new access token.
                """
            ),
        ]
    ):
        self.refresh_token = refresh_token


token_refresh_form_dep = Annotated[OAuth2RefreshTokenRequestForm, Depends()]


class NotAuthenticatedException(AppError):
    def __init__(
            self, 
            code: str = "NOT_AUTHENTICATED_ERROR", 
            message: str = "Could not authenticate", 
            status_code: int = 401
        ):
        self.code = code
        self.message = message
        self.status_code = status_code


class NotValidatedException(AppError):
    def __init__(
            self, 
            code: str = "NOT_VALIDATED_ERROR", 
            message: str = "Could not validate token", 
            status_code: int = 401
        ):
        self.code = code
        self.message = message
        self.status_code = status_code


class NotAuthorizedException(AppError):
    def __init__(
            self, 
            code: str = "NOT_AUTHORIZED_ERROR", 
            message: str = "Not enough permissions", 
            status_code: int = 403
        ):
        self.code = code
        self.message = message
        self.status_code = status_code


class TokenExpiredException(AppError):
    def __init__(
            self, 
            code: str = "TOKEN_EXPIRED_ERROR", 
            message: str = "Token expired", 
            status_code: int = 401
        ):
        self.code = code
        self.message = message
        self.status_code = status_code


class AuthService:

    @staticmethod
    async def refresh(refresh_token: str, db: db_dep) -> dict:
        
        # Логируем факт операции, без самого токена
        logger.info(f"Refreshing access token using refresh token: {refresh_token}")

        if not AuthService.__refresh_token_valid(refresh_token):
            raise TokenExpiredException

        if decoded_refresh_token := AuthService.decode_token(refresh_token):
            print(decoded_refresh_token)
            access_token, new_refresh = AuthService.__create_token_pair(
                db,
                email=decoded_refresh_token["sub"],
                id=decoded_refresh_token["id"],
            )
            logger.info("Access token refreshed successfully")
            return {
                "access_token": access_token,
                "refresh_token": new_refresh,
            }
        else:
            logger.warning("Refresh token expired")
            raise TokenExpiredException()


    @staticmethod
    async def get_current_user(token: oauth2_dep, db: db_dep) -> UserDto:
        logger.debug("Decoding access token")
        payload = AuthService.decode_token(token)
        email: str = payload.get('sub')
        user_id: int = payload.get('id')
        if not email or not user_id:
            logger.warning("Access token payload is missing required claims (sub/id)")
            raise NotValidatedException()
        user = UserOrm().get_first(db, email=email, id=user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return CurrentUserDto(email=email, id=user_id)

    @staticmethod
    def __create_token_pair(db: db_dep, **kwargs):
        logger.debug(f"Creating token pair for user_id={kwargs.get('id')} email={kwargs.get('email')}")
        access_token = AuthService.create_access_token(
            {"sub": kwargs['email'], "id": kwargs['id']},
            timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = AuthService.create_refresh_token(
            {"sub": kwargs['email'], "id": kwargs['id']},
            db,
            timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        logger.info("Token pair created")
        return access_token, refresh_token

    @staticmethod
    def get_token(form_data: OAuth2PasswordRequestForm, db: db_dep) -> dict:
        logger.info(f"Issuing token via password grant for username={form_data.username}")
        user = AuthService.authenticate_user(form_data.username, form_data.password, db)
        if not user:
            logger.warning(f"Could not validate user: username={form_data.username}")
            raise NotValidatedException()

        access_token, refresh_token = AuthService.__create_token_pair(db, email=user.email, id=user.id)
        logger.info(f"Token issued for username={form_data.username}")
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "Bearer"}

    @staticmethod
    def authenticate_user(username: str, password: str, db) -> bool | UserModel:
        logger.debug(f"Authenticating username={username}")
        user = UserOrm().get_first(session_factory=db, username=username)
        if not user:
            logger.warning(f"User not found: {username}")
            return False
        if not AuthService.verify_password(password, user.hashed_password):
            logger.warning(f"Invalid password for username={username}")
            return False
        logger.info(f"User authenticated: {username}")
        return user

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(str.encode(password), bcrypt.gensalt()).decode(encoding="utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(str.encode(plain_password), str.encode(hashed_password))

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        expire = datetime.now(tz=timezone.utc) + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, config.settings.SECRET_KEY, algorithm=ALGORITHM)
        logger.debug("Access token created")
        return token

    @staticmethod
    def create_refresh_token(data: dict, db, expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        expire = datetime.now(tz=timezone.utc) + (expires_delta if expires_delta else timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
        to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, config.settings.SECRET_KEY, algorithm=ALGORITHM)
        logger.debug("Refresh token created and stored")
        return token

    @staticmethod
    def __refresh_token_valid(refresh_token: str) -> bool:
        decoded = AuthService.decode_token(refresh_token)
        now_utc = datetime.now(tz=timezone.utc)
        exp = decoded["exp"]
        exp_dt = datetime.fromtimestamp(exp)
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
        valid = now_utc < exp_dt
        logger.debug(f"Refresh token valid={valid} (now={now_utc}, exp={exp})")
        if valid:
            return valid
        return False

    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            return jwt.decode(token, config.settings.SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            logger.warning("Access token expired")
            raise TokenExpiredException()
        except jwt.InvalidTokenError:
            logger.warning("Invalid access token")
            raise NotValidatedException()



current_user_dep = Annotated[CurrentUserDto, Depends(AuthService.get_current_user)]
