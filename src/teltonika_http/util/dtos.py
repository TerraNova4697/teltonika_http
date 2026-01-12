from pydantic import BaseModel, Field


class UserDto(BaseModel):
    username: str
    email: str


class CurrentUserDto(BaseModel):
    email: str
    id: int


class LoginUserDto(UserDto):
    username: str
    email: str
    grant_type: str = "password"


class AdminCreateUserDto(BaseModel):
    admin_token: str = Field(..., description="Admin token for authentication")
    username: str = Field(..., description="Username for the new user")
    password: str = Field(..., description="Password for the new user")
    email: str = Field(..., description="Email address of the new user")


class TokenPairDto(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class TransportDto(BaseModel):
    imei: str
    name: str
