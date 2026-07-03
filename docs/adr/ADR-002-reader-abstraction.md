# ADR-002: Reader 抽象化層の追加

## ステータス

採用済み（v0.12.6）

## コンテキスト

USB 接続のみを前提とした `reader/uhf_reader.py` が `main.py` から直接使用されていた。
UART / LAN（TCP）への対応拡張が困難であり、接続方式ごとの差異が `main.py` に漏れ出す懸念があった。

## 決定

v0.12.6 で Reader 抽象化層を `reader/` 配下に追加した。

追加したモジュール：

| モジュール | 内容 |
|---|---|
| `reader/connection_state.py` | 通信状態を表す Enum |
| `reader/exceptions.py` | Reader 共通例外クラス |
| `reader/base_reader.py` | Reader 共通基底クラス `BaseReader` |
| `reader/usb_reader.py` | USB 接続用 `UsbReader`（`UHFReader` をラップ） |
| `reader/uart_reader.py` | UART 接続用 `UartReader` |
| `reader/tcp_reader.py` | LAN/TCP 接続用 `TcpReader` |
| `reader/reader_manager.py` | 接続方式に応じて Reader を生成する `ReaderManager` |

`main.py` では `ReaderManager.create(settings)` を使用することで、
接続方式の詳細を意識せずに Reader を生成できる。

## 理由

* USB / UART / LAN を統一インターフェースで切替可能にする
* 通信方式ごとの差異を `reader/` 配下に閉じ込め、`main.py` への漏れを防ぐ
* 将来的な接続方式の追加を容易にする

## 影響

* 既存の `reader/uhf_reader.py` は互換性維持のため残す
* `main.py` は `ReaderManager.create(settings)` のみを呼び出す形に変更

## 今後の方針

* 通信方式ごとの差異は `UsbReader` / `UartReader` / `TcpReader` に閉じ込める
* 新たな接続方式を追加する場合は `BaseReader` を継承し、`ReaderManager` に登録する
* `reader/uhf_reader.py` への直接依存は新規コードでは避ける
