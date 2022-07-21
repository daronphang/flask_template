import logging
import pymssql as p
import psycopg2 as pg
import snowflake.connector as s
from snowflake.connector import DictCursor
import requests as r
from abc import ABC, abstractmethod
from functools import wraps
from operator import itemgetter
from celery.utils.log import get_task_logger
from ..error_handlers import DBFailure, InvalidField


logger = logging.getLogger(__name__)
celery_logger = get_task_logger(__name__)


def db_request(f):
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
                db.cursor.close()
                return results
            except Exception as e:
                db.conn.rollback()
                logger_map[self.logger].error(e)
                raise DBFailure(str(e))
    return wrapper


# DB connection factory method
def init_db_session(config: dict):
    if not config:
        return  # for unittesting

    dbtype = config['DB_TYPE']

    if dbtype == 'MSSQL':
        host, username, password, port, as_dict = itemgetter(
            'HOST', 'USERNAME', 'PASSWORD', 'PORT', 'AS_DICT')(config)
        db_session = MSSQLConnSession(host, username, password, port, as_dict)
    elif dbtype == 'PG':
        host, username, password, port = itemgetter(
            'HOST', 'USERNAME', 'PASSWORD', 'PORT')(config)
        db_session = PGSQLConnSession(host, username, password, port)
    elif dbtype == 'SNOWFLAKE':
        username, password, account, region, warehouse = itemgetter(
            'USERNAME', 'PASSWORD', 'ACCOUNT', 'REGION', 'WAREHOUSE')(config)
        db_session = SnowflakeConnSession(username, password, account, region, warehouse)
    else:
        raise InvalidField(f'unable to initialize db session for {db_type}')

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


class PGSQLConnSession(ContextManager):
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


class MSSQLConnSession(ContextManager):
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


class SnowflakeConnSession(ContextManager):
    def __init__(
        self,
        username: str,
        password: str,
        account: str,
        region: str,
        warehouse: str
    ):
        self.conn = s.connect(
            user=username,
            password=password,
            account=account,
            region=region,
            warehouse=warehouse
        )
        self.cursor = self.conn.cursor(DictCursor)