# Contributing to ApexOne Status Checker

## 🤝 コントリビューションガイド

ApexOne Status Checkerへのコントリビューションを歓迎します！

## 📝 コントリビューション方法

### 1. Issue の報告
- バグ報告
- 機能要求
- 質問やサポート

### 2. Pull Request
1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/AmazingFeature`)
3. 変更をコミット (`git commit -m 'Add some AmazingFeature'`)
4. ブランチにプッシュ (`git push origin feature/AmazingFeature`)
5. Pull Requestを開く

## 🔧 開発環境のセットアップ

### 前提条件
- Python 3.7+
- Google Chrome
- Windows 10/11

### セットアップ手順
```bash
# リポジトリをクローン
git clone https://github.com/[username]/ApexOne_status_checker.git
cd ApexOne_status_checker

# 仮想環境を作成
python -m venv venv
venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt
```

## 📋 コーディング規約

### Python コーディングスタイル
- PEP 8に従う
- 関数とクラスにはdocstringを記述
- 変数名は英語で記述（コメントは日本語OK）

### コミットメッセージ
- 英語で記述
- 簡潔で分かりやすく
- 例: `feat: add new status check feature`

## 🧪 テスト

### テスト実行
```bash
# メインスクリプトのテスト
python ApexOne_status_checker.py

# バッチファイルのテスト
run_status_checker.bat
```

## 📚 ドキュメント

- README.mdの更新
- コード内コメントの充実
- 新機能の使用方法を記述

## 🚨 セキュリティ

- 認証情報をコードに含めない
- `.gitignore`でセンシティブな情報を除外
- セキュリティ関連の問題は private issue で報告

## 📬 連絡先

- Issues: このリポジトリのIssuesセクション
- メール: [適切な連絡先を記述]

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。
