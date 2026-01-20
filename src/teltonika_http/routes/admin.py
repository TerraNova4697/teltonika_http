import logging

from fastapi import APIRouter, HTTPException, Request
from starlette import status

from src.teltonika_http.util.dependencies import db_dep
from src.teltonika_http.util.dtos import LoginUserDto, AdminCreateUserDto
from src.teltonika_http.services.auth import AuthService
from src.teltonika_http.infra.db.queries import UserOrm
from src.teltonika_http import config

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)


@router.post("/create-user", response_model=LoginUserDto, include_in_schema=config.settings.DEBUG)
async def create_user(request: Request, body: AdminCreateUserDto, session: db_dep):
    client = request.client.host if request.client else "-"
    logger.info(f"CONNECT {request.method} {request.url.path} from={client} username={body.username}")
    logger.debug(
        f"REQUEST {request.method} {request.url} body={{'username':'{body.username}', 'email':'{body.email}', 'admin_token':'***'}}"
    )

    if body.admin_token != config.settings.ADMIN_TOKEN:
        logger.warning(f"Invalid admin_token for create-user from={client} username={body.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to perform this operation!"
        )

    UserOrm().create(
        session,
        username=body.username,
        hashed_password=AuthService.hash_password(body.password),
        email=body.email
    )

    logger.info(f"User created username={body.username} status=200")
    return LoginUserDto(
        username=body.username,
        email=body.email
    )
