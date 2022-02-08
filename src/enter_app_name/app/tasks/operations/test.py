from celery import Task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


class TestTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(exc.message)
