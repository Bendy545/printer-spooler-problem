import threading
from models.task import Task
import random
import time

class UserException(Exception):
    pass

class User(threading.Thread):
    def __init__(self, username, task_list, number_of_tasks):
        threading.Thread.__init__(self)
        self.username = None
        self.number_of_tasks = None
        self.task_list = task_list
        self.set_username(username)
        self.set_number_of_tasks(number_of_tasks)

    def set_number_of_tasks(self, number_of_tasks):
        if not isinstance(number_of_tasks, int):
            raise UserException("number_of_tasks must be an integer")
        self.number_of_tasks = number_of_tasks

    def set_username(self, username):
        if not isinstance(username, str):
            raise UserException("username must be a string")
        self.username = username

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



