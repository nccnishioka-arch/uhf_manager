from reader.base_reader import BaseReader
from reader.uhf_reader import UHFReader


class TcpReader(BaseReader):
    """LAN/TCP接続用 Reader。
    
    v0.12.6 時点では最小実装。
    IP / Port は settings から受け取り、将来的に完全な TCP 通信を実装する。
    """

    def __init__(self, settings=None):
        super().__init__(settings)
        self._reader = UHFReader()

    def connect(self):
        host = self.settings.get("host", "192.168.1.100")
        port = int(self.settings.get("tcp_port", 10001))
        return self._reader.connect_tcp(host, port)

    def disconnect(self):
        self._reader.close()

    def is_connected(self):
        return self._reader.is_connected()

    def read_once(self):
        return self._reader.read_tags()

    def start_continuous_reading(self):
        raise NotImplementedError

    def stop_continuous_reading(self):
        raise NotImplementedError

    # --- UHFReader 互換メソッド ---

    def set_antenna(self, ant_no):
        return self._reader.set_antenna(ant_no)

    def get_antenna(self):
        return self._reader.get_antenna()

    def set_tx_power(self, power):
        return self._reader.set_tx_power(power)

    def get_tx_power(self):
        return self._reader.get_tx_power()

    def read_tags(self):
        return self._reader.read_tags()

    def close(self):
        self._reader.close()
