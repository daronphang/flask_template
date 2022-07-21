import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from celery.app.log import TaskFormatter
from celery._state import get_current_task
from celery.signals import after_setup_task_logger, after_setup_logger
from pythonjsonlogger import jsonlogger
from .app import celery, create_app

basedir = os.path.abspath(os.path.dirname(__file__))

app = create_app(os.getenv('FLASK_CONFIG') or 'DEFAULT')
app.app_context().push()


class CustomJSONCeleryFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJSONCeleryFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
     
        task = get_current_task()
        if task and task.request:
            log_record['task_id'] = task.request.id
            log_record['task_name'] = task.name


def setup_file_handler_logger(logger, formatter):
    logfile_handler = RotatingFileHandler(
        os.path.join(basedir, f'CELERY-TEST.log'),
        maxBytes=1024000,
        backupCount=10,
        encoding='UTF-8'
    )
    logfile_handler.setFormatter(formatter)
    logfile_handler.setLevel(logging.INFO)
    logger.addHandler(logfile_handler)

# For celery global logger
@after_setup_logger.connect
def setup_global_logger(logger, *args, **kwargs):
    formatter = CustomJSONCeleryFormatter(
            '%(timestamp)s %(levelname)s %(module)s %(message)s',
        )
    setup_file_handler_logger(logger, formatter)
    

# For customizing celery task_logger
@after_setup_task_logger.connect
def setup_task_logger(logger, *args, **kwargs):
    formatter = CustomJSONCeleryFormatter(
        '%(timestamp)s %(task_name)s %(task_id)s %(levelname)s %(module)s %(message)s'
    )
    setup_file_handler_logger(logger, formatter)