import threading
import time
import asyncio
import win32print
import os
from PIL import Image
from pypdf import PdfReader
from pdf2image import convert_from_path
import io

from src.spooler.task_list import TaskList


class PrinterException(Exception):
    pass


class Printer(threading.Thread):
    def __init__(self, task_list, manager, loop, name="printer", get_system_state_func=None, printer_name="Xprinter"):
        threading.Thread.__init__(self)
        self.name = name
        self.tasks = task_list
        self.running = True
        self.manager = manager
        self.loop = loop
        self.current_task = None
        self.is_printing = False
        self.lock = threading.Lock()
        self.get_system_state_func = get_system_state_func
        self.printer_name = printer_name
        self.printer_available = False

        self.paper_width_mm = 58
        self.char_per_line = 32

        self._check_printer_availability()

        print(f"Printer thread: current task={self.current_task.name if self.current_task else None}")

    def _check_printer_availability(self):
        """
        Checks if the printer is available in Windows

        :return: True if the printer is available, False otherwise
        """
        try:
            printers = [printer[2] for printer in win32print.EnumPrinters(2)]
            if self.printer_name in printers:
                self.printer_available = True
                print(f"✓ Printer '{self.printer_name}' is connected and ready")
                return True
            else:
                self.printer_available = False
                print(f"✗ Printer '{self.printer_name}' not found.")
                print(f"Available printers: {printers}")
                return False
        except Exception as e:
            self.printer_available = False
            print(f"Error checking printer: {e}")
            return False

    def _extract_text_from_pdf(self, pdf_path):
        """
        Extract text from PDF for thermal printer

        :param pdf_path: Path to PDF file
        :return: Extracted text string
        """
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            raise PrinterException(f"Failed to extract PDF text: {e}")

    def _format_text_for_thermal(self, text):
        """
        Format text for thermal printer (word wrap, etc.)

        :param text: Text to format
        :return: Formatted text
        """
        lines = []
        for line in text.split('\n'):
            if len(line) <= self.char_per_line:
                lines.append(line)
            else:
                words = line.split(' ')
                current_line = ""
                for word in words:
                    if len(current_line) + len(word) + 1 <= self.char_per_line:
                        current_line += word + " "
                    else:
                        lines.append(current_line.strip())
                        current_line = word + " "
                if current_line:
                    lines.append(current_line.strip())

        return '\n'.join(lines)

    def _convert_image_to_thermal(self, image_or_path):
        """
        Convert a PIL.Image object or image path to ESC/POS bytes.
        """
        if isinstance(image_or_path, str):
            img = Image.open(image_or_path)
        else:
            img = image_or_path

        thermal_width = 384
        aspect_ratio = img.height / img.width
        new_height = int(thermal_width * aspect_ratio)

        img = img.resize((thermal_width, new_height), Image.Resampling.LANCZOS)
        img = img.convert('1')

        width_bytes = (thermal_width + 7) // 8
        height = img.height
        commands = b''

        for y in range(height):
            line_bytes = []
            for x in range(0, thermal_width, 8):
                byte = 0
                for bit in range(8):
                    if x + bit < thermal_width:
                        pixel = img.getpixel((x + bit, y))
                        if pixel == 0:
                            byte |= (1 << (7 - bit))
                line_bytes.append(byte)
            nL = width_bytes % 256
            nH = width_bytes // 256
            commands += b'\x1B\x2A\x21' + bytes([nL, nH]) + bytes(line_bytes) + b'\n'

        return commands

    def _print_raw(self, data, job_name="Print Job"):
        """
        Send raw data directly to thermal printer

        :param data: Bytes to send to printer
        :param job_name: Name for the print job
        """
        try:
            if not self._check_printer_availability():
                raise PrinterException(f"Printer '{self.printer_name}' is not available")

            hPrinter = win32print.OpenPrinter(self.printer_name)
            try:
                win32print.StartDocPrinter(hPrinter, 1, (job_name, None, "RAW"))
                win32print.StartPagePrinter(hPrinter)

                if isinstance(data, str):
                    try:
                        data = data.encode('cp852')
                    except:
                        data = data.encode('latin1', errors='replace')

                win32print.WritePrinter(hPrinter, data)
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)

            print(f"Data sent to printer successfully")

        except Exception as e:
            print(f"Error printing: {e}")
            raise PrinterException(f"Failed to print: {e}")

    def _print_file(self, file_path, task_name):
        """
        Print a file to the thermal printer.
        Supports PDF (text or image) and images.
        Converts scanned PDF pages to images automatically.
        """
        try:
            if not self._check_printer_availability():
                raise PrinterException(f"Printer '{self.printer_name}' is not available")

            file_ext = os.path.splitext(file_path)[1].lower()
            commands = b'\x1B\x40'

            if file_ext == '.pdf':
                print(f"Processing PDF: {file_path}")
                
                try:
                    text = self._extract_text_from_pdf(file_path)
                except Exception as e:
                    print(f"Text extraction failed: {e}")
                    text = ""

                if text.strip():
                    
                    formatted_text = self._format_text_for_thermal(text)

                    commands += b'\x1B\x61\x01'
                    commands += b'\x1D\x21\x11'
                    commands += f"{task_name}\n".encode('cp852', errors='replace')
                    commands += b'\x1D\x21\x00'
                    commands += b'\x1B\x61\x00'
                    commands += b'-' * self.char_per_line + b'\n'
                    commands += formatted_text.encode('cp852', errors='replace')
                    commands += b'\n' + b'-' * self.char_per_line + b'\n'
                else:
                    
                    print("PDF contains no text, converting pages to images...")
                    images = convert_from_path(file_path)
                    for img in images:
                        img_commands = self._convert_image_to_thermal(img)
                        commands += img_commands

            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                print(f"Converting image for thermal printer: {file_path}")
                commands += b'\x1B\x61\x01'
                commands += f"{task_name}\n".encode('cp852', errors='replace')
                commands += b'\x1B\x61\x00'
                img_commands = self._convert_image_to_thermal(file_path)
                commands += img_commands

            else:
                raise PrinterException(f"Unsupported file type: {file_ext}")

            commands += b'\n\n\n'
            commands += b'\x1D\x56\x00'

            self._print_raw(commands, task_name)
            print(f"Document printed: {file_path}")

        except Exception as e:
            print(f"Error printing file {file_path}: {e}")
            raise PrinterException(f"Failed to print: {e}")

    def _delete_file_after_print(self, file_path):
        """
        Delete the file after successful printing

        :param file_path: Path to file to delete
        """
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
        except Exception as e:
            print(f"Warning: Could not delete file {file_path}: {e}")

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
        """
        Stops the printer
        """
        with self.lock:
            self.running = False

        with self.tasks.not_empty:
            self.tasks.not_empty.notify_all()

        print("Finished printing")
        msg = "STOP: Printer is stopping"
        asyncio.run_coroutine_threadsafe(self.manager.broadcast(msg), self.loop)

    def get_status(self):
        """
        Returns the status of the printer

        :return: status of the printer
        """
        with self.lock:
            return {
                'running': self.running,
                'current_task': self.current_task,
                'is_printing': self.is_printing,
                'printer_available': self.printer_available
            }

    async def _broadcast_system_state(self):
        if self.get_system_state_func:
            state = await self.get_system_state_func()
            await self.manager.broadcast_json({"type": "system_state", "data": state})

    def run(self):
        """
        Main loop of the printer
        Handles printer disconnection and waits for reconnection
        """
        print("Printer thread started")

        while True:
            with self.lock:
                if not self.running:
                    break

            try:
                if not self._check_printer_availability():
                    if not self.printer_available:
                        msg = f"WARNING: Printer '{self.printer_name}' not connected. Waiting for connection..."
                        asyncio.run_coroutine_threadsafe(self.manager.broadcast(msg), self.loop)
                        print(msg)

                        time.sleep(5)
                        continue

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

                print_success = False
                try:
                    if hasattr(task, 'file_path') and task.file_path:
                        if not self._check_printer_availability():
                            raise PrinterException("Printer disconnected before printing")

                        self._print_file(task.file_path, task.name)
                        print_success = True

                        self._delete_file_after_print(task.file_path)

                        time.sleep(max(2, task.pages * 0.5))
                    else:
                        print("Warning: No file path found, skipping print")

                except PrinterException as print_error:
                    print(f"Printer error: {print_error}")
                    error_msg = f"ERROR: Printer issue with {task.name}. Task returned to queue."
                    asyncio.run_coroutine_threadsafe(self.manager.broadcast(error_msg), self.loop)

                    self.tasks.append(task)

                    with self.lock:
                        self.current_task = None
                        self.is_printing = False

                    asyncio.run_coroutine_threadsafe(self._broadcast_system_state(), self.loop)

                    time.sleep(10)
                    continue

                except Exception as e:
                    print(f"Unexpected error during printing: {e}")
                    import traceback
                    traceback.print_exc()

                    error_msg = f"ERROR: Failed to print {task.name}: {str(e)}"
                    asyncio.run_coroutine_threadsafe(self.manager.broadcast(error_msg), self.loop)

                    if hasattr(task, 'file_path'):
                        self._delete_file_after_print(task.file_path)

                if self.running and print_success:
                    msg_end = f"END: Printing finished {task.name}"
                    asyncio.run_coroutine_threadsafe(self.manager.broadcast(msg_end), self.loop)

                with self.lock:
                    self.current_task = None
                    self.is_printing = False

                if self.running:
                    asyncio.run_coroutine_threadsafe(self._broadcast_system_state(), self.loop)

            except Exception as e:
                print(f"Problem in printer thread: {e}")
                import traceback
                traceback.print_exc()

                with self.lock:
                    if self.running:
                        self.current_task = None
                        self.is_printing = False
                        asyncio.run_coroutine_threadsafe(self._broadcast_system_state(), self.loop)
                    else:
                        break

        print("Print thread has stopped")
