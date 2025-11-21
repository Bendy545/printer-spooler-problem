import unittest
from spooler.task_list import TaskList, TaskListException
from models.task import Task
from users.user import User

class TestTaskList(unittest.TestCase):
    def test_init(self):
        task_list = TaskList()
        self.assertEqual(task_list.max_size, 10)
        self.assertEqual(task_list.size, 0)

    def test_setters(self):
        task_list = TaskList()
        task_list.max_size = 15
        self.assertEqual(task_list.max_size, 15)

    def test_setters_error(self):
        task_list = TaskList()
        with self.assertRaises(TaskListException):
            task_list.max_size = "A"

    def test_append(self):
        task_list = TaskList()
        user = User("user1",task_list, 1)
        task = Task("doc1", 10, 1, user)
        task_list.append(task)
        self.assertEqual(task_list.size, 1)

    def test_pop(self):
        task_list = TaskList()
        user = User("user1",task_list, 1)
        task = Task("doc1", 10, 1, user)
        task_list.append(task)
        self.assertEqual(task_list.size, 1)
        task_list.pop()
        self.assertEqual(task_list.size, 0)

    def test_str(self):
        task_list = TaskList()
        self.assertEqual(str(task_list), "Current Tasks: \n")

    def test_len(self):
        task_list = TaskList()
        self.assertEqual(len(task_list), 0)

if __name__ == '__main__':
    unittest.main()
