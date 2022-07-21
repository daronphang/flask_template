import logging
import os
from flask import g, request, has_app_context, has_request_context
from dotenv import load_dotenv
from datetime import datetime
from .logger_config import init_logger, CustomJSONFormatter, RequestFormatter


load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))


class CeleryConfig:
    # redis :// [[username :] password@] host [: port] [/ database]
    broker_url = os.getenv("REDIS_URI")
    backend_result = os.getenv("CELERY_BACKEND")


class Config:
    BASEDIR = basedir
    PROJECT_NAME = 'Your-App-Name'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'R4nd0MS3cret'
    MAIL_SERVER = None
    MAIL_PORT = None
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = False
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    
    # SQLSERVER = {
    #     'HOST': os.environ.get('SQLSERVER'),
    #     'USERNAME': os.environ.get('SQLUSERNAME'),
    #     'PASSWORD': os.environ.get('SQLPASSWORD'),
    #     'PORT': os.environ.get('SQLPORT'),
    #     'DB_TYPE': 'MSSQL',
    #     'AS_DICT': True
    # }

    TSMSSPROD06 = {
        'HOST': os.environ.get('TSMSSPROD06SERVER'),
        'USERNAME': os.environ.get('TSMSSPROD06USERNAME'),
        'PASSWORD': os.environ.get('TSMSSPROD06PASSWORD'),
        'PORT': os.environ.get('TSMSSPROD06PORT'),
        'DB_TYPE': 'MSSQL',
        'AS_DICT': True
    }

    SNOWFLAKE = {
        'ACCOUNT': os.environ.get('SNOWFLAKEACCOUNT'),
        'USERNAME': os.environ.get('SNOWFLAKEUSERNAME'),
        'PASSWORD': os.environ.get('SNOWFLAKEPASSWORD'),
        'ROLE': os.environ.get('SNOWFLAKEROLE'),
        'REGION': os.environ.get('SNOWFLAKEREGION'),
        'WAREHOUSE': os.environ.get('SNOWFLAKEWAREHOUSE'),
        'DB_TYPE': 'SNOWFLAKE',
    }

    
    @staticmethod
    def init_app(app):
        # to customize configuration
        pass


class TestingConfig(Config):
    TESTING = True

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        init_logger('TESTING', CustomJSONFormatter, os.path.join(cls.BASEDIR, cls.PROJECT_NAME))


class ProductionConfig(Config):
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        init_logger('PRODUCTION', CustomJSONFormatter, os.path.join(cls.BASEDIR, cls.PROJECT_NAME))


config = {
    'TESTING': TestingConfig,
    'PRODUCTION': ProductionConfig,
    'DEFAULT': TestingConfig
}
