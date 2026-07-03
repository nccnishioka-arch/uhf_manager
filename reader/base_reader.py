class BaseReader:
    def __init__(self, settings=None):
        self.settings = settings or {}

    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError

    def is_connected(self):
        raise NotImplementedError

    def read_once(self):
        raise NotImplementedError

    def start_continuous_reading(self):
        raise NotImplementedError

    def stop_continuous_reading(self):
        raise NotImplementedError
