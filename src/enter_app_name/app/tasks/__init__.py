from abc import ABC, abstractmethod
from .espec_monitoring import ESPECMonitoring
from .fdc_failures import *

class StandardTask(ABC):
    def pre_task(self):
        # logic to run before executing task
        pass

    @abstractmethod
    def execute(self):
        # execution of task itself
        pass