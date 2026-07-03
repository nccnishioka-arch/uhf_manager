import socket

from reader.base_reader import BaseReader
from reader.connection_state import ConnectionState
from reader.exceptions import ReaderConnectionError


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
            except Exception:
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

    # --- 将来実装予定（タグ読取・アンテナ・TxPower は対象外） ---

    def set_antenna(self, ant_no):
        raise NotImplementedError

    def get_antenna(self):
        raise NotImplementedError

    def set_tx_power(self, power):
        raise NotImplementedError

    def get_tx_power(self):
        raise NotImplementedError

    def read_tags(self):
        raise NotImplementedError
