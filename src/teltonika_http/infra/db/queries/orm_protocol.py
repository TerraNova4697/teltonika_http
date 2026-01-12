from typing import Protocol


class OrmProtocol(Protocol):
    @staticmethod
    def all():
        ...
        
    @staticmethod
    def get_first(session_factory, **kwargs):
        ...


    @staticmethod
    def create(session, **kwargs):
        ...

    @staticmethod
    def delete(entity):
        ...

    @staticmethod
    def update(entity):
        ...
