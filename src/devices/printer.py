import threading
import time

from src.spooler.task_list import TaskList

class PrinterException(Exception):
    pass

class Printer(threading.Thread):
    def __init__(self, task_list, name="printer"):
        """
        Represents a printer device that runs in its own thread.

        It continuously takes tasks from TaskList and prints them
        :param task_list: TaskList instance
        :param name: Name of the printer
        :raises PrinterException: If TaskList is not a TaskList or name is not a string
        """
        threading.Thread.__init__(self)

        self.name = name
        self.tasks = task_list
        self.running = True

    @property
    def name(self):
        """
        Get the name of the printer

        :return: Printer name
        """
        return self._name

    @name.setter
    def name(self, value):
        """
        Set the name of the printer

        :param value: Printer name
        :raises PrinterException: If value is not a string
        """
        if not isinstance(value, str):
            raise PrinterException("Printer Name must be a string")
        self._name = value

    @property
    def tasks(self):
        """
        Get the TaskList instance

        :return: TaskList instance
        """
        return self._tasks

    @tasks.setter
    def tasks(self, value):
        """
        Set the TaskList instance

        :param value: TaskList instance
        :raises PrinterException: If value is not a TaskList
        """
        if not isinstance(value, TaskList):
            raise PrinterException("Printer tasks must be a TaskList class")
        self._tasks = value

    def stop(self):
        """
        Stops the printer
        """
        self.running = False
        print("Finished printing")

    def run(self):
        """
        Main loop of the printer

        continuously fetches tasks from TaskList and prints them
        Each task takes 'task.pages' seconds to print
        """
        while self.running:
            task = self.tasks.pop()
            print(f"PRINTING: {task.name}, pages={task.pages}, priority={task.priority} for user={task.user.username}")
            time.sleep(task.pages * 1)



