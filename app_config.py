from pathlib import Path

APP_VERSION = "v0.12.4"

DB_PATH = "data/uhf_manager.db"
SETTINGS_PATH = "config/settings.json"

DEFAULT_BOOKMASTER_PATH = str(
    Path.home() / "OneDrive" / "??????" / "UHF Manager" / "bookmaster.csv"
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
    "lost_timeout_sec": 10,
    "tx_power": 2400,
    "connection_type": "USB",
    "host": "192.168.1.100",
    "tcp_port": 10001,
}
