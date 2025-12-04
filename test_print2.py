import win32print
from pypdf import PdfReader


def test_simple_text():
    """Test 1: Simple text printing (like your working example)"""
    print("Test 1: Simple text printing...")
    printer_name = "Xprinter"

    hPrinter = win32print.OpenPrinter(printer_name)
    win32print.StartDocPrinter(hPrinter, 1, ("Test Print", None, "RAW"))
    win32print.StartPagePrinter(hPrinter)

    # Simple text
    text = b"=================================\n"
    text += b"   TEST TISKU THERMAL PRINTER\n"
    text += b"=================================\n"
    text += b"Ahoj! Toto je testovaci tisk.\n"
    text += b"Pokud toto vidis, printer funguje!\n\n"
    text += b"Radek 1: Test\n"
    text += b"Radek 2: Faktura\n"
    text += b"Radek 3: Invoice\n\n\n"

    win32print.WritePrinter(hPrinter, text)
    win32print.EndPagePrinter(hPrinter)
    win32print.EndDocPrinter(hPrinter)
    win32print.ClosePrinter(hPrinter)

    print("✓ Test 1 completed - check printer output")


def test_formatted_text():
    """Test 2: Formatted text with ESC/POS commands"""
    print("\nTest 2: Formatted text with ESC/POS...")
    printer_name = "Xprinter"

    hPrinter = win32print.OpenPrinter(printer_name)
    win32print.StartDocPrinter(hPrinter, 1, ("Formatted Test", None, "RAW"))
    win32print.StartPagePrinter(hPrinter)

    # ESC/POS commands
    commands = b'\x1B\x40'  # Initialize printer
    commands += b'\x1B\x61\x01'  # Center alignment
    commands += b'\x1D\x21\x11'  # Double size
    commands += b'FAKTURA\n'
    commands += b'\x1D\x21\x00'  # Normal size
    commands += b'\x1B\x61\x00'  # Left alignment
    commands += b'--------------------------------\n'
    commands += b'Polozka 1:          100 Kc\n'
    commands += b'Polozka 2:          200 Kc\n'
    commands += b'--------------------------------\n'
    commands += b'CELKEM:             300 Kc\n'
    commands += b'\n\n\n'
    commands += b'\x1D\x56\x00'  # Cut paper

    win32print.WritePrinter(hPrinter, commands)
    win32print.EndPagePrinter(hPrinter)
    win32print.EndDocPrinter(hPrinter)
    win32print.ClosePrinter(hPrinter)

    print("✓ Test 2 completed - check formatted output")


def test_pdf_text_extraction(pdf_path):
    """Test 3: Extract text from PDF"""
    print(f"\nTest 3: Extracting text from PDF: {pdf_path}")

    try:
        reader = PdfReader(pdf_path)
        text = ""
        for i, page in enumerate(reader.pages):
            print(f"  Page {i + 1}:")
            page_text = page.extract_text()
            print(f"    {page_text[:100]}...")  # First 100 chars
            text += page_text + "\n"

        print(f"\n✓ Successfully extracted {len(text)} characters")
        print("\nWould you like to print this? (y/n)")

        choice = input().lower()
        if choice == 'y':
            print_pdf_text(text)

    except Exception as e:
        print(f"✗ Error: {e}")


def print_pdf_text(text):
    """Print extracted PDF text to thermal printer"""
    print("Printing PDF text to thermal printer...")
    printer_name = "Xprinter"

    # Format text for 58mm thermal (32 chars per line)
    char_per_line = 32
    formatted_lines = []

    for line in text.split('\n'):
        if len(line) <= char_per_line:
            formatted_lines.append(line)
        else:
            # Simple word wrap
            words = line.split(' ')
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 <= char_per_line:
                    current_line += word + " "
                else:
                    formatted_lines.append(current_line.strip())
                    current_line = word + " "
            if current_line:
                formatted_lines.append(current_line.strip())

    formatted_text = '\n'.join(formatted_lines)

    # Print
    hPrinter = win32print.OpenPrinter(printer_name)
    win32print.StartDocPrinter(hPrinter, 1, ("PDF Print", None, "RAW"))
    win32print.StartPagePrinter(hPrinter)

    commands = b'\x1B\x40'  # Initialize
    commands += b'\x1B\x61\x01'  # Center
    commands += b'PDF DOCUMENT\n'
    commands += b'\x1B\x61\x00'  # Left
    commands += b'================================\n'

    try:
        commands += formatted_text.encode('cp852', errors='replace')
    except:
        commands += formatted_text.encode('latin1', errors='replace')

    commands += b'\n\n\n'
    commands += b'\x1D\x56\x00'  # Cut

    win32print.WritePrinter(hPrinter, commands)
    win32print.EndPagePrinter(hPrinter)
    win32print.EndDocPrinter(hPrinter)
    win32print.ClosePrinter(hPrinter)

    print("✓ PDF text printed!")


if __name__ == "__main__":
    print("=" * 50)
    print("THERMAL PRINTER TEST SUITE")
    print("=" * 50)

    # Test 1: Simple text (your working example)
    test_simple_text()
    input("\nPress Enter to continue to Test 2...")

    # Test 2: Formatted text with ESC/POS
    test_formatted_text()
    input("\nPress Enter to continue to Test 3...")

    # Test 3: PDF text extraction
    print("\nTest 3: PDF Text Extraction")
    pdf_path = "CV9_Chmelík_Vydaná_faktura.pdf"

    if pdf_path:
        test_pdf_text_extraction(pdf_path)
    else:
        print("Skipped PDF test")

    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)