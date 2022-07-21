from celery import Task
from flask import current_app
from celery.utils.log import get_task_logger
from enter_app_name.app import celery
from enter_app_name.app.utils import CeleryFailure


logger = get_task_logger(__name__)


class CustomBaseTask(Task):
    def before_start(self, task_id, args, kwargs):
        pass

    def on_success(self, retval, task_id, args, kwargs):
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        pass


@celery.task(bind=True)
def testing_celery(self):
    logger.info('hello world!')
    # raise CeleryFailure('testing celery failure')
    return {'status': 'testing completed'} 