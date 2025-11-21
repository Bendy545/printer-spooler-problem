import threading
from src.models.task import Task
import random
import time

from src.spooler.task_list import TaskList


class UserException(Exception):
    pass

class User(threading.Thread):
    def __init__(self, username, task_list, number_of_tasks):
        """
        Represents a user submitting print tasks to a TaskList

        :param username: Name of the user
        :param task_list: TaskList instance to which tasks will be submitted
        :param number_of_tasks: Number of the tasks the user will submit
        :raises UserException: If any parameter is not of the expected type
        """
        threading.Thread.__init__(self)
        self.username = username
        self.number_of_tasks = number_of_tasks
        self.task_list = task_list

    @property
    def username(self):
        """
        Get the username of the user

        :return: username of the user
        """
        return self._username

    @username.setter
    def username(self, value):
        """
        Set the username of the user

        :param value: username of the user
        :raises UserException: If value is not a string
        """
        if not isinstance(value, str):
            raise UserException("username must be a string")
        self._username = value

    @property
    def task_list(self):
        """
        Get the task list of the user

        :return: the task list of the user
        """
        return self._task_list

    @task_list.setter
    def task_list(self, value):
        """
        Set the task list of the user

        :param value: the task list of the user
        :raises UserException: If value is not an instance os TaskList
        """
        if not isinstance(value, TaskList):
            raise UserException('task_list must be an instance of TaskList')
        self._task_list = value

    @property
    def number_of_tasks(self):
        """
        Get the number of tasks the user can submit

        :return: the number of tasks the user can submit
        """
        return self._number_of_tasks

    @number_of_tasks.setter
    def number_of_tasks(self, value):
        """
        Set the number of tasks the user can submit

        :param value: the number of tasks the user can submit
        :raises UserException: If value is not an integer
        """
        if not isinstance(value, int):
            raise UserException('number_of_tasks must be an integer')
        self._number_of_tasks = value

    def run(self):
        """
        Main thread loop

        Submits tasks to the assigned TaskList.
        Each task has a random number of pages and random priority.
        Sleeps a random amount of time between submissions.
        """
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



