import unittest
from src.spooler.task_list import TaskList, TaskListException
from src.models.task import Task
from src.users.user import User

class TestTaskList(unittest.TestCase):
    def test_init(self):
        """
        Test that TaskList initializes correctly
        """
        task_list = TaskList()
        self.assertEqual(task_list.max_size, 10)
        self.assertEqual(task_list.size, 0)

    def test_setters(self):
        """
        Test the setter method
        """
        task_list = TaskList()
        task_list.max_size = 15
        self.assertEqual(task_list.max_size, 15)

    def test_setters_error(self):
        """
        Test that setter method with invalid value raises TaskListException
        """
        task_list = TaskList()
        with self.assertRaises(TaskListException):
            task_list.max_size = "A"

    def test_append(self):
        """
        Test the append() method
        """
        task_list = TaskList()
        user = User("user1",task_list, 1)
        task = Task("doc1", 10, 1, user)
        task_list.append(task)
        self.assertEqual(task_list.size, 1)

    def test_pop(self):
        """
        Test the pop() method
        """
        task_list = TaskList()
        user = User("user1",task_list, 1)
        task = Task("doc1", 10, 1, user)
        task_list.append(task)
        self.assertEqual(task_list.size, 1)
        task_list.pop()
        self.assertEqual(task_list.size, 0)

    def test_str(self):
        """
        Test the string representation is correct
        """
        task_list = TaskList()
        self.assertEqual(str(task_list), "Current Tasks: \n")

    def test_len(self):
        """
        Test the __len__ method return correct number of tasks
        """
        task_list = TaskList()
        self.assertEqual(len(task_list), 0)

if __name__ == '__main__':
    unittest.main()
