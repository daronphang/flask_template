import logging
import pymssql as p
import psycopg2 as pg
import requests as r
import urllib3
from abc import ABC, abstractmethod
from functools import wraps
from operator import itemgetter
from celery.utils.log import get_task_logger

from ..error_handling import DatabaseError, InvalidField

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)
celery_logger = get_task_logger(__name__)


def db_decorator(f):
    # self._db is an instance of database session class
    def wrapper(self, *args, **kwargs):
        logger_map = {
            'DEFAULT': logger,
            'CELERY': celery_logger
        }

        with self._db as db:
            try:
                results = f(self, *args, **kwargs)
                db.conn.commit()
                return results
            except Exception as e:
                db.conn.rollback()
                logger_map[self.logger].error(e)
                raise DatabaseError(str(e))
    return wrapper


# DB connection factory method
def create_db(config: dict):
    if not config:
        return  # for unittesting

    db_type = config['db_type']

    if dbtype == 'MSSQL':
        host, username, password, port, as_dict = itemgetter(
            'host', 'username', 'password', 'port', 'as_dict')(config)
        db_session = MSSQLDBConnectionSession(host, username, password, port, as_dict)
    elif dbtype == 'PG':
        host, username, password, port = itemgetter(
            'host', 'username', 'password', 'port')(config)
        db_session = PGSQLConnectionSession(host, username, password, port)
    else:
        raise InvalidField(f'Unable to establish connection with db {db_type}')

    return db_session
   

class ContextManager(ABC):
    @abstractmethod
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.conn.close()
        if exc_type or exc_value:
            logger.error(exc_type)
            return False
        return True


class HttpConnectionSession(ContextManager):
    def __init__(self):
        self.conn = r.Session()
    
    def __enter__(self):
        return self.conn


class PGSQLConnectionSession(ContextManager):
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: str
    ):
        self.conn = pg.connect(
            host=host,
            user=username,
            password=password,
            port=port
        )
        self.cursor = self.conn.cursor(cursor_factory=pg.extras.RealDictCursor)


class MSSQLDBConnectionSession(ContextManager):
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: str,
        as_dict: bool
    ):
        self.conn = p.connect(
            host=host,
            user=username,
            password=password,
            port=port
        )
        self.as_dict = as_dict
        self.cursor = self.conn.cursor(as_dict=as_dict)
