import logging

from fastapi import APIRouter, HTTPException, Request
from starlette import status

from src.teltonika_http.util.dependencies import db_dep, token_form_dep
from src.teltonika_http.util.dtos import TokenPairDto
from src.teltonika_http.services.auth import (
    AuthService, 
    NotValidatedException, 
    NotAuthorizedException,
    TokenExpiredException,
    token_refresh_form_dep
)


logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["auth"]
)


@router.post("/token", response_model=TokenPairDto)
async def token(request: Request, form_data: token_form_dep, db: db_dep):
    """
    Obtain token pair (access and refresh tokens)
    
    :param request: Description
    :type request: Request
    :param form_data: Description
    :type form_data: token_form_dep
    :param db: Description
    :type db: db_dep
    """
    client = request.client.host if request.client else "-"
    logger.info(f"CONNECT {request.method} {request.url.path} from={client}")
    logger.debug(
        f"REQUEST {request.method} {request.url} grant_type={getattr(form_data, 'grant_type', None)} "
        f"username={getattr(form_data, 'username', None)}"
    )

    if form_data.grant_type != "password":
        raise HTTPException(status_code=400, detail="Invalid grant type")
    result = AuthService.get_token(form_data, db)
    logger.info(f"Token issued for username={getattr(form_data, 'username', None)} status=200")  # ADDED
    return result


@router.post("/refresh", response_model=TokenPairDto)
async def refresh(
    request: Request,
    db: db_dep,
    # refresh_token: Annotated[str | None, Header()] = None,
    form_data: token_refresh_form_dep
):
    """
    Obtain a new access token using a refresh token
    
    :param request: Description
    :type request: Request
    :param db: Description
    :type db: db_dep
    :param form_data: Description
    :type form_data: token_refresh_form_dep
    """
    # if form_data.refresh_token is None:
    #     logger.warning("Missing refresh_token for /auth/refresh")
    #     raise HTTPException(detail="Invalid refresh token", status_code=status.HTTP_401_UNAUTHORIZED)

    return await AuthService.refresh(form_data.refresh_token, db)
