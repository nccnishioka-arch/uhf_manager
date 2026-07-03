# NCC UHF Manager Release History

## v0.13.4

- `main.py` : 複数アンテナ読取結果を EPC 単位で重複排除し、同一EPCを1行表示・1冊カウントへ統一
  - 同一EPCが複数ANTで読めた場合は、RSSIが強い読取結果を優先して ANT / RSSI を更新
  - 検出冊数表示を EPC ユニーク数ベースに変更
  - `check_movements` / `present` / `missed_count` / `active_taken` は従来どおり EPC 単位管理を維持
- `main.py` / `ui/main_window.ui` : Reader情報の「現在ANT」を「ANT数」に変更し、設定中 `antenna_count` を表示
  - LAN接続時の `ANT0` 表示を解消
- `app_config.py` : バージョンを `0.13.4` に更新
- `tests/test_main_regressions.py` : EPC重複排除・Reader ANT数表示・RSSI不正値ロバスト性の回帰テストを追加
  - `test_read_once_rssi_none_dash_string_does_not_crash` : None / "-" / 文字列 の RSSI が来ても例外なく、弱い値として扱われることを検証
  - `test_read_once_rssi_only_bad_values_does_not_crash` : 全 ANT で RSSI 不正でも EPC 1行にまとまることを検証

## v0.13.3

- `main.py` : 持出判定を「未読秒数」だけで即判定せず、連続未検出回数も満たした場合のみ持出に変更
  - `missed_count` をタグ単位・読取サイクル単位で保持し、再検出時は未読回数をリセット
  - `lost_timeout_sec` と新規 `lost_detection_count` の両条件成立時のみ `持出` を記録
  - `持出` 済みタグの再検出時は従来どおり `返却` 表示へ戻し、継続読取時は `棚にある` へ復帰
- `app_config.py` : `lost_timeout_sec` の初期値を 5 秒へ変更し、`lost_detection_count` 初期値 3 回を追加
- `dialogs/settings_dialog.py` / `ui/settings_dialog.ui` / `services/settings_service.py` : `持出判定回数` 設定の保存・再読込に対応
- `tests/test_main_regressions.py` : 持出判定安定化・再検出復帰・設定保存の回帰テストを追加

## v0.13.2

- `reader/protocol/artfinex_protocol.py` : アンテナ設定 88h / アンテナ取得 89h コマンドを追加 (UXA250-4 / CBファミリARモデル LAN対応)
  - `build_set_antenna_command(ant_no)` / `build_get_antenna_command()` を追加
  - `parse_set_antenna_response()` / `parse_get_antenna_response()` を追加
- `reader/protocol/__init__.py` : 新規アンテナ関数をエクスポートに追加
- `reader/tcp_reader.py` : `set_antenna()` / `get_antenna()` を実装 (88h/89h プロトコルを使用)
  - 従来の `NotImplementedError` を解消
- `main.py` : LAN接続時のアンテナ読取を「ソフトウェアフィルタ方式」から「実アンテナ切替方式」に変更
  - `antenna_count` 設定に応じて ANT1〜ANT4 を順番に切替えながら読取
  - ANT列には実際に切替えたアンテナ番号を表示
  - USB / UART と同一ループを使用 (USB / UART の既存動作は変更なし)
- `tests/test_protocol_tcp_reader.py` : `set_antenna` / `get_antenna` のテストを追加
- `tests/test_main_regressions.py` : LAN接続のテストを実アンテナ切替動作に合わせて更新

## v0.13.1

- `main.py` : LAN接続時も `antenna_count` 設定に応じて ANT1〜ANT4 のタグをフィルタリング
  - Inventory応答に含まれる各タグの `ant` 番号が `1 ≤ ant ≤ antenna_count` の範囲内のみを処理対象とする
  - `set_antenna()` は呼び出さず、単一の Inventory コマンドで全タグを取得してソフトウェアでフィルタリング
  - USB / UART の既存アンテナ切替ループは変更なし
- `tests/test_main_regressions.py` : LAN アンテナフィルタリングのテスト追加

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
