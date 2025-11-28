import unittest

from src.spooler.task_list import TaskList
from src.users.user import User, UserException

class UserTest(unittest.TestCase):
    def test_init(self):
        """
        Test that initialization works as expected
        """
        task_list = TaskList()
        user1 = User('user1', task_list, 1)
        self.assertEqual(user1.username, 'user1')
        self.assertEqual(user1.task_list, task_list)
        self.assertEqual(user1.number_of_tasks, 1)

    def test_setters(self):
        """
        Test that all setters work as expected
        """
        task_list1 = TaskList()
        user1 = User('user1', task_list1, 1)
        user1.username = 'user2'
        self.assertEqual(user1.username, 'user2')
        task_list2 = TaskList(10)
        user1.task_list = task_list2
        self.assertEqual(user1.task_list, task_list2)
        user1.number_of_tasks = 22
        self.assertEqual(user1.number_of_tasks, 22)

    def test_setters_error(self):
        """
        Test that setting an invalid value at all setters raises an UserException
        """
        task_list1 = TaskList()
        user1 = User('user1', task_list1, 1)
        with self.assertRaises(UserException):
            user1.username = False
        with self.assertRaises(UserException):
            user1.number_of_tasks = "Ten"
        with self.assertRaises(UserException):
            user1.task_list = "tasklist"

if __name__ == '__main__':
    unittest.main()
