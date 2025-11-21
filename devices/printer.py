import threading
import time

from spooler.task_list import TaskList

class PrinterException(Exception):
    pass

class Printer(threading.Thread):
    def __init__(self, task_list, name="printer"):
        threading.Thread.__init__(self)

        self.name = name
        self.tasks = task_list
        self.running = True

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise PrinterException("Printer Name must be a string")
        self._name = value

    @property
    def tasks(self):
        return self._tasks

    @tasks.setter
    def tasks(self, value):
        if not isinstance(value, TaskList):
            raise PrinterException("Printer tasks must be a TaskList class")
        self._tasks = value

    def stop(self):
        self.running = False
        print("Finished printing")

    def run(self):
        while self.running:
            task = self.tasks.pop()
            print(f"PRINTING: {task.name}, pages={task.pages}, priority={task.priority} for user={task.user.username}")
            time.sleep(task.pages * 1)



