import threading

import time


class LastOpMonitor(threading.Thread):
    def __init__(self, thread_list, print_period=1):
        super(LastOpMonitor, self).__init__()
        self.thread_list = thread_list
        self.print_period = print_period

    def run(self):
        while True:
            time.sleep(self.print_period)
            print("Current time:%f" % time.time())
            for thread in self.thread_list:
                print("Thread:%s\tLastOp:%s" % (thread.name, thread.last_op))
