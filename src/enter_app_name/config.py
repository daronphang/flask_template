from flask import g, request
from dotenv import load_dotenv
import logging
import os

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))


class RequestFormatter(logging.Formatter):
    def format(self, record):
        record.context = g.context
        record.username = g.username if hasattr(g, 'username') else request.remote_addr  # noqa
        return super().format(record)


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

    SQLALCHEMY_DATABASE_URI = os.getenv("PG_DATABASE_URI")
    
    SQLSERVER = {
        'host': os.environ.get('SQLSERVER'),
        'username': os.environ.get('SQLUSERNAME'),
        'password': os.environ.get('SQLPASSWORD'),
        'port': os.environ.get('SQLPORT'),
        'db_type': 'MSSQL',
        'as_dict': True
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

        import logging
        from flask.logging import default_handler

        app.logger.removeHandler(default_handler)
        app.logger.setLevel(logging.DEBUG)
        formatter = RequestFormatter(
            '[%(asctime)s] %(username)s payload %(context)s '
            '%(levelname)s in %(module)s: %(message)s'
        )
        logfile_handler = logging.FileHandler(
            os.path.join(cls.BASEDIR, f'{cls.PROJECT_NAME}-TESTING.log')
        )
        logfile_handler.setFormatter(formatter)
        logfile_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(logfile_handler)


class ProductionConfig(Config):
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        import logging
        from flask.logging import default_handler

        app.logger.removeHandler(default_handler)
        app.logger.setLevel(logging.INFO)
        formatter = RequestFormatter(
            '[%(asctime)s] %(username)s payload %(context)s '
            '%(levelname)s in %(module)s: %(message)s'
        )
        logfile_handler = logging.RotatingFileHandler(
            os.path.join(cls.BASEDIR, f'{cls.PROJECT_NAME}-PROD.log'),
            maxBytes=1024000,
            backupCount=10,
            encoding='UTF-8'
        )
        logfile_handler.setFormatter(formatter)
        logfile_handler.setLevel(logging.INFO)
        app.logger.addHandler(logfile_handler)


config = {
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': TestingConfig
}
