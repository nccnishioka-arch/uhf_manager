class ReaderError(Exception):
    pass


class ReaderConnectionError(ReaderError):
    pass


class ReaderTimeoutError(ReaderError):
    pass


class ReaderProtocolError(ReaderError):
    pass
