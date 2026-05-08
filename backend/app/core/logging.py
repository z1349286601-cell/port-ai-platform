import sys
from loguru import logger
from app.core.config import settings


def setup_logging():
    logger.remove()

    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[trace_id]: <36}</cyan> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG",
    )

    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[trace_id]: <36} | {name}:{function}:{line} - {message}",
        level="INFO",
        rotation="00:00",
        retention="7 days",
        encoding="utf-8",
    )

    return logger


def get_logger(name: str = __name__):
    return logger.bind(name=name, trace_id="")
