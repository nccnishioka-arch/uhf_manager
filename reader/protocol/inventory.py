from reader.exceptions import ReaderProtocolError
from reader.protocol.packet import build_command, get_payload, validate_response

INVENTORY_MSG_ID = 0x65


def build_inventory_command() -> bytes:
    return build_command(INVENTORY_MSG_ID)


def _signed16(data: bytes) -> int:
    return int.from_bytes(data, byteorder="big", signed=True)


def parse_inventory_response(response: bytes) -> list:
    """Inventory応答を解析してタグリストを返す。

    Returns:
        list[dict]: {"ant": int, "epc": str, "rssi": int} のリスト。
                    タグなし・エラー時は空リスト。

    Raises:
        ReaderProtocolError: レスポンスが不正なパケット形式の場合。
    """
    if not response:
        return []

    if not validate_response(response):
        raise ReaderProtocolError("Inventory応答が不正です")

    body = get_payload(response)
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
        rssi = _signed16(body[rssi_start:rssi_end])

        tags.append({
            "ant": ant,
            "epc": epc,
            "rssi": rssi,
        })

        offset = rssi_end

    return tags
