import socket
import serial

from reader.protocol import build_command, get_data_length, get_payload
from reader.protocol.artfinex_protocol import (
    build_get_tx_power_command,
    build_set_tx_power_command,
    parse_set_tx_power_response,
    parse_tx_power_response,
)
from reader.protocol.inventory import (
    INVENTORY_MSG_ID,
    build_inventory_command,
    parse_inventory_response,
)


class UHFReader:
    def __init__(self):
        self.conn = None
        self.connection_type = None

    def connect(self, port="/dev/ttyUSB0", baudrate=115200):
        self.close()
        self.conn = serial.Serial(port=port, baudrate=baudrate, timeout=3)
        self.connection_type = "USB"
        return self.conn.is_open

    def connect_tcp(self, host="192.168.1.100", port=10001, timeout=3):
        self.close()
        self.conn = socket.create_connection((host, int(port)), timeout=timeout)
        self.conn.settimeout(timeout)
        self.connection_type = "LAN"
        return True

    def is_connected(self):
        if self.conn is None:
            return False

        if self.connection_type == "USB":
            return self.conn.is_open

        if self.connection_type == "LAN":
            return True

        return False

    def close(self):
        if self.conn is None:
            return

        try:
            self.conn.close()
        except Exception:
            pass

        self.conn = None
        self.connection_type = None

    def _clear_buffers(self):
        if self.connection_type == "USB":
            self.conn.reset_input_buffer()
            self.conn.reset_output_buffer()

    def _send(self, data: bytes):
        if self.connection_type == "USB":
            self.conn.write(data)
            self.conn.flush()
            return

        if self.connection_type == "LAN":
            self.conn.sendall(data)
            return

        raise RuntimeError("リーダ未接続です")

    def _recv(self, size: int) -> bytes:
        if self.connection_type == "USB":
            return self.conn.read(size)

        if self.connection_type == "LAN":
            buf = b""
            while len(buf) < size:
                chunk = self.conn.recv(size - len(buf))
                if not chunk:
                    break
                buf += chunk
            return buf

        raise RuntimeError("リーダ未接続です")

    def _make_cb_command(self, msg_id: int, payload: bytes = b"") -> bytes:
        return build_command(msg_id, payload)

    def _read_response(self):
        header = self._recv(16)
        if len(header) < 16:
            return b""

        data_len = get_data_length(header)
        body = self._recv(data_len + 1)
        return header + body

    def _execute_command(self, msg_id: int, payload: bytes = b"") -> bytes:
        if not self.is_connected():
            raise RuntimeError("リーダ未接続です")

        cmd = self._make_cb_command(msg_id, payload)

        self._clear_buffers()
        self._send(cmd)

        return self._read_response()

    def _signed16(self, data: bytes) -> int:
        return int.from_bytes(data, byteorder="big", signed=True)

    def set_antenna(self, ant_no: int):
        if ant_no < 1 or ant_no > 16:
            raise ValueError("アンテナ番号は1〜16で指定してください")

        res = self._execute_command(0x82, bytes([ant_no]))
        if not res:
            return False

        body = res[16:-1]
        if len(body) == 0:
            return True

        return body[0] == 0

    def get_antenna(self):
        res = self._execute_command(0x83)
        if not res:
            return None

        body = res[16:-1]
        if len(body) < 1:
            return None

        return body[0]

    def set_tx_power(self, power: int):
        if power < 0 or power > 2400:
            raise ValueError("送信出力は0〜2400で指定してください")
        if not self.is_connected():
            raise RuntimeError("リーダ未接続です")

        self._clear_buffers()
        self._send(build_set_tx_power_command(power))
        res = self._read_response()

        if not res:
            return False

        return parse_set_tx_power_response(res)

    def get_tx_power(self):
        if not self.is_connected():
            raise RuntimeError("リーダ未接続です")

        self._clear_buffers()
        self._send(build_get_tx_power_command())
        res = self._read_response()
        if not res:
            return None

        body = get_payload(res)
        if len(body) < 2:
            return None

        return parse_tx_power_response(res)

    def read_tags(self):
        res = self._execute_command(INVENTORY_MSG_ID)
        if not res:
            return []

        return parse_inventory_response(res)
