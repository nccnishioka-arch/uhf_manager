from pathlib import Path

APP_VERSION = "0.13.5"

DB_PATH = "data/uhf_manager.db"
SETTINGS_PATH = "config/settings.json"

DEFAULT_BOOKMASTER_PATH = str(
    Path.home() / "ドキュメント" / "bookmaster.csv"
)

DEFAULT_SETTINGS = {
    "port": "/dev/ttyUSB0",
    "baudrate": 115200,
    "antenna_count": 1,
    "auto_connect": True,
    "auto_load_books": True,
    "auto_start_reading": True,
    "bookmaster_path": DEFAULT_BOOKMASTER_PATH,
    "read_interval_ms": 500,
    "lost_timeout_sec": 5,
    "lost_detection_count": 3,
    "tx_power": 2400,
    "connection_type": "USB",
    "host": "192.168.1.100",
    "tcp_port": 10001,
    "connection_timeout": 5,
}
