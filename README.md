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



Current Version : v0.12.7

## v0.12.7

- `CONTRIBUTING.md` を追加（Git 運用・バージョン管理・開発方針を明文化）
- `docs/adr/ADR-001-settings-dialog.md` を追加
- `docs/adr/ADR-002-reader-abstraction.md` を追加

## v0.12.6

- `reader/` 配下に Reader 抽象化基盤を追加
- `reader/connection_state.py` : 通信状態 Enum を追加
- `reader/exceptions.py` : Reader 共通例外クラスを追加
- `reader/base_reader.py` : Reader 共通基底クラス `BaseReader` を追加
- `reader/usb_reader.py` : USB接続用 `UsbReader` を追加（`UHFReader` をラップ）
- `reader/uart_reader.py` : UART接続用 `UartReader` を追加
- `reader/tcp_reader.py` : LAN/TCP接続用 `TcpReader` を追加
- `reader/reader_manager.py` : 接続方式に応じて Reader を生成する `ReaderManager` を追加
- `main.py` で `ReaderManager.create(settings)` を使用するよう変更

## v0.12.5

- `show_settings()` を `dialogs/settings_dialog.py` へ移動し、`main.py` を軽量化
- `detect_serial_ports()` / `get_preferred_serial_port()` も `settings_dialog.py` へ移動
- 不要になった import を `main.py` から削除（`json`, `QFrame`, `QDialog`, `QStyle`, `list_ports`, `save_settings`）
- `dialogs/` パッケージを新規作成
