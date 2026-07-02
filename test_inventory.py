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


def parse_inventory_response(res: bytes):
    if not res:
        print("応答なし")
        return

    print("recv:", res.hex(" ").upper())

    body = res[16:-1]
    if not body:
        print("タグなし")
        return

    tag_count = body[0]
    print("tag_count:", tag_count)

    offset = 1

    for i in range(tag_count):
        rec = body[offset:offset + 18]

        if len(rec) < 18:
            print(f"{i + 1}: データ不足")
            break

        ant = rec[0]
        uii_len = rec[1]
        pc = rec[2:4].hex().upper()
        epc = rec[4:-2].hex().upper()
        crc = rec[-2:].hex().upper()

        print(
            f"{i + 1}: "
            f"ANT={ant} "
            f"UII_LEN={uii_len} "
            f"PC={pc} "
            f"EPC={epc} "
            f"CRC={crc}"
        )

        offset += 18


ser = serial.Serial(PORT, baudrate=BAUDRATE, timeout=3)

cmd = make_cb_command(0x20)

print("send:", cmd.hex(" ").upper())

ser.reset_input_buffer()
ser.write(cmd)

res = read_response(ser)

parse_inventory_response(res)

ser.close()
