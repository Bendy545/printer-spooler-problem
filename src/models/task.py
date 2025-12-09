class TaskException(Exception):
    pass

class Task:
    def __init__(self, name, pages, priority, username, file_path=None):
        """
        Represents a print job submitted by the user

        :param name: Name of the task/document
        :param pages: Number of pages to print
        :param priority: Priority of the task (lower number = higher priority)
        :param username: User who submitted the task
        :raises TaskException: If parameters are not of the expected type
        """
        self.name = name
        self.pages = pages
        self.priority = priority
        self.username = username
        self.file_path = file_path

    @property
    def name(self):
        """
        Get the name of the task

        :return: name of the task
        """
        return self._name

    @name.setter
    def name(self, value):
        """
        Set the name of the task
        :param value: name of the task
        :raises TaskException: If value is not a string
        """
        if not isinstance(value, str):
            raise TaskException('name must be a string')
        self._name = value

    @property
    def pages(self):
        """
        Get the number of pages to print

        :return: number of pages to print
        """
        return self._pages

    @pages.setter
    def pages(self, value):
        """
        Set the number of pages to print

        :param value: number of pages to print
        :raises TaskException: If value is not a integer
        """
        if not isinstance(value, int):
            raise TaskException('pages must be a integer')
        self._pages = value

    @property
    def priority(self):
        """
        Get the priority of the task

        :return: the priority of the task
        """
        return self._priority

    @priority.setter
    def priority(self, value):
        """
        Set the priority of the task

        :param value: priority of the task
        :raises TaskException: If value is not a integer
        """
        if not isinstance(value, int):
            raise TaskException('priority must be an integer')
        self._priority = value

    @property
    def username(self):
        """
        Get the user who submitted the task

        :return: the user who submitted the task
        """
        return self._username

    @username.setter
    def username(self, value):
        """
        Set the user who submitted the task

        :param value: the user who submitted the task
        :raises TaskException: If value is not a string
        """
        if not isinstance(value, str):
            raise TaskException('user must be a string')
        self._username = value

    def __str__(self):
        """
        Return a string representation of the task

        :return: String describing the task
        """
        return f"Task {self.name}, pages={self.pages}, priority={self.priority} by username={self.username}"
