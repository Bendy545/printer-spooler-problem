import unittest

from devices.printer import Printer, PrinterException
from spooler.task_list import TaskList


class PrinterTest(unittest.TestCase):
    def test_init(self):
        """
        Test that the Printer initializes correctly
        """
        task_list = TaskList()
        printer = Printer(task_list)
        self.assertEqual(printer.name, "printer")

    def test_tasks(self):
        """
        Test that the Printer stores the TaskList correctly
        """
        task_list = TaskList()
        printer = Printer(task_list)
        self.assertEqual(printer.tasks, task_list)

    def test_name_setter(self):
        """
        Test the setter of the Printer name
        """
        task_list = TaskList()
        printer = Printer(task_list)
        printer.name = "Laser"
        self.assertEqual(printer.name, "Laser")

    def test_name_error(self):
        """
        Test that setting an invalid name raises PrinterException
        """
        task_list = TaskList()
        printer = Printer(task_list)
        with self.assertRaises(PrinterException):
            printer.name = 9

    def test_stop(self):
        """
        Test the stop() method
        """
        task_list = TaskList()
        printer = Printer(task_list)
        self.assertEqual(printer.running, True)
        printer.stop()
        self.assertEqual(printer.running, False)


if __name__ == '__main__':
    unittest.main()
