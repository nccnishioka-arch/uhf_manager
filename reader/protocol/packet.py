HEADER_SIZE = 16
CHECKSUM_SIZE = 1
START_BYTE = 0x53


def calculate_bcc(data: bytes) -> int:
    return sum(data) & 0xFF


def build_command(msg_id: int, payload: bytes = b"") -> bytes:
    length = len(payload)
    cmd = bytearray([
        START_BYTE, 0x00, 0x00, 0x00,
        msg_id,
        0x00,
        length & 0xFF,
        (length >> 8) & 0xFF,
        0x20, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,
    ])
    cmd.extend(payload)
    cmd.append(calculate_bcc(cmd))
    return bytes(cmd)


def get_data_length(header: bytes) -> int:
    if len(header) < HEADER_SIZE:
        raise ValueError("ヘッダ長が不足しています")
    return header[6] + (header[7] << 8)


def get_expected_response_length(header: bytes) -> int:
    return HEADER_SIZE + get_data_length(header) + CHECKSUM_SIZE


def get_payload(response: bytes) -> bytes:
    if len(response) < HEADER_SIZE + CHECKSUM_SIZE:
        return b""
    return response[HEADER_SIZE:-CHECKSUM_SIZE]


def validate_response(response: bytes) -> bool:
    if len(response) < HEADER_SIZE + CHECKSUM_SIZE:
        return False
    if response[0] != START_BYTE:
        return False

    try:
        expected_length = get_expected_response_length(response[:HEADER_SIZE])
    except ValueError:
        return False

    if len(response) != expected_length:
        return False

    return calculate_bcc(response[:-1]) == response[-1]
