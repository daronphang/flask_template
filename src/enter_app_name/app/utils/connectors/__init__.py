import logging
from celery.utils.log import get_task_logger

from .database import db_decorator, create_db
from .requests import http_handler

logger = logging.getLogger(__name__)
celery_logger = get_task_logger(__name__)


def exponential_backoff(exc_to_check, logger: str, retries=3, delay=3, backoff=2):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            logger_map = {
                'DEFAULT': logger,
                'CELERY': celery_logger
            }

            retry, exp_delay = retries, delay
            while retry > 0:
                try:
                    return f(*args, **kwargs)
                except exc_to_check as e:
                    retry_msg = f'{e.message}. Retrying in {exp_delay} seconds... Retries left: {retry}'
                    logger_map[logger].warning(retry_msg)
                    time.sleep(exp_delay)
                    retry -= 1
                    exp_delay *= backoff
            return f(*args, **kwargs)
        return wrapper
    return decorator