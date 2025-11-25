import threading
import time
import asyncio

from src.spooler.task_list import TaskList

class PrinterException(Exception):
    pass

class Printer(threading.Thread):
    def __init__(self, task_list, manager, loop, name="printer", get_system_state_func=None):
        threading.Thread.__init__(self)
        self.name = name
        self.tasks = task_list
        self.running = True
        self.manager = manager
        self.loop = loop
        self.current_task = None
        self.is_printing = False
        self.lock = threading.Lock()
        self.get_system_state_func = get_system_state_func  # Store the function reference

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise PrinterException("Printer Name must be a string")
        self._name = value

    @property
    def tasks(self):
        return self._tasks

    @tasks.setter
    def tasks(self, value):
        if not isinstance(value, TaskList):
            raise PrinterException("Printer tasks must be a TaskList class")
        self._tasks = value

    def stop(self):
        with self.lock:
            self.running = False

        with self.tasks.not_empty:
            self.tasks.not_empty.notify_all()

        print("Finished printing")
        msg = "STOP: Printer is stopping"
        asyncio.run_coroutine_threadsafe(self.manager.broadcast(msg), self.loop)

    def get_status(self):
        with self.lock:
            return {
                'running': self.running,
                'current_task': self.current_task,
                'is_printing': self.is_printing
            }

    async def _broadcast_system_state(self):
        if self.get_system_state_func:
            state = await self.get_system_state_func()
            await self.manager.broadcast_json({"type": "system_state", "data": state})

    def run(self):
        """
        Main loop of the printer
        """
        print("Printer thread started")
        while True:
            with self.lock:
                if not self.running:
                    break

            try:
                task = self.tasks.pop()

                with self.lock:
                    if not self.running:
                        self.tasks.append(task)
                        break

                    self.current_task = task
                    self.is_printing = True

                msg_start = f"START: Printing {task.name} ({task.pages} pages) for {task.user.username}"
                asyncio.run_coroutine_threadsafe(self.manager.broadcast(msg_start), self.loop)
                asyncio.run_coroutine_threadsafe(self._broadcast_system_state(), self.loop)

                print_msg = f"PRINTING: {task.name}, pages={task.pages}, priority={task.priority} for user={task.user.username}"
                print(print_msg)

                for page in range(task.pages):
                    if not self.running:
                        break
                    time.sleep(1)  # 1 second per page
                    print(f"Printed page {page + 1}/{task.pages} of {task.name}")

                if self.running:
                    msg_end = f"END: Printing finished {task.name}"
                    asyncio.run_coroutine_threadsafe(self.manager.broadcast(msg_end), self.loop)

                with self.lock:
                    self.current_task = None
                    self.is_printing = False

                if self.running:
                    asyncio.run_coroutine_threadsafe(self._broadcast_system_state(), self.loop)

            except Exception as e:
                print(f"Problem in printer thread: {e}")
                with self.lock:
                    if self.running:
                        self.current_task = None
                        self.is_printing = False
                        asyncio.run_coroutine_threadsafe(self._broadcast_system_state(), self.loop)
                    else:
                        break

        print("Print thread has stopped")