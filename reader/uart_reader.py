from reader.base_reader import BaseReader
from reader.uhf_reader import UHFReader


class UartReader(BaseReader):
    """UART接続用 Reader。
    
    v0.12.6 時点では USB と同等のシリアル通信として扱う。
    Raspberry Pi の /dev/ttyAMA0 や /dev/ttyS0 への対応は後続で拡張する。
    """

    def __init__(self, settings=None):
        super().__init__(settings)
        self._reader = UHFReader()

    def connect(self):
        port = self.settings.get("port", "/dev/ttyAMA0")
        baudrate = int(self.settings.get("baudrate", 115200))
        return self._reader.connect(port, baudrate)

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
        """UHFReader 互換エイリアス。read_once() と同等。"""
        return self._reader.read_tags()
