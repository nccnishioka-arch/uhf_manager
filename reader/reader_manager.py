from reader.usb_reader import UsbReader
from reader.uart_reader import UartReader
from reader.tcp_reader import TcpReader
from reader.exceptions import ReaderConnectionError


def normalize_connection_type(connection_type):
    value = str(connection_type or "USB").strip()

    if value in ("UART", "232C(UART)", "RS232C(UART)"):
        return "UART"
    if value == "LAN":
        return "LAN"
    return "USB"


class ReaderManager:
    @staticmethod
    def create(settings):
        connection_type = normalize_connection_type(
            settings.get("connection_type", "USB")
        )

        if connection_type == "USB":
            return UsbReader(settings)
        elif connection_type == "UART":
            return UartReader(settings)
        elif connection_type == "LAN":
            return TcpReader(settings)

        raise ReaderConnectionError(f"Unsupported connection type: {connection_type}")
