import logging
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path


logger = logging.getLogger()


def setup_logger(base_path: str, log_level: int = logging.INFO):
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(base_path, 'logs', 'teltonika.log'), 
        when="midnight", 
        backupCount=31, 
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)s - %(message)s",
    )
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [file_handler, ]

class Settings():
    BASE_PATH = Path(__file__).parent.parent.parent

    # DATABASE
    POSTGRES_HOST = "postgres"
    POSTGRES_USER = os.environ["POSTGRES_USER"]
    POSTGRES_DB = os.environ["POSTGRES_DB"]
    POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]

    PORT = 8000
    HOST = "0.0.0.0"
    BACKLOG = 100
    DEBUG = os.environ["DEBUG"]
    LOG_LEVEL = 10 if DEBUG else 20
    ALGORITHM = os.environ["ALGORITHM"]
    SECRET_KEY = os.environ["SECRET_KEY"]
    ADMIN_TOKEN = os.environ["ADMIN_TOKEN"]

    REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
    REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
    REDIS_DB = os.environ.get("REDIS_DB", "0")
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', "supersecretpassword")

    @property
    def redis_url(self):
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = Settings()


def initial_setup():
    setup_logger(settings.BASE_PATH, settings.LOG_LEVEL)
