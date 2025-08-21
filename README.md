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

## 🚀 機能

### ✨ 自動化機能
- 🌐 **Chromeデバッグモード自動起動**: 証明書エラー対応済み
- 🔑 **ドメインログイン**: Apex Oneコンソールへの自動認証
- 🧭 **自動ナビゲーション**: ダッシュボード → 概要ページへの自動移行

### 📊 監視機能
- 🖥️ **エージェントステータス取得**: 指定された4つのApex Oneエージェントを監視
  - `PCVTMU54_OSCE`
  - `PCVTMU53_OSCE` 
  - `PCVTMU54_TMSM`
  - `PCVTMU53_TMSM`

### 📈 レポート機能
- ⚡ **リアルタイム判定**: 全て「有効」→OK、そうでなければNG
- 📝 **実行ログ**: CSV形式で実行履歴を蓄積
- 📊 **統計表示**: 成功率、実行回数などのサマリー表示

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
├── run_status_checker.bat       # 実行用バッチファイル
├── setup_task_scheduler.ps1     # タスクスケジューラー設定スクリプト
├── requirements.txt             # 依存関係
├── apexone_status_log.csv       # 実行ログ（自動生成）
├── タスクスケジューラー設定手順.md  # 設定手順書
└── README.md                    # このファイル
```

## 使用方法

### 統合版スクリプトの実行（推奨）

```bash
py ApexOne_status_checker.py
```

**実行結果の例：**
```
🚀 Chromeデバッグモード起動スクリプト
🔧 デバッグポート: 9222
📁 ユーザーデータディレクトリ: C:\Users\[ユーザー名]\chrome_debug_profile
✅ Chrome実行ファイル発見: C:\Program Files\Google\Chrome\Application\chrome.exe
🚀 Chromeをデバッグモードで起動中...
✅ Chromeプロセス起動成功 (PID: XXXXX)
✅ ポート9222が利用可能になりました
🎯 Playwrightから接続可能です
🎉 Chromeデバッグモード起動完了！
```

### バッチファイルでの実行

```bash
run_status_checker.bat
```

**実行結果の例：**
```
🎯 ApexOne：指定された4つの製品の接続ステータスを確実に確認します
🎯 対象製品: PCVTMU54_OSCE, PCVTMU53_OSCE, PCVTMU54_TMSM, PCVTMU53_TMSM

🔍 Chromeデバッグポート(9222)の確認中...
✅ Chromeデバッグポート(9222)が利用可能です

📋 ステップ1: ログインページにアクセス中...
✅ ログインページにアクセス成功
📋 ステップ2: ドメインログインボタンを探す中...
✅ ドメインログインボタンをクリックしました
📋 ステップ3: メインページにアクセス中...
✅ メインページにアクセス成功
📋 ステップ4: フレーム構造を確認中...
🖼️ フレーム数: 24
📋 ステップ5: ダッシュボードボタンを探す中...
✅ ダッシュボードをクリックしました
📋 ステップ6: 概要ボタンを探す中...
✅ 概要をクリックしました
📋 ステップ7: 製品の接続ステータスを確認中...

📊 取得結果:
   1. PCVTMU54_OSCE: ✅ 有効
   2. PCVTMU53_OSCE: ✅ 有効
   3. PCVTMU54_TMSM: ✅ 有効
   4. PCVTMU53_TMSM: ✅ 有効

🎯 最終判定結果: OK
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

## 技術仕様

- **対応システム**: Trend Micro Apex One 管理コンソール
- **対応ブラウザ**: Google Chrome（デバッグモード）
- **自動化ライブラリ**: Playwright
- **プロトコル**: Chrome DevTools Protocol (CDP)
- **デバッグポート**: 9222
- **SSL証明書**: 企業環境の証明書問題に対応済み
- **ログ機能**: CSV形式で実行結果を累積記録
- **スケジュール実行**: Windowsタスクスケジューラー対応

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

## ライセンス

このプロジェクトはApex One管理目的で作成されました。

## サポート

技術的な質問や問題については、開発者までお問い合わせください。