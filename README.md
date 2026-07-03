\# NCC UHF Manager



Windows / Raspberry Pi 対応 UHF RFID 管理アプリケーション



\## Features



\- USB

\- RS232C(UART)

\- LAN（TCP socket 接続対応）

\- SQLite

\- PySide6

\- Qt Designer



\## Version



Current Version : v0.12.8

## v0.12.8

- `reader/protocol/` を追加し、ART Finex UHF Reader のコマンド生成・BCC・レスポンス検証を共通化
- `reader/tcp_reader.py` : LAN接続時の送信出力設定 / 取得を実装
- `main.py` : 未実装機能が残る場合でも原因が分かる電波強度ログへ改善
- タグ読取 / インベントリ は今回未実装のまま維持
## v0.12.7

- `reader/tcp_reader.py` : LAN接続処理を実装（TCP socket による接続・切断・状態確認）
- `reader/tcp_reader.py` : `ConnectionState` による内部状態管理を追加
- `reader/tcp_reader.py` : 接続失敗時に `ReaderConnectionError` を送出するよう変更
- `main.py` : `ReaderConnectionError` をインポートし、LAN接続失敗時のログを改善
- `dialogs/settings_dialog.py` : LAN設定保存時に IP アドレスとポート番号のバリデーションを追加
- `app_config.py` : `connection_timeout` をデフォルト設定に追加（デフォルト: 5秒）

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
