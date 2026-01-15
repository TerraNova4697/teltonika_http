from abc import ABC
import logging

from src.teltonika_http.services.broker import BrokerService


class BaseService(ABC):
    def __init__(self, db_session, logger_name: str, broker = None):
        self.db = db_session
        self.broker: BrokerService = broker
        self.logger = logging.getLogger(logger_name)
    
    def _handle_error(self, e: Exception):
        """Общий метод обработки внутренних ошибок"""
        self.logger.error(f"Error occurred: {e}")
        raise e