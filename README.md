\# NCC UHF Manager



Windows / Raspberry Pi 対応 UHF RFID 管理アプリケーション



\## Features



\- USB

\- RS232C(UART)

\- LAN（開発中）

\- SQLite

\- PySide6

\- Qt Designer



\## Version



Current Version : v0.12.5

## v0.12.5

- `show_settings()` を `dialogs/settings_dialog.py` へ移動し、`main.py` を軽量化
- `detect_serial_ports()` / `get_preferred_serial_port()` も `settings_dialog.py` へ移動
- 不要になった import を `main.py` から削除（`json`, `QFrame`, `QDialog`, `QStyle`, `list_ports`, `save_settings`）
- `dialogs/` パッケージを新規作成
