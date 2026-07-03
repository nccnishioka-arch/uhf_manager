# ADR-001: Settings Dialog の分離

## ステータス

採用済み（v0.12.5）

## コンテキスト

`main.py` に設定ダイアログの表示ロジック（`show_settings()`）が直接実装されていた。
機能追加に伴い `main.py` が肥大化し、UI 責務と通信・制御責務が混在していた。

## 決定

v0.12.5 で `show_settings()` を `dialogs/settings_dialog.py` に分離した。
あわせて `detect_serial_ports()` / `get_preferred_serial_port()` も同ファイルへ移動した。

## 理由

* `main.py` の肥大化を防ぐ
* UI 責務を `dialogs/` パッケージに集約する
* 設定画面の独立したテスト・拡張を容易にする

## 影響

* 不要になった import を `main.py` から削除（`json`, `QFrame`, `QDialog`, `QStyle`, `list_ports`, `save_settings`）
* `dialogs/` パッケージを新規作成

## 今後の方針

今後の設定画面の拡張は `dialogs/settings_dialog.py` を中心に行う。
新たな設定項目や UI 変更はすべてこのファイルに閉じ込め、`main.py` には影響を与えない。
