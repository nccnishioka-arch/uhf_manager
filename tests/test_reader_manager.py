import unittest

from reader.reader_manager import ReaderManager, normalize_connection_type
from reader.tcp_reader import TcpReader
from reader.uart_reader import UartReader
from reader.usb_reader import UsbReader


class ReaderManagerTests(unittest.TestCase):
    def test_normalize_connection_type_absorbs_ui_and_saved_values(self):
        cases = {
            None: "USB",
            "": "USB",
            "USB": "USB",
            "LAN": "LAN",
            "UART": "UART",
            "232C(UART)": "UART",
            "RS232C(UART)": "UART",
        }

        for raw_value, expected in cases.items():
            with self.subTest(raw_value=raw_value):
                self.assertEqual(normalize_connection_type(raw_value), expected)

    def test_create_returns_uart_reader_for_uart_alias(self):
        reader = ReaderManager.create({"connection_type": "232C(UART)"})
        self.assertIsInstance(reader, UartReader)

    def test_create_returns_expected_reader_types(self):
        self.assertIsInstance(
            ReaderManager.create({"connection_type": "USB"}),
            UsbReader,
        )
        self.assertIsInstance(
            ReaderManager.create({"connection_type": "LAN"}),
            TcpReader,
        )


if __name__ == "__main__":
    unittest.main()
