import os
import logging
from celery.app.log import TaskFormatter
from celery.signals import after_setup_task_logger, after_setup_logger

from .app import celery, create_app

basedir = os.path.abspath(os.path.dirname(__file__))

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
app.app_context().push()

def setup_file_handler_logger(logger, formatter):
    logfile_handler = logging.FileHandler(
            os.path.join(basedir, f'CELERY_TEST.log')
        )
    logfile_handler.setFormatter(formatter)
    logfile_handler.setLevel(logging.INFO)
    logger.addHandler(logfile_handler)

# For celery global logger
@after_setup_logger.connect
def setup_global_logger(logger, *args, **kwargs):
    formatter = logging.Formatter(
        '[%(asctime)s: %(levelname)s in %(module)s] %(message)s'
    )
    setup_file_handler_logger(logger, formatter)
    

# For customizing celery task_logger
@after_setup_task_logger.connect
def setup_task_logger(logger, *args, **kwargs):
    formatter = TaskFormatter(
        '[%(asctime)s: %(task_name)s %(levelname)s in %(module)s][%(task_id)s] %(message)s'
    )
    setup_file_handler_logger(logger, formatter)