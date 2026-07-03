# NCC UHF Manager 開発ガイドライン

## 1. Git 運用

### 基本フロー

```
feature
  ↓
develop
  ↓
PR
  ↓
main
  ↓
Git Tag
```

### ルール

* 作業ブランチは `develop` から作成する
* PR の向きは原則 `develop` 向け
* `main` への直接 PR・直接 push は禁止
* `main` はリリース専用ブランチ
* Copilot への依頼時は必ず以下を含める

```
Target branch: develop

Do not create PR against main.
```

---

## 2. ブランチ命名規則

```
feature/xxxx
fix/xxxx
refactor/xxxx
docs/xxxx
release/vx.xx.x
hotfix/vx.xx.x
```

Copilot が作成するブランチも、この命名規則に従う。

---

## 3. バージョン管理

### バージョン番号の規則

```
Major.Minor.Patch

Major  : 製品版・大規模な仕様変更
Minor  : 新機能・アーキテクチャ変更
Patch  : バグ修正・小規模改善
```

ロードマップ例：

```
0.12.x  リファクタリング
0.13.x  コアアーキテクチャ・データモデル
0.14.x  業務機能追加
1.0.0   正式版
```

### 更新対象ファイル

リリース時は必ず以下を更新する。

```
app_config.py
README.md
docs/RELEASE_HISTORY.md
Git Tag
```

`app_config.py` の形式は `v` なし。

```python
APP_VERSION = "0.12.7"
```

画面表示やログ表示では `v{APP_VERSION}` とする。

Git Tag は `v` あり。

```
v0.12.7
```

---

## 4. リリース手順

```powershell
git checkout main
git pull origin main
git merge develop
git push origin main

git tag -a v0.12.7 -m "NCC UHF Manager v0.12.7"
git push origin v0.12.7
```

ただし、GitHub PR で `develop → main` をマージする運用を優先する。

### リリースチェックリスト

* APP_VERSION 更新
* README 更新
* docs/RELEASE_HISTORY 更新
* Git Tag 作成
* main ブランチ更新
* リリース後に working tree clean を確認
* Tag が HEAD を指していることを確認

---

## 5. Pull Request 方針

PR は小さく保つ。

目安：

* 1 PR = 1 機能
* UI 変更と通信変更を同一 PR に含めない
* リファクタリングと新機能追加を混在させない

---

## 6. アーキテクチャ規則

各モジュールの責務を明確にする。

```
main.py      起動・配線のみ
dialogs/     Dialog UI
widgets/     Custom Widget
reader/      通信
services/    DB・設定・CSV
models/      データモデル
utils/       共通処理
```

`main.py` には業務ロジックを書かない。

---

## 7. 開発方針

* Windows / Raspberry Pi 共通コードを維持する
* USB / UART / LAN は Reader 抽象化層を通して扱う
* UI 処理は `dialogs/`、通信処理は `reader/`、永続化処理は `services/` に分離する
* `main.py` を肥大化させない
* 既存動作を壊さない小さな PR を基本とする

### 将来の通信方式追加

今後追加される通信方式（BLE・Wi-Fi・その他）は必ず `BaseReader` を継承する。
通信方式ごとの差異は `reader/` 配下に閉じ込め、UI や Service へ影響を与えない設計を維持する。

---

## 8. コーディング方針

* Python 3.13 を前提とする
* PySide6 を使用する
* 型ヒントをできるだけ付ける
* 共通データは今後 `models/` に集約する
* 例外は Reader 共通例外を使う
* 通信方式ごとの差異は `reader/` 配下に閉じ込める

---

## 9. Copilot ルール

すべての実装で以下を遵守する。

```
Target branch: develop

Do not create PR against main.
```

PR の Base branch は必ず `develop` とする。
