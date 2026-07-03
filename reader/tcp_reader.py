import socket

from reader.base_reader import BaseReader
from reader.connection_state import ConnectionState
from reader.exceptions import ReaderConnectionError, ReaderProtocolError
from reader.protocol import HEADER_SIZE, get_data_length
from reader.protocol.artfinex_protocol import (
    build_get_tx_power_command,
    build_set_tx_power_command,
    parse_set_tx_power_response,
    parse_tx_power_response,
)


class TcpReader(BaseReader):
    """LAN/TCP接続用 Reader。

    settings から IP アドレスとポートを取得し、TCP socket で接続する。
    接続成功時は ConnectionState.CONNECTED、失敗時は ReaderConnectionError を送出する。
    """

    def __init__(self, settings=None):
        super().__init__(settings)
        self._socket = None
        self._state = ConnectionState.DISCONNECTED

    def connect(self):
        host = self.settings.get("host", "192.168.1.100")
        port = int(self.settings.get("tcp_port", 10001))
        timeout = int(self.settings.get("connection_timeout", 5))

        self._state = ConnectionState.CONNECTING
        try:
            self._socket = socket.create_connection((host, port), timeout=timeout)
            self._socket.settimeout(timeout)
            self._state = ConnectionState.CONNECTED
            return True
        except Exception as e:
            self._socket = None
            self._state = ConnectionState.ERROR
            raise ReaderConnectionError(
                f"LAN接続に失敗しました: {host}:{port} ({e})"
            ) from e

    def disconnect(self):
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None
        self._state = ConnectionState.DISCONNECTED

    def is_connected(self):
        return self._state == ConnectionState.CONNECTED

    def read_once(self):
        raise NotImplementedError

    def start_continuous_reading(self):
        raise NotImplementedError

    def stop_continuous_reading(self):
        raise NotImplementedError

    def _ensure_connected(self):
        if not self.is_connected() or self._socket is None:
            raise ReaderConnectionError("LANリーダが接続されていません")

    def _send(self, data: bytes):
        self._ensure_connected()
        try:
            self._socket.sendall(data)
        except OSError as e:
            self._state = ConnectionState.ERROR
            raise ReaderConnectionError(f"LAN送信に失敗しました: {e}") from e

    def _recv_exact(self, size: int) -> bytes:
        self._ensure_connected()
        buf = b""

        while len(buf) < size:
            try:
                chunk = self._socket.recv(size - len(buf))
            except socket.timeout as e:
                self._state = ConnectionState.ERROR
                raise ReaderConnectionError("LAN受信がタイムアウトしました") from e
            except OSError as e:
                self._state = ConnectionState.ERROR
                raise ReaderConnectionError(f"LAN受信に失敗しました: {e}") from e

            if not chunk:
                self._state = ConnectionState.ERROR
                raise ReaderConnectionError("LAN接続が切断されました")

            buf += chunk

        return buf

    def _read_response(self) -> bytes:
        header = self._recv_exact(HEADER_SIZE)

        try:
            data_len = get_data_length(header)
        except ValueError as e:
            raise ReaderProtocolError(str(e)) from e

        body = self._recv_exact(data_len + 1)
        return header + body

    # --- 将来実装予定（タグ読取・アンテナ・Inventory は対象外） ---

    def set_antenna(self, ant_no):
        raise NotImplementedError

    def get_antenna(self):
        raise NotImplementedError

    def set_tx_power(self, power):
        self._send(build_set_tx_power_command(power))
        response = self._read_response()
        return parse_set_tx_power_response(response)

    def get_tx_power(self):
        self._send(build_get_tx_power_command())
        response = self._read_response()
        return parse_tx_power_response(response)

    def read_tags(self):
        raise NotImplementedError
