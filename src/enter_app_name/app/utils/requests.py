import logging
import requests as r
import urllib3
from functools import wraps
from abc import abstractmethod, ABC
from celery.utils.log import get_task_logger
from .error_handlers import HTTPFailure

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)
celery_logger = get_task_logger(__name__)


def init_http_session(config: dict):
    connection_map = {
        'GET': GetSession,
        'POST': PostSession,
    }

    logger_map = {
        'DEFAULT': logger,
        'CELERY': celery_logger
    }

    if config['METHOD'] in connection_map:
        with connection_map[config['METHOD']](config) as resp:
            pass
        if resp.status_code > 300:
            raise HTTPFailure(config['ERROR'])
        return resp
    else:
        logger_map(config['LOGGER']).error('invalid http request')
        raise HTTPFailure('invalid http request')


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
            self.config['URL'],
            params=self.config['PARAMS'],
            verify=self.config['VERIFY']
        ) 


class PostSession(HttpSession):
    def __enter__(self):
        data = None
        payload = None
        if 'DATA' in self.config:
            data = self.config['DATA']
        if 'PAYLOAD' in self.config:
            payload = self.config['PAYLOAD']
        return self.s.post(
            self.config['URL'],
            json=payload,
            data=data,
            verify=self.config['VERIFY']
        )


