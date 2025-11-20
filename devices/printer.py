from spooler.task_list import TaskList

class PrinterException(Exception):
    pass

class Printer:
    def __init__(self, size,name="printer"):
        self.size = size
        self.name = name
        self.tasks = TaskList(size)

    @property
    def name(self):
        return self.name

    @property
    def size(self):
        return self.size

    @size.setter
    def size(self, value):
        if not isinstance(value, int):
            raise PrinterException("size must be an integer")
        if value < 1:
            raise PrinterException("size must be positive")
        self.size = value

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise PrinterException("name must be a string")
        self.name = value



