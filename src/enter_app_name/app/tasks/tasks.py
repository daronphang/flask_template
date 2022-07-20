import celery
from flask import current_app
from celery.utils.log import get_task_logger
from enter_app_name.app import celery
from enter_app_name.app.utils import CeleryFailure


logger = get_task_logger(__name__)


@celery.task(bind=True, base=celery.Task)
def testing_celery(self):
    logger.info('hello world!')
    raise CeleryFailure('testing celery failure')
    return {'status': 'testing completed'} 