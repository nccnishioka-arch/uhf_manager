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

## 2. バージョン管理

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

## 3. リリース手順

```powershell
git checkout main
git pull origin main
git merge develop
git push origin main

git tag -a v0.12.7 -m "NCC UHF Manager v0.12.7"
git push origin v0.12.7
```

ただし、GitHub PR で `develop → main` をマージする運用を優先する。

---

## 4. 開発方針

* Windows / Raspberry Pi 共通コードを維持する
* USB / UART / LAN は Reader 抽象化層を通して扱う
* UI 処理は `dialogs/`、通信処理は `reader/`、永続化処理は `services/` に分離する
* `main.py` を肥大化させない
* 既存動作を壊さない小さな PR を基本とする

---

## 5. コーディング方針

* Python 3.13 を前提とする
* PySide6 を使用する
* 型ヒントをできるだけ付ける
* 共通データは今後 `models/` に集約する
* 例外は Reader 共通例外を使う
* 通信方式ごとの差異は `reader/` 配下に閉じ込める
