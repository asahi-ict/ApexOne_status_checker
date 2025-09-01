# ApexOne Status Checker

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Playwright](https://img.shields.io/badge/Playwright-Latest-green.svg)](https://playwright.dev)
[![Windows](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://windows.microsoft.com)
[![License](https://img.shields.io/badge/License-Internal%20Use-yellow.svg)](#ライセンス)

## 📋 概要

ApexOne Status Checkerは、Trend Micro Apex Oneの管理コンソールに自動ログインし、エージェントの接続ステータスを監視するPlaywrightベースの自動化ツールです。

### 🎯 主な用途
- Apex Oneエージェントのヘルスチェック自動化
- 定期的なステータス監視とレポート生成
- 管理者の日常業務効率化
- **OfficeScanシステムイベントログの自動取得**

## 🚀 機能

### ✨ 自動化機能
- 🌐 **Chromeデバッグモード自動起動**: 証明書エラー対応済み
- 🔑 **ドメインログイン**: Apex Oneコンソールへの自動認証
- 🧭 **自動ナビゲーション**: ダッシュボード → 概要ページへの自動移行
- **🔐 安全な認証情報管理**: 暗号化された認証情報の保存と再利用

### 📊 監視機能
- 🖥️ **エージェントステータス取得**: 指定された4つのApex Oneエージェントを監視
  - `PCVTMU54_OSCE`
  - `PCVTMU53_OSCE` 
  - `PCVTMU54_TMSM`
  - `PCVTMU53_TMSM`
- **📋 システムイベントログ監視**: OfficeScan管理コンソールからの最新ログ取得

### 📈 レポート機能
- ⚡ **リアルタイム判定**: 全て「有効」→OK、そうでなければNG
- 📝 **実行ログ**: CSV形式で実行履歴を蓄積
- 📊 **統計表示**: 成功率、実行回数などのサマリー表示
- **📸 スクリーンショット保存**: ログ取得時の画面キャプチャ

### ⏰ スケジューリング
- 🕙 **タスクスケジューラー対応**: 毎日自動実行可能
- 🔄 **バッチ実行**: ワンクリック実行対応

## 必要な環境

- Python 3.7以上
- Google Chrome ブラウザ
- Windows環境（テスト済み）

## セットアップ

### 1. 依存関係のインストール

```bash
# SSL証明書の問題がある場合
py -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

# 通常の場合
py -m pip install -r requirements.txt
```

### 2. ファイル構成

```
ApexOne_status_checker/
├── ApexOne_status_checker.py    # メインスクリプト（統合版）
├── ApexOne_log_checker.py       # ログチェッカー（新機能）
├── run_status_checker.bat       # 実行用バッチファイル
├── run_log_checker.bat          # ログチェッカー実行用バッチ
├── setup_task_scheduler.ps1     # タスクスケジューラー設定スクリプト
├── requirements.txt             # 依存関係
├── apexone_status_log.csv       # 実行ログ（自動生成）
├── apexone_log_checker.log      # ログチェッカー実行ログ
├── secure_credentials.enc       # 暗号化された認証情報
├── encryption_key.key           # 暗号化キー
├── タスクスケジューラー設定手順.md  # 設定手順書
└── README.md                    # このファイル
```

## 使用方法

### 統合版スクリプトの実行（推奨）

```bash
py ApexOne_status_checker.py
```

### ログチェッカーの実行（新機能）

```bash
py ApexOne_log_checker.py
```

**初回実行時:**
```
🔐 初回アクセスのため、認証情報を入力してください
==================================================
ユーザー名: admin
パスワード: ********
🔐 認証情報を暗号化して保存しました
```

**次回実行時:**
```
🔓 保存された認証情報を復号化しました
📋 ステップ1: OfficeScan管理コンソールにアクセス中...
📋 ステップ2: ログイン情報を入力中...
📋 ステップ3: ログイン処理中...
📋 ステップ4: ログメニューにアクセス中...
📋 ステップ5: システムイベントメニューを選択中...
📋 ステップ6: システムイベントログを取得中...

============================================================
📊 最新のシステムイベントログ:
============================================================
2025/01/15 10:30:15 INFO システム起動完了
============================================================
📸 スクリーンショットを保存: system_event_log_20250115_103015.png
```

### バッチファイルでの実行

```bash
# ステータスチェッカー
run_status_checker.bat

# ログチェッカー
run_log_checker.bat
```

## 判定ロジック

- **OK**: 4つの製品すべてが「有効」の場合
- **NG**: 1つでも「有効」以外（無効、接続なし、エラーなど）の場合
- **INSUFFICIENT_DATA**: 4つの製品のステータスを取得できなかった場合

## 出力ファイル

実行時に以下のファイルが自動保存されます：

- `apexone_status_check_[タイムスタンプ].png` - 最終画面のスクリーンショット
- `apexone_status_check_[タイムスタンプ].html` - ページのHTML
- `apexone_widget_content_[タイムスタンプ].html` - ウィジェットフレームのHTML
- `apexone_frame_text_[タイムスタンプ].txt` - フレームの抽出テキスト
- `apexone_status_log.csv` - 実行ログ（累積）
- **`system_event_log_[タイムスタンプ].png`** - システムイベントログ画面のスクリーンショット
- **`apexone_log_checker.log`** - ログチェッカー実行ログ
- **`secure_credentials.enc`** - 暗号化された認証情報
- **`encryption_key.key`** - 暗号化キー

## セキュリティ機能

### 🔐 認証情報の安全な管理
- **初回アクセス**: 手動でユーザー名・パスワードを入力
- **暗号化保存**: Fernet暗号化アルゴリズムで認証情報を暗号化
- **自動再利用**: 次回以降は保存された認証情報を自動使用
- **キー分離**: 暗号化キーと認証情報を別ファイルで管理

## トラブルシューティング

### Chrome起動エラー

**問題**: Chromeが起動しない、またはポート9222が利用できない

**解決策**:
1. `ApexOne_status_checker.py`を再実行（自動でChromeを起動）
2. Chromeの実行ファイルパスを確認
3. 管理者権限で実行

### SSL証明書エラー

**問題**: `net::ERR_CERT_AUTHORITY_INVALID` エラー

**解決策**:
- `ApexOne_status_checker.py`に含まれている以下のオプションが有効になっていることを確認：
  - `--ignore-certificate-errors`
  - `--ignore-ssl-errors`
  - `--ignore-certificate-errors-spki-list`

### 接続エラー

**問題**: Playwrightが接続できない

**解決策**:
1. `ApexOne_status_checker.py`を再実行（自動でChromeデバッグモードを起動）
2. ポート9222が使用中か確認: `netstat -an | findstr 9222`
3. ファイアウォールの設定を確認

### 認証情報エラー

**問題**: 保存された認証情報が使用できない

**解決策**:
1. `secure_credentials.enc`と`encryption_key.key`を削除
2. スクリプトを再実行して認証情報を再入力

## 技術仕様

- **対応システム**: Trend Micro Apex One 管理コンソール
- **対応ブラウザ**: Google Chrome（デバッグモード）
- **自動化ライブラリ**: Playwright
- **プロトコル**: Chrome DevTools Protocol (CDP)
- **デバッグポート**: 9222
- **SSL証明書**: 企業環境の証明書問題に対応済み
- **ログ機能**: CSV形式で実行結果を累積記録
- **スケジュール実行**: Windowsタスクスケジューラー対応
- **暗号化**: Fernet暗号化アルゴリズム
- **対象URL**: https://pcvtmu53:4343/officescan/

## 更新履歴

### v1.0 (2025/08/21)
- 初版リリース
- Chromeデバッグモード自動起動機能
- 4つの指定Apex Oneエージェントのステータス自動取得
- SSL証明書エラー対応
- 包括的なエラーハンドリング

### v2.0 (2025/08/21)
- 統合版スクリプト作成
- 実行ログ機能追加
- タスクスケジューラー対応
- ApexOneブランド化

### v3.0 (2025/01/15)
- **OfficeScanログチェッカー機能追加**
- **安全な認証情報管理機能**
- **システムイベントログ自動取得**
- **暗号化機能によるセキュリティ強化**

## ライセンス

このプロジェクトはApex One管理目的で作成されました。

## サポート

技術的な質問や問題については、開発者までお問い合わせください。