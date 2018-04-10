import time
import threading
from abc import abstractmethod
import logging


class BackgroundTask(threading.Thread):
    def __init__(self,
                 name="default_name",
                 timeout=float("inf"),
                 set_parent_progress=lambda p: None):
        threading.Thread.__init__(self, name="task_" + name)
        self.progress_value = 0
        self.progress_info_value = ""
        self.start_tick = time.time()
        self.timeout = timeout
        self.set_parent_progress = set_parent_progress
        self.terminated = False
        self.current_logger = logging.getLogger("Background task: " + self.name)

    @property
    def progress_info(self):
        return self.progress_info_value

    @progress_info.setter
    def progress_info(self, value):
        self.progress_info_value = value

    @property
    def progress(self):
        return self.progress_value

    @progress.setter
    def progress(self, value):
        self.progress_value = value
        self.set_parent_progress(value)

    def get_past_time(self):
        return time.time() - self.start_tick

    def should_be_killed(self):
        return self.get_past_time() >= self.timeout

    def get_progress(self):
        return self.progress

    def get_progress_info(self):
        return self.progress_info

    @abstractmethod
    def run(self): pass


class BackgroundTaskGroup(BackgroundTask):
    def __init__(self, task_list, weight_list=None, name="default_group_name", timeout=float("inf"),
                 set_parent_progress=lambda p: None):
        assert len(task_list) > 0, "No task in task list"
        BackgroundTask.__init__(
            self, name="group_" + name, timeout=timeout,
            set_parent_progress=set_parent_progress)

        if weight_list is None:
            weight_list = [1 for _ in range(len(task_list))]
        else:
            assert len(weight_list) == len(task_list)

        sum_weight = sum(weight_list)
        self.weight_list = [w * 100.0 / sum_weight for w in weight_list]
        self.task_list = task_list

    def set_progress(self, value):
        self.progress = value

    def run(self):
        processed = 0.0
        for index, task in enumerate(self.task_list):
            task_weight = self.weight_list[index]
            task.set_parent_progress = lambda value: self.set_progress(
                processed + value * task_weight / 100.0)
            task.run()
            processed += task_weight
        self.progress = 100.0
        self.terminated = True
