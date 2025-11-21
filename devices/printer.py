import threading
import time

from spooler.task_list import TaskList

class PrinterException(Exception):
    pass

class Printer(threading.Thread):
    def __init__(self, task_list, name="printer"):
        threading.Thread.__init__(self)

        self._name = None
        self.tasks = None
        self.running = True
        self.set_tasks(task_list)
        self.set_name(name)

    def set_name(self, name):
        if not isinstance(name, str):
            raise PrinterException("Printer name must be a string")
        self._name = name

    def set_tasks(self, tasks):
        if not isinstance(tasks, TaskList):
            raise PrinterException("Printer tasks must be a type of a TaskList")
        self.tasks = tasks

    def stop(self):
        self.running = False
        print("Finished printing")

    def run(self):
        while self.running:
            task = self.tasks.pop()
            print(f"PRINTING: {task.name}, pages={task.pages}, priority={task.priority} for user={task.user.username}")
            time.sleep(task.pages * 1)



