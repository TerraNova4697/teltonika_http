from .base_orm import BaseOrm
from ..models import Transport


class TransportOrm(BaseOrm):

    def __init__(self):
        super().__init__(Transport)
