import threading
import time
import asyncio
import win32print
import os
from PIL import Image
from pypdf import PdfReader
from pdf2image import convert_from_path
import io

import re

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

    import re

    def _detect_invoice_language(self, text):
        """Detect invoice language"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['faktura', 'dodavatel', 'odběratel', 'celkem', 'částka']):
            return 'cs'
        elif any(
                word in text_lower for word in ['invoice', 'bill', 'receipt', 'total', 'amount', 'customer', 'vendor']):
            return 'en'
        else:
            return 'unknown'

    def _smart_format_invoice(self, text):
        """
        Universal invoice formatter - works with any layout/language
        Intelligently extracts key information without hardcoded patterns

        :param text: Extracted text from PDF
        :return: Formatted text for thermal printer
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        formatted = []
        width = self.char_per_line

        header_keywords = ['invoice', 'faktura', 'bill', 'receipt', 'daňový doklad', 'dañový doklad']
        vendor_keywords = ['from:', 'vendor:', 'seller:', 'dodavatel:', 'supplier:', 'issued by:']
        customer_keywords = ['to:', 'customer:', 'buyer:', 'odběratel:', 'odberatel:', 'bill to:', 'billed to:']
        date_keywords = ['date:', 'datum:', 'issued:', 'vystavení:', 'vystaveni:']
        due_keywords = ['due:', 'splatnost:', 'payment due:', 'due date:']
        payment_keywords = ['payment:', 'forma:', 'method:', 'úhrady:', 'uhrady:']
        items_keywords = ['item', 'description', 'product', 'položk', 'polozk', 'označení', 'oznaceni', 'qty',
                          'množství', 'mnozstvi']
        total_keywords = ['total', 'celkem', 'amount due', 'balance', 'součet', 'soucet', 'subtotal']
        tax_keywords = ['tax', 'vat', 'dph', 'gst']

        formatted.append('=' * width)

        current_section = None
        in_items_section = False
        found_total = False

        for i, line in enumerate(lines):
            line_lower = line.lower()

            if len(line) < 2 or line in ['HR', 'ks', 'Kč', 'Kc', '%DPH']:
                continue

            if any(keyword in line_lower for keyword in header_keywords):
                number_match = re.search(r'(?:č\.|#|no\.?|number)?\s*(\d{6,})', line, re.IGNORECASE)
                if number_match:
                    formatted.append(self._center_text('INVOICE', width))
                    formatted.append(self._center_text(f"#{number_match.group(1)}", width))
                    formatted.append('-' * width)
                else:
                    formatted.append(self._center_text(line[:width], width))
                    formatted.append('-' * width)
                continue

            if any(keyword in line_lower for keyword in vendor_keywords):
                current_section = 'vendor'
                formatted.append('')
                formatted.append('FROM:')
                formatted.append('-' * width)
                continue

            if any(keyword in line_lower for keyword in customer_keywords):
                current_section = 'customer'
                formatted.append('')
                formatted.append('TO:')
                formatted.append('-' * width)
                continue

            date_match = re.search(r'(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})', line)
            if date_match:
                date_str = date_match.group(1)
                if any(keyword in line_lower for keyword in date_keywords):
                    formatted.append(f"Date: {date_str}")
                    continue
                elif any(keyword in line_lower for keyword in due_keywords):
                    formatted.append(f"Due: {date_str}")
                    continue
                elif current_section not in ['vendor', 'customer']:
                    formatted.append(f"Date: {date_str}")
                    continue

            if re.search(r'(VS|variabilní|variable|ref|reference|order).*?(\d{3,})', line, re.IGNORECASE):
                ref_match = re.search(r'(\d{3,})', line)
                if ref_match:
                    formatted.append(f"Ref: {ref_match.group(1)}")
                continue

            if any(keyword in line_lower for keyword in payment_keywords):
                payment = re.sub(r'(payment|forma|method|úhrady|uhrady)[:\s]*', '', line, flags=re.IGNORECASE).strip()
                if payment and len(payment) < 20:
                    formatted.append(f"Payment: {payment}")
                continue

            if re.match(r'(IČ|IC|DIČ|DIC|VAT|Tax ID|EIN)[:\s]*', line, re.IGNORECASE):
                id_match = re.search(r'[\d\s]{6,}', line)
                if id_match:
                    label = line.split(':')[0].strip() if ':' in line else 'ID'
                    formatted.append(f"{label}: {id_match.group().strip()}")
                continue

            if any(keyword in line_lower for keyword in items_keywords) and not in_items_section:
                in_items_section = True
                formatted.append('')
                formatted.append('=' * width)
                formatted.append('ITEMS:')
                formatted.append('-' * width)
                continue

            if any(keyword in line_lower for keyword in total_keywords) and not found_total:
                in_items_section = False
                formatted.append('-' * width)

                amount = self._extract_amount(line)
                if amount:
                    formatted.append(self._format_total_line('TOTAL', amount, width))
                    found_total = True
                else:
                    formatted.append('TOTAL:')
                continue

            if in_items_section:
                if re.search(r'\d{1,3}[,\s]\d{3}|\d+[.,]\d{2}', line):
                    item_name, price = self._parse_item_line(line)
                    if item_name:
                        formatted.append(self._format_item_line(item_name, price, width))
                    continue

            if any(keyword in line_lower for keyword in tax_keywords):
                tax_match = re.search(r'(\d+)%.*?([\d,.\s]+)', line)
                if tax_match:
                    rate = tax_match.group(1)
                    amount = tax_match.group(2).replace(' ', '')
                    formatted.append(f"VAT {rate}%: {amount}")
                    continue

            if current_section in ['vendor', 'customer']:
                if not any(skip in line_lower for skip in ['ičo', 'ico', 'dič', 'dic', 'vat', 'tax']):
                    if len(line) <= width:
                        formatted.append(line)
                    else:
                        words = line.split()
                        current_line = ""
                        for word in words:
                            if len(current_line) + len(word) + 1 <= width:
                                current_line += word + " "
                            else:
                                if current_line:
                                    formatted.append(current_line.strip())
                                current_line = word + " "
                        if current_line:
                            formatted.append(current_line.strip())
                continue

            if re.search(r'\d{10,}', line) and len(line) < width:
                formatted.append(line)
                continue

        formatted.append('=' * width)
        return '\n'.join(formatted)

    def _extract_amount(self, text):
        """Extract monetary amount from text"""
        match = re.search(r'(\d{1,3}(?:[,\s]\d{3})*(?:[.,]\d{2})?)', text)
        if match:
            return match.group(1).replace(' ', '')
        return None

    def _parse_item_line(self, line):
        """
        Parse item line to extract name and price
        Returns: (item_name, price)
        """
        prices = re.findall(r'\d{1,3}(?:[,\s]\d{3})*(?:[.,]\d{2})', line)

        if not prices:
            return None, None

        price = prices[-1]

        item_name = re.sub(r'\d+[,.\s]*\d*', '', line).strip()
        item_name = re.sub(r'\s+', ' ', item_name)  # Clean multiple spaces
        item_name = re.sub(r'[^\w\s\-áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]', '', item_name)  # Remove special chars

        if len(item_name) > 3:
            return item_name, price

        return None, None

    def _center_text(self, text, width):
        """Center text within given width"""
        return text.center(width)

    def _format_item_line(self, item_name, price, width):
        """Format item line with dots"""
        price = str(price).replace(' ', '')

        max_item_len = width - len(price) - 3
        if len(item_name) > max_item_len:
            item_name = item_name[:max_item_len - 2] + '..'

        dots_count = width - len(item_name) - len(price) - 2
        if dots_count < 1:
            return f"{item_name}\n  {price}"

        dots = '.' * dots_count
        return f"{item_name} {dots} {price}"

    def _format_total_line(self, label, amount, width):
        """Format total line"""
        amount = str(amount).replace(' ', '')
        line = f"{label}: {amount}"

        if len(line) <= width:
            return line

        dots_count = width - len(label) - len(amount) - 2
        if dots_count < 1:
            return f"{label}\n{amount}"

        return f"{label} {'.' * dots_count} {amount}"

    def _get_encoding_for_text(self, text):
        """
        Determine best encoding for text based on content
        """
        # Check for Czech characters
        if any(char in text for char in 'áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ'):
            return 'cp852'

        elif any(char in text for char in 'àâäèéêëîïôöùûü'):
            return 'cp850'

        return 'cp437'

    def _print_file(self, file_path, task_name):
        """
        Print PDF with smart universal formatting
        """
        try:
            if not self._check_printer_availability():
                raise PrinterException(f"Printer '{self.printer_name}' is not available")

            file_ext = os.path.splitext(file_path)[1].lower()
            commands = b'\x1B\x40'

            if file_ext != '.pdf':
                raise PrinterException(f"Unsupported file type: {file_ext}")

            try:
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            except Exception as e:
                print(f"Text extraction failed: {e}")
                raise PrinterException(f"Failed to extract PDF text: {e}")

            if not text.strip():
                raise PrinterException("PDF contains no extractable text")

            is_invoice = self._detect_invoice_language(text) in ['cs', 'en']

            if is_invoice:
                formatted_text = self._smart_format_invoice(text)
            else:
                formatted_text = text

            encoding = self._get_encoding_for_text(formatted_text)
            print(f"Using encoding: {encoding}")

            commands += b'\x1B\x61\x00'
            try:
                commands += formatted_text.encode(encoding, errors='replace')
            except Exception:
                commands += formatted_text.encode('utf-8', errors='replace')

            commands += b'\n\n\n'
            commands += b'\x1D\x56\x00'

            self._print_raw(commands, task_name)
            print(f"Document printed: {file_path}")

        except Exception as e:
            print(f"Error printing file {file_path}: {e}")
            raise PrinterException(f"Failed to print: {e}")

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
