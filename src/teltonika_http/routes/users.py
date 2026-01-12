from fastapi import APIRouter
from src.teltonika_http.services.auth import current_user_dep


router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@router.get("/users/me")
async def read_users_me(user: current_user_dep):
    return user