from abc import ABC, abstractmethod


class StandardTask(ABC):
    @abstractmethod
    def pre_task(self):
        # logic to run before executing task
        pass

    @abstractmethod
    def execute(self):
        # execution of task itself
        pass