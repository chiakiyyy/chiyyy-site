#!/bin/bash
# MoneyForward自動化スクリプト セットアップ

set -e

echo "======================================"
echo " セットアップを開始します"
echo "======================================"

# Python パッケージのインストール
echo ""
echo "1. Pythonパッケージをインストール中..."
pip install -r requirements.txt

# .env ファイルの確認
echo ""
if [ ! -f ".env" ]; then
    echo "2. .envファイルを作成中..."
    cp .env.example .env
    echo "   ⚠️ .envを編集してログイン情報を入力してください。"
    echo "   → nano .env または テキストエディタで開いてください"
else
    echo "2. .envファイルはすでに存在します。"
fi

echo ""
echo "======================================"
echo " 次のステップ"
echo "======================================"
echo ""
echo "【Google Sheets 認証設定（初回のみ）】"
echo "1. https://console.cloud.google.com にアクセス"
echo "2. プロジェクト作成（または既存選択）"
echo "3. 「APIとサービス」→「ライブラリ」→「Google Sheets API」を有効化"
echo "4. 「認証情報」→「認証情報を作成」→「OAuthクライアントID」"
echo "5. アプリの種類: デスクトップアプリ"
echo "6. ダウンロードした JSON を credentials.json として"
echo "   このフォルダ（personal/moneyfwd/）に保存"
echo ""
echo "【実行方法】"
echo "  python main.py ダウンロードしたCSV.csv"
echo ""
echo "初回実行時にブラウザが開きGoogleアカウント認証を求めます。"
echo "2回目以降は自動で実行されます。"
