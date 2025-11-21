class TaskException(Exception):
    pass

class Task:
    def __init__(self, name, pages, priority, user):
        self.name = None
        self.pages = None
        self.priority = None
        self.user = None
        self.set_name(name)
        self.set_pages(pages)
        self.set_priority(priority)
        self.set_user(user)

    def set_name(self,name):
        if not isinstance(name, str):
            raise TaskException(f"Task name must be a string")
        self.name = name

    def set_pages(self, pages):
        if not isinstance(pages, int):
            raise TaskException(f"Pages must be a integer")
        self.pages = pages

    def set_priority(self, priority):
        if not isinstance(priority, int):
            raise TaskException(f"Priority must be a integer")
        self.priority = priority

    def set_user(self, user):
        from users.user import User
        if not isinstance(user, User):
            raise TaskException(f"User must be a User")
        self.user = user

    def __str__(self):
        return f"Task {self.name}, pages={self.pages}, priority={self.priority} by user={self.user.username}"
