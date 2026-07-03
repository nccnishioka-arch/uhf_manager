from reader.exceptions import ReaderProtocolError
from reader.protocol.packet import (
    build_command,
    get_payload,
    validate_response as packet_validate_response,
)

SET_TX_POWER_MSG_ID = 0x16
GET_TX_POWER_MSG_ID = 0x1B


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
