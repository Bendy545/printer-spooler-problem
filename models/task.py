class TaskException(Exception):
    pass

class Task:
    def __init__(self, name, pages, priority, user):
        self.name = name
        self.pages = pages
        self.priority = priority
        self.user = user

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise TaskException('name must be a string')
        self._name = value

    @property
    def pages(self):
        return self._pages

    @pages.setter
    def pages(self, value):
        if not isinstance(value, int):
            raise TaskException('pages must be a integer')
        self._pages = value

    @property
    def priority(self):
        return self._priority

    @priority.setter
    def priority(self, value):
        if not isinstance(value, int):
            raise TaskException('priority must be an integer')
        self._priority = value

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, value):
        from users.user import User
        if not isinstance(value, User):
            raise TaskException('user must be a User')
        self._user = value

    def __str__(self):
        return f"Task {self.name}, pages={self.pages}, priority={self.priority} by user={self.user.username}"
