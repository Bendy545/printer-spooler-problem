class Task:
    def __init__(self, name, pages, priority=10):
        self.name = name
        self.pages = pages
        self.priority = priority

    def __str__(self):
        return f"Task {self.name}, pages={self.pages}, priority={self.priority}"
