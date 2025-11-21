import threading
from models.task import Task


class TaskListException(Exception):
    pass

class Node:
    def __init__(self, task):
        """
        Defines the single task in the TaskList

        :param task: Task instance stored in this node
        """
        self.task = task
        self.prev = None
        self.next = None

class TaskList:
    def __init__(self, max_size=10):
        """
        Defines LinkedList queue of tasks ordered by priority.

        :param max_size: maximum number of tasks to print
        """
        self.tail = None
        self.head = None
        self.size = 0
        self.max_size = max_size
        self.lock = threading.Lock()
        self.not_empty = threading.Condition(self.lock)
        self.not_full = threading.Condition(self.lock)

    @property
    def max_size(self):
        """
        Get the maximum size of the TaskList

        :return: maximum size of the TaskList
        """
        return self._max_size

    @max_size.setter
    def max_size(self, value):
        """
        Set the maximum size of the TaskList

        :param value: The maximum size of the TaskList
        :raises TaskListException: If value is not a positive integer
        """
        if not isinstance(value, int):
            raise TaskListException('max_size must be an integer')
        if value < 1:
            raise TaskListException('max_size must be positive')
        self._max_size = value

    def append(self, task):
        """
        Add a new task to the queue based on its priority

        :param task: Task instance to add to the queue
        :raises TaskListException: If task is not a Task instance
        """

        if not isinstance(task, Task):
            raise TaskListException("task must be a Task")
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
                new_node.prev = current

                if current.next:
                    current.next.prev = new_node
                else:
                    self.tail = new_node

                current.next = new_node

            self.size += 1
            self.not_empty.notify()

    def pop(self):
        """
        Removes the first task in the queue
        Blocks if the queue is empty until a task is available

        :return: the first task in the queue
        """

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

    def __str__(self):
        """
        Return a string representation of the current tasks in the TaskList

        :return: String with all tasks in the queue
        """
        current = self.head
        result = "Current Tasks: \n"
        while current is not None:
            result += str(current.task) + "\n"
            current = current.next
        return result

    def __len__(self):
        """
        Return the number of tasks in the TaskList

        :return: Number of tasks in the TaskList
        """
        return self.size
