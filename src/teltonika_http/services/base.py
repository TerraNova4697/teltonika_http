from abc import ABC
import logging


class BaseService(ABC):
    def __init__(self, db_session, logger_name: str):
        self.db = db_session
        self.logger = logging.getLogger(logger_name)
    
    def _handle_error(self, e: Exception):
        """Общий метод обработки внутренних ошибок"""
        self.logger.error(f"Error occurred: {e}")
        raise e