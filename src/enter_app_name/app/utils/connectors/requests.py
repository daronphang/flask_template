import logging
import time
import requests as r
import urllib3
from functools import wraps
from abc import abstractmethod, ABC
from celery.utils.log import get_task_logger
from ..error_handling import HttpError

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)
celery_logger = get_task_logger(__name__)


def http_handler(config: dict):
    connection_map = {
        'GET': GetSession,
        'POST': PostSession,
    }

    logger_map = {
        'DEFAULT': logger,
        'CELERY': celery_logger
    }

    if config['method'] in connection_map:
        with connection_map[config['method']](config) as resp:
            pass
        if resp.status_code > 300:
            raise HttpError(config['error'])
        return resp
    else:
        logger_map(config['logger']).error('Invalid connection type passed to http_handler')
        raise HttpError('Invalid connection type passed.')


class HttpSession(ABC):
    def __init__(self, config: dict):
        self.config = config
        self.s = r.Session()
        self.s.trust_env = False

    @abstractmethod
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.s.close()
        if exc_type or exc_value:
            return False
        return True


class GetSession(HttpSession):
    def __enter__(self):
        return self.s.get(
            self.config['url'],
            params=self.config['params'],
            verify=self.config['verify']
        ) 


class PostSession(HttpSession):
    def __enter__(self):
        data = None
        payload = None
        if 'data' in self.config:
            data = self.config['data']
        if 'payload' in self.config:
            payload = self.config['payload']
        return self.s.post(
            self.config['url'],
            json=payload,
            data=data,
            verify=self.config['verify']
        )


