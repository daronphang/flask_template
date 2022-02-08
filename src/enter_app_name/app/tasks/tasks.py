from logging import error
from flask import current_app
from celery.utils.log import get_task_logger

from enter_app_name.app import celery
from enter_app_name.app.utils import CeleryFailure, HttpError, http_handler
from .operations import TestTask


logger = get_task_logger(__name__)


@celery.task(bind=True, base=TestTask)
def test_celery(self):
    logger.info('hello world!')
    raise CeleryFailure('testing celery failure')
    return {'status': 'finished'} 
