# NCC UHF Manager Release History

## v0.13.0

- `reader/reader_manager.py` : `232C(UART)` 設定値を UART として扱えるよう補正
- `dialogs/settings_dialog.py` : 既存 UART 設定の表示互換を復旧
- `main.py` : 接続方式変更後の Reader 再生成、LAN Inventory 読取、CSV保存、クリア時状態更新を復旧
- **実機確認復旧漏れ対応 (追加コミット)**
  - `widgets/table_items.py` : RSSI表示が "??????" になる問題を修正 → dBm値をテキスト表示、不明時は "-"
  - `reader/tcp_reader.py` : `set_antenna` / `get_antenna` を実装（LAN接続でのアンテナ操作を有効化）
  - `dialogs/settings_dialog.py` : qt_material でチェックボックス・スピンボックス矢印・コンボボックスが不可視になる問題を復旧
  - `dialogs/settings_dialog.py` : 接続テストで接続済みの場合は失敗扱いにせず「接続済み」を表示するよう修正
  - `dialogs/settings_dialog.py` : LAN接続テスト時に同一IP/ポートへ二重接続しないよう修正
  - `ui/settings_dialog.ui` : マスタパスに「参照...」ボタンを追加 (QFileDialog でCSVファイルを選択)
  - `app_config.py` : `DEFAULT_BOOKMASTER_PATH` の文字化け ("??????") を修正

## v0.12.9

- `reader/protocol/inventory.py` を追加し、Inventory Command / Response / EPC解析 / RSSI解析 を共通化
- `reader/uhf_reader.py` : `read_tags()` を共通プロトコル関数（`parse_inventory_response`）に移行
- `reader/tcp_reader.py` : `read_tags()` を共通プロトコル関数で実装（USB/UART/LAN 共通 API 化）
- `reader/protocol/__init__.py` : `build_inventory_command` / `parse_inventory_response` をエクスポートに追加

## v0.12.8

- `reader/protocol/` を追加し、ART Finex UHF Reader のコマンド生成・BCC・レスポンス検証を共通化
- `reader/tcp_reader.py` : LAN接続時の送信出力設定 / 取得を実装
- `main.py` : 未実装機能が残る場合でも原因が分かる電波強度ログへ改善
- タグ読取 / インベントリ は今回未実装

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

## v0.12.4

- show_settings整理

- LAN接続テスト重複削除

- clock_timer重複削除

## v0.12.2

\- Windows開発環境へ移行

\- app\_config 分離

\- settings\_service 分離

\- database\_service 分離

\- table\_items 分離

\- GitHub管理開始
