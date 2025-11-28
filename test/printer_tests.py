import unittest
import asyncio

from src.devices.printer import Printer, PrinterException
from src.spooler.task_list import TaskList

class DummyManager:
    """
    Simple mock of the WebSocket manager with async methods.
    """
    async def broadcast(self, msg):
        pass

    async def broadcast_json(self, data):
        pass

class PrinterTest(unittest.TestCase):

    def setUp(self):
        """
        Runs before each test
        """
        self.task_list = TaskList()
        self.manager = DummyManager()
        self.loop = asyncio.new_event_loop()

    def test_init(self):
        """
        Test printer initializes correctly
        """
        printer = Printer(
            self.task_list,
            self.manager,
            self.loop,
            name="TestPrinter"
        )
        self.assertEqual(printer.name, "TestPrinter")
        self.assertTrue(printer.running)
        self.assertFalse(printer.is_printing)

    def test_init_missing_tasklist(self):
        """
        Test that wrong task_list type raises error
        """
        with self.assertRaises(PrinterException):
            Printer("wrong", self.manager, self.loop)

    def test_name_setter(self):
        """
        Test setter for printer name
        """
        printer = Printer(self.task_list, self.manager, self.loop)
        printer.name = "LaserJet"
        self.assertEqual(printer.name, "LaserJet")

    def test_name_setter_invalid(self):
        """
        Test invalid name assignment raises exception
        """
        printer = Printer(self.task_list, self.manager, self.loop)
        with self.assertRaises(PrinterException):
            printer.name = 1234

    def test_tasks_setter_invalid(self):
        """
        Test invalid task list raises exception
        """
        printer = Printer(self.task_list, self.manager, self.loop)
        with self.assertRaises(PrinterException):
            printer.tasks = "not-a-tasklist"

    def test_get_status(self):
        """
        Test get_status returns correct structure
        """
        printer = Printer(self.task_list, self.manager, self.loop)

        status = printer.get_status()
        self.assertEqual(status["running"], True)
        self.assertEqual(status["current_task"], None)
        self.assertEqual(status["is_printing"], False)

if __name__ == '__main__':
    unittest.main()