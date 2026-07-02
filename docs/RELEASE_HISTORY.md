# NCC UHF Manager Release History



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
