import time
import serial

PORT = "/dev/ttyUSB0"
BAUDRATE = 115200


def bcc(data: bytes) -> int:
    return sum(data) & 0xFF


def make_cb_command(msg_id: int, payload: bytes = b"") -> bytes:
    length = len(payload)
    cmd = bytearray([
        0x53, 0x00, 0x00, 0x00,
        msg_id,
        0x00,
        length & 0xFF,
        (length >> 8) & 0xFF,
        0x20, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,
    ])
    cmd.extend(payload)
    cmd.append(bcc(cmd))
    return bytes(cmd)


def read_response(ser):
    header = ser.read(16)
    if len(header) < 16:
        return b""

    data_len = header[6] + (header[7] << 8)
    body = ser.read(data_len + 1)
    return header + body


def signed16(data: bytes) -> int:
    return int.from_bytes(data, byteorder="big", signed=True)


def parse_rssi_response(res: bytes):
    if not res:
        print("応答なし")
        return

    print("recv:", res.hex(" ").upper())

    body = res[16:-1]

    if len(body) < 2:
        print("タグなし")
        return

    tag_count = body[0]
    status = body[1]

    print()
    print("===================================")
    print(f"タグ数: {tag_count}")
    print(f"ステータス: {status}")
    print("===================================")

    offset = 2

    for i in range(tag_count):
        try:
            ant = body[offset]
            data_len = body[offset + 1]

            epc_len = data_len - 2

            epc_start = offset + 2
            epc_end = epc_start + epc_len

            epc = body[epc_start:epc_end].hex().upper()

            rssi_start = epc_end
            rssi_end = rssi_start + 2

            rssi = signed16(body[rssi_start:rssi_end])

            print(f"{i + 1:02d}: ANT={ant} RSSI={rssi:4d} EPC={epc}")

            offset = rssi_end

        except Exception as e:
            print(f"{i + 1}: 解析失敗 offset={offset} error={e}")
            break

ser = serial.Serial(PORT, baudrate=BAUDRATE, timeout=3)

ser.reset_input_buffer()
ser.reset_output_buffer()
time.sleep(0.2)

cmd = make_cb_command(0x65)

print("send:", cmd.hex(" ").upper())

ser.write(cmd)
ser.flush()
time.sleep(0.2)

res = read_response(ser)

parse_rssi_response(res)

ser.close()
