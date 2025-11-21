import threading
from models.task import Task
import random
import time

from spooler.task_list import TaskList


class UserException(Exception):
    pass

class User(threading.Thread):
    def __init__(self, username, task_list, number_of_tasks):
        threading.Thread.__init__(self)
        self.username = username
        self.number_of_tasks = number_of_tasks
        self.task_list = task_list

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        if not isinstance(value, str):
            raise UserException("username must be a string")
        self._username = value

    @property
    def task_list(self):
        return self._task_list

    @task_list.setter
    def task_list(self, value):
        if not isinstance(value, TaskList):
            raise UserException('task_list must be an instance of TaskList')
        self._task_list = value

    @property
    def number_of_tasks(self):
        return self._number_of_tasks

    @number_of_tasks.setter
    def number_of_tasks(self, value):
        if not isinstance(value, int):
            raise UserException('number_of_tasks must be an integer')
        self._number_of_tasks = value

    def run(self):
        for i in range(self.number_of_tasks):
            task_name = f"Doc-{self.username}-{i}"
            pages = random.randint(1, 5)
            priority = random.randint(1, 10)
            task = Task(name=task_name, pages=pages, priority=priority, user=self)
            self.task_list.append(task)
            print(f"[{self.username}] submitted {task_name}")
            time.sleep(random.random() * 2)
"""
    def print_file(self, task_list, name, pages, priority=1):
        task = Task(name=name, pages=pages, priority=priority, user=self)
        task_list.append(task)
        print(f"User {self.username} has submitted task {task.name}.")
"""



