from celery import Task
from flask import current_app
from celery.utils.log import get_task_logger
from enter_app_name.app import celery
from enter_app_name.app.utils import CeleryFailure, InvalidField
from .get_dpn_data import GetDPNDataTask
from .plot_weekly_spc_ooc import PlotWeeklySPCOOC
from .espec_monitoring import ESPECMonitoring


logger = get_task_logger(__name__)


class CustomCeleryBaseTask(Task):
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


@celery.task(bind=True)
def automated_task(self, taskname: str, userinfo: dict, payload: dict):
    if taskname == 'GET_DPN_DATA':
        concrete = GetDPNDataTask(userinfo, payload, taskname)
    elif taskname == 'PLOT_WEEKLY_SPC_OOC':
        concrete = PlotWeeklySPCOOC(userinfo, payload)
    elif taskname == 'ESPEC_MONITORING':
        concrete = ESPECMonitoring(userinfo, payload)
    else:
        raise InvalidField(f'{taskname} task does not exist')

    results = concrete.execute()
    return results