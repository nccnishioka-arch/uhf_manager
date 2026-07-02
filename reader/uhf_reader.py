import socket
import serial


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

    def _bcc(self, data: bytes) -> int:
        return sum(data) & 0xFF

    def _make_cb_command(self, msg_id: int, payload: bytes = b"") -> bytes:
        length = len(payload)
        cmd = bytearray([
            0x53, 0x00, 0x00, 0x00,
            msg_id,
            0x00,
            length & 0xFF,
            (length >> 8) & 0xFF,
            0x20, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00,
        ])
        cmd.extend(payload)
        cmd.append(self._bcc(cmd))
        return bytes(cmd)

    def _read_response(self):
        header = self._recv(16)
        if len(header) < 16:
            return b""

        data_len = header[6] + (header[7] << 8)
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

        payload = power.to_bytes(2, byteorder="big", signed=False)
        res = self._execute_command(0x16, payload)

        if not res:
            return False

        body = res[16:-1]
        if len(body) == 0:
            return True

        return body[0] == 0

    def get_tx_power(self):
        res = self._execute_command(0x1B)
        if not res:
            return None

        body = res[16:-1]
        if len(body) < 2:
            return None

        return int.from_bytes(body[0:2], byteorder="big", signed=False)

    def read_tags(self):
        res = self._execute_command(0x65)
        if not res:
            return []

        body = res[16:-1]
        if len(body) < 2:
            return []

        tag_count = body[0]
        status = body[1]

        if status != 0:
            return []

        tags = []
        offset = 2

        for _ in range(tag_count):
            if offset + 2 > len(body):
                break

            ant = body[offset]
            data_len = body[offset + 1]
            epc_len = data_len - 2

            epc_start = offset + 2
            epc_end = epc_start + epc_len
            rssi_start = epc_end
            rssi_end = rssi_start + 2

            if rssi_end > len(body):
                break

            epc = body[epc_start:epc_end].hex().upper()
            rssi = self._signed16(body[rssi_start:rssi_end])

            tags.append({
                "ant": ant,
                "epc": epc,
                "rssi": rssi,
            })

            offset = rssi_end

        return tags
