import serial

PORT = "/dev/ttyUSB0"
BAUDRATE = 115200

def bcc(data: bytes) -> int:
    return sum(data) & 0xFF

ser = serial.Serial(PORT, baudrate=BAUDRATE, timeout=2)

# CBファミリ: 機器種別取得 0x1A
cmd = bytearray([
    0x53,       # 'S'
    0x00,       # フラグ
    0x00,       # 自局アドレス
    0x00,       # 宛先アドレス
    0x1A,       # メッセージ区分
    0x00,       # オプションフラグ
    0x00, 0x00, # レングス
    0x20,       # 年: 0x20固定
    0x00,       # 年
    0x00,       # 月
    0x00,       # 日
    0x00,       # 時
    0x00,       # 分
    0x00,       # 秒
    0x00,       # ミリ秒
])

cmd.append(bcc(cmd))

print("send:", cmd.hex(" ").upper())
ser.write(cmd)

data = ser.read(128)
print("recv:", data.hex(" ").upper())

ser.close()
