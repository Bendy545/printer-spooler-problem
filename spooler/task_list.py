import threading
from models.task import Task

from devices.printer import PrinterException


class TaskListException(Exception):
    pass

class Node:
    def __init__(self, task):
        self.task = task
        self.prev = None
        self.next = None

class TaskList:
    def __init__(self, max_size=10):
        self.tail = None
        self.head = None
        self.size = 0
        self.max_size = max_size
        self.lock = threading.Lock()
        self.not_empty = threading.Condition(self.lock)
        self.not_full = threading.Condition(self.lock)

    def append(self, task):
        if not isinstance(task, Task):
            raise PrinterException("task must be a Task")
        new_node = Node(task)
        with self.not_full:
            while self.size >= self.max_size:
                print(f"TaskList is full {self.size}/{self.max_size}")
                self.not_full.wait()

            if self.head is None:
                self.head = new_node
                self.tail = new_node
            elif task.priority < self.head.task.priority:
                new_node.next = self.head
                self.head.prev = new_node
                self.head = new_node
            else:
                current = self.head
                while current.next and task.priority >= current.next.task.priority:
                    current = current.next

                new_node.next = current.next
                current.prev = current
                current.next = new_node
                if new_node.next:
                    new_node.next.prev = new_node
                else:
                    self.tail = new_node

            self.size += 1
            self.not_empty.notify()

    def pop(self):
        with self.not_empty:
            while self.size == 0:
                print(f"TaskList is empty {self.size}/{self.max_size} waiting.....")
                self.not_empty.wait()

            node = self.head
            self.head = node.next
            if self.head:
                self.head.prev = None
            else:
                self.head = None

            self.size -= 1
            self.not_full.notify()
            return node.task
