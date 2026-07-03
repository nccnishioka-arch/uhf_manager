import unittest

from reader.connection_state import ConnectionState
from reader.exceptions import ReaderConnectionError, ReaderProtocolError
from reader.protocol.artfinex_protocol import (
    build_get_tx_power_command,
    build_set_tx_power_command,
    parse_tx_power_response,
    validate_response,
)
from reader.protocol.inventory import build_inventory_command
from reader.protocol.packet import build_command
from reader.tcp_reader import TcpReader


class FakeSocket:
    def __init__(self, response: bytes):
        self._response = bytearray(response)
        self.sent = []

    def sendall(self, data: bytes):
        self.sent.append(data)

    def recv(self, size: int) -> bytes:
        if not self._response:
            return b""
        chunk = self._response[:size]
        del self._response[:size]
        return bytes(chunk)


class ProtocolAndTcpReaderTests(unittest.TestCase):
    def test_validate_response_accepts_valid_packet(self):
        response = build_command(0x1B, (2400).to_bytes(2, byteorder="big"))
        self.assertTrue(validate_response(response))
        self.assertEqual(parse_tx_power_response(response), 2400)

    def test_set_tx_power_sends_shared_protocol_command(self):
        response = build_command(0x16, b"\x00")
        reader = TcpReader()
        reader._socket = FakeSocket(response)
        reader._state = ConnectionState.CONNECTED

        self.assertTrue(reader.set_tx_power(2400))
        self.assertEqual(reader._socket.sent, [build_set_tx_power_command(2400)])

    def test_get_tx_power_returns_power_value(self):
        response = build_command(0x1B, (2400).to_bytes(2, byteorder="big"))
        reader = TcpReader()
        reader._socket = FakeSocket(response)
        reader._state = ConnectionState.CONNECTED

        self.assertEqual(reader.get_tx_power(), 2400)
        self.assertEqual(reader._socket.sent, [build_get_tx_power_command()])

    def test_tcp_reader_requires_connection(self):
        reader = TcpReader()
        with self.assertRaises(ReaderConnectionError):
            reader.set_tx_power(2400)

    def test_tcp_reader_rejects_invalid_response(self):
        invalid_response = build_command(0x1B, (2400).to_bytes(2, byteorder="big"))[:-1] + b"\x00"
        reader = TcpReader()
        reader._socket = FakeSocket(invalid_response)
        reader._state = ConnectionState.CONNECTED

        with self.assertRaises(ReaderProtocolError):
            reader.get_tx_power()

    def test_read_tags_returns_empty_when_no_tags(self):
        # status=0, tag_count=0
        payload = bytes([0x00, 0x00])
        response = build_command(0x65, payload)
        reader = TcpReader()
        reader._socket = FakeSocket(response)
        reader._state = ConnectionState.CONNECTED

        tags = reader.read_tags()
        self.assertEqual(tags, [])
        self.assertEqual(reader._socket.sent, [build_inventory_command()])

    def test_read_tags_returns_tag_list(self):
        epc_bytes = bytes.fromhex("E2001234567890ABCDEF1234")
        rssi_bytes = (0xFF9C).to_bytes(2, byteorder="big")  # -100 dBm
        data_len = len(epc_bytes) + len(rssi_bytes)  # epc + rssi = data_len
        # body: tag_count=1, status=0, ant, data_len, epc, rssi
        payload = bytes([0x01, 0x00, 0x01, data_len]) + epc_bytes + rssi_bytes
        response = build_command(0x65, payload)
        reader = TcpReader()
        reader._socket = FakeSocket(response)
        reader._state = ConnectionState.CONNECTED

        tags = reader.read_tags()
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0]["ant"], 1)
        self.assertEqual(tags[0]["epc"], epc_bytes.hex().upper())
        self.assertEqual(tags[0]["rssi"], -100)


if __name__ == "__main__":
    unittest.main()
