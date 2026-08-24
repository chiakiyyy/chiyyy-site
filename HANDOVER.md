# chiyyy-site 引き継ぎメモ

> 新しいClaudeセッションへの引き継ぎ用。このファイルを読んだ上で作業を続けてください。

## サイト概要

- **URL**: chiyyy.com
- **構成**: Astro / Cloudflare Pages
- **デプロイ**: mainブランチにマージ → Cloudflare自動ビルド・公開
- **作業ブランチ**: `claude/shared-session-21y970`（→ mainへのPRを通じて公開）
- **記事数**: 12記事（2026-08-24時点）

## 最近の作業（前セッション完了分）

### 公開済み記事（ブランチにプッシュ済み・main未マージ）
- `src/content/blog/job-dislike-family-cannot-change.md`
  - タイトル: 「転職に踏み出せない人へ。「家族のため」という不安の正体と、最初にやること一つ」
  - カテゴリ: お金・キャリア
  - ブランチ `claude/shared-session-21y970` にpush済み（SHA: eaf801b）
  - **mainへのマージがまだ**

## ペンディングタスク

### 1. JACリクルートメント・doda アフィリエイトリンク追加
- `job-dislike-family-cannot-change.md` でJACリクルートメント・dodaをテキストで紹介中
- ASPからトラッキングURLを取得し、`affiliates.json` に追加 → AffCardコンポーネントで表示
- 追加時は `affiliates.json` の既存フォーマット（type-women-agentなど）を参考に

### 2. MoneyForward ME のトラッキングURL設定
- `affiliates.json` の `moneyforward-me` エントリ: 提携承認済みだがURLがまだ空
- ASPからURLが来たら `url` フィールドに設定 → `status: "active"` に変更

### 3. マイナビキャリレーション ASP承認待ち
- `affiliates.json` の `mynavi-careerelation`: アクセストレード提携申請中（2026-07-29）
- 承認されたらURLを設定して `status: "active"` に

### 4. Google AdSense 申請タイミング
- 現在12記事。**20記事前後が目安**（あと8記事程度）
- 記事数が増えたら申請を検討

### 5. ワンオペ疲れ記事のリライト
- `wanope-tired-how-to-escape.md` に家事代行サービスの紹介セクションを追加予定
- ユーザーが実際に家事代行を試してから加筆する方針

### 6. GA4 + Search Console データ活用
- 「次は何書こう？」と聞かれたときにデータ連携して提案する機能
- Google Cloud API設定はまだ未実施

## 技術メモ

### 記事作成のルール
- frontmatter: `title` / `description` / `pubDate` / `category` / `tags` / `draft: false`
- ハイライト: `<mark>テキスト</mark>`（`==...==`は使わない）
- ファイル名は必ず `.md` 拡張子

### カテゴリ（5つ）
| カテゴリ名 | スラッグ |
|---|---|
| お金・キャリア | money-career |
| 地方移住・暮らし | local-life |
| 子育て・共働き | parenting |
| 食・卵・富山 | food |
| 健康・その他 | health |

### アフィリエイト管理
- `src/data/affiliates.json` で一元管理
- `status: "active"` のものだけAffCardとして表示される

## 個人情報ルール（重要）
- 氏名・会社名・社員番号・銀行口座情報は**絶対に使わない**
- 給与は丸めた概算のみ（「月収〇〇万円台」等）
- 社外公開物は上長確認が必要な旨をユーザーに伝える
