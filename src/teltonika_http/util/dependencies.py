from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm

from src.teltonika_http.infra.db.db import sessionmaker, session


def __get_db():
    return session


db_dep = Annotated[sessionmaker, Depends(__get_db)]


token_form_dep = Annotated[OAuth2PasswordRequestForm, Depends()]


token_dep = Annotated[str, Depends()]
