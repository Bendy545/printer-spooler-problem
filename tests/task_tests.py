import unittest
from users.user import User
from spooler.task_list import TaskList
from models.task import Task, TaskException

class TaskTests(unittest.TestCase):
    def test_init(self):
        task_list = TaskList()
        user1 = User("User1", task_list, 2)
        task = Task("Doc", 12, 2, user1)
        self.assertEqual(task.name, "Doc")
        self.assertEqual(task.pages, 12)
        self.assertEqual(task.priority, 2)
        self.assertEqual(task.user, user1)

    def test_setters(self):
        task_list = TaskList()
        user1 = User("User1", task_list, 2)
        user2 = User("User2", task_list, 2)
        task = Task("Doc", 12, 2, user1)
        task.name = "Help"
        self.assertEqual(task.name, "Help")
        task.pages = 22
        self.assertEqual(task.pages, 22)
        task.priority = 8
        self.assertEqual(task.priority, 8)
        task.user = user2
        self.assertEqual(task.user, user2)

    def test_setters_error(self):
        task_list = TaskList()
        user1 = User("User1", task_list, 2)
        task = Task("Doc", 12, 2, user1)
        with self.assertRaises(TaskException):
            task.name = set()
        with self.assertRaises(TaskException):
            task.pages = "one"
        with self.assertRaises(TaskException):
            task.priority = None
        with self.assertRaises(TaskException):
            task.user = "user"

    def test_str(self):
        task_list = TaskList()
        user1 = User("User1", task_list, 2)
        task = Task("Doc", 12, 2, user1)
        self.assertEqual(str(task), "Task Doc, pages=12, priority=2 by user=User1")



if __name__ == "__main__":
    unittest.main()