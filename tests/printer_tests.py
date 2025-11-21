import unittest

from devices.printer import Printer, PrinterException
from spooler.task_list import TaskList


class PrinterTest(unittest.TestCase):
    def test_init(self):
        task_list = TaskList()
        printer = Printer(task_list)
        self.assertEqual(printer.name, "printer")

    def test_tasks(self):
        task_list = TaskList()
        printer = Printer(task_list)
        self.assertEqual(printer.tasks, task_list)

    def test_name_setter(self):
        task_list = TaskList()
        printer = Printer(task_list)
        printer.name = "Laser"
        self.assertEqual(printer.name, "Laser")

    def test_name_error(self):
        task_list = TaskList()
        printer = Printer(task_list)
        with self.assertRaises(PrinterException):
            printer.name = 9

    def test_stop(self):
        task_list = TaskList()
        printer = Printer(task_list)
        self.assertEqual(printer.running, True)
        printer.stop()
        self.assertEqual(printer.running, False)


if __name__ == '__main__':
    unittest.main()
