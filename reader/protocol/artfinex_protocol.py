from reader.exceptions import ReaderProtocolError
from reader.protocol.packet import (
    build_command,
    get_payload,
    validate_response as packet_validate_response,
)

SET_TX_POWER_MSG_ID = 0x16
GET_TX_POWER_MSG_ID = 0x1B

SET_ANTENNA_PORT_MSG_ID = 0x88
GET_ANTENNA_PORT_MSG_ID = 0x89


def build_set_tx_power_command(power: int) -> bytes:
    if power < 0 or power > 2400:
        raise ValueError("送信出力は0〜2400で指定してください")

    return build_command(
        SET_TX_POWER_MSG_ID,
        power.to_bytes(2, byteorder="big", signed=False),
    )


def build_get_tx_power_command() -> bytes:
    return build_command(GET_TX_POWER_MSG_ID)


def validate_response(response: bytes) -> bool:
    return packet_validate_response(response)


def parse_set_tx_power_response(response: bytes) -> bool:
    if not validate_response(response):
        raise ReaderProtocolError("送信出力設定応答が不正です")

    body = get_payload(response)
    if len(body) == 0:
        return True

    return body[0] == 0


def parse_tx_power_response(response: bytes) -> int:
    if not validate_response(response):
        raise ReaderProtocolError("送信出力取得応答が不正です")

    body = get_payload(response)
    if len(body) < 2:
        raise ReaderProtocolError("送信出力取得応答のデータ長が不正です")

    return int.from_bytes(body[0:2], byteorder="big", signed=False)


def build_set_antenna_command(ant_no: int) -> bytes:
    if ant_no < 1 or ant_no > 4:
        raise ValueError("アンテナ番号は1〜4で指定してください")

    return build_command(SET_ANTENNA_PORT_MSG_ID, bytes([ant_no]))


def build_get_antenna_command() -> bytes:
    return build_command(GET_ANTENNA_PORT_MSG_ID)


def parse_set_antenna_response(response: bytes) -> bool:
    if not validate_response(response):
        raise ReaderProtocolError("アンテナ設定応答が不正です")

    body = get_payload(response)
    if len(body) == 0:
        return True

    return body[0] == 0


def parse_get_antenna_response(response: bytes) -> int:
    if not validate_response(response):
        raise ReaderProtocolError("アンテナ取得応答が不正です")

    body = get_payload(response)
    if len(body) < 1:
        raise ReaderProtocolError("アンテナ取得応答のデータ長が不正です")

    return body[0]
