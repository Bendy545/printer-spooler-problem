import unittest
from src.spooler.task_list import TaskList, TaskListException
from src.models.task import Task


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
        task = Task("doc1", 10, 1, "user")
        task_list.append(task)
        self.assertEqual(task_list.size, 1)

    def test_pop(self):
        """
        Test the pop() method
        """
        task_list = TaskList()
        task = Task("doc1", 10, 1, "user")
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

    def test_append_priority_insertion(self):
        """
        Test that tasks are added in correct order based on priority (lower number = higher priority).
        """
        task_list = TaskList()

        task_low = Task("low_doc", 1, 10, "user")
        task_high = Task("high_doc", 10, 2, "user")
        task_mid = Task("mid_doc", 5, 3, "user")

        task_list.append(task_low)
        task_list.append(task_high)
        task_list.append(task_mid)

        ordered_tasks = task_list.get_all_tasks()

        self.assertEqual(ordered_tasks[0].name, "high_doc")
        self.assertEqual(ordered_tasks[1].name, "mid_doc")
        self.assertEqual(ordered_tasks[2].name, "low_doc")
        self.assertEqual(task_list.size, 3)

        task_high_2 = Task("high_doc_2", 10, 1, "user")
        task_list.append(task_high_2)

        ordered_tasks = task_list.get_all_tasks()
        self.assertEqual(ordered_tasks[0].name, "high_doc_2")

if __name__ == '__main__':
    unittest.main()
