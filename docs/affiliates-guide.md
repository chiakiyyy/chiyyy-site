# アフィリエイトリンク運用ガイド

記事のMarkdown本文にリンクを直接書かず、frontmatterに案件IDを書くだけでアフィリエイトリンクを掲載できる仕組みです。案件終了時は案件マスタ1箇所を書き換えるだけで、全記事のリンクが自動的に外れます。

## 1. 案件を登録する

`src/data/affiliates.json` に案件を1件追加します。

```json
"case-id": {
  "label": "商品名・サービス名",
  "desc": "1〜2行の説明（省略可）",
  "asp": "A8",
  "url": "https://実際のアフィリエイトリンク",
  "fallbackUrl": "https://公式サイトなど通常リンク（省略可）",
  "reward": "報酬額や料率のメモ（表示はされません）",
  "startedAt": "2026-07-29",
  "endsAt": "",
  "status": "active",
  "note": "自分用のメモ（表示はされません）"
}
```

- `status`: `active`（掲載中） / `paused`（一時停止） / `ended`（終了）
- `endsAt`: 終了予定日（`YYYY-MM-DD`）。過ぎると次回ビルドから自動的に非掲載扱いになります（`status`を書き換える前でも失効します）
- `fallbackUrl`: 案件が終了・失効したときに代わりに案内するリンク。空にするとリンクごと消えます

サンプルとして `oisix-otameshi`（掲載中）・`hario-kettle`（掲載中）・`sample-ended`（終了済み）の3件が入っています。実際の案件に差し替えるか、不要なら削除してください。

### バナー画像を使う場合

ASPから発行されたバナー画像（ロゴ等）をテキストカードの代わりに表示したいときは、`banner`を追加します。

```json
"case-id": {
  ...,
  "banner": {
    "src": "https://ASPが発行したバナー画像のURL",
    "width": 600,
    "height": 600,
    "impressionPixel": "https://ASPが発行した表示回数計測用の1x1画像URL（あれば）"
  }
}
```

`banner`があると、`AffCard`は文字のカードではなくこの画像を表示します（クリックで案件URLへ）。`impressionPixel`を入れておくと、ASP側の表示回数集計にも反映されます（成果・報酬の判定には影響しません）。`banner`を書かなければ今まで通りテキストカードのままです。

## 2. 記事に紐付ける

記事のfrontmatターに `affiliates` と `pr` を追加するだけです。本文は今まで通り書けます。

```yaml
---
title: "サンプル記事"
description: "..."
pubDate: 2026-07-29
category: "くらし"
affiliates: ["oisix-otameshi"]
pr: true
---
```

- `affiliates`: 掲載したい案件IDの配列。複数指定可
- `pr: true`: 広告表記（PRバッジ）を出す。`affiliates` を1件でも指定していれば `pr: true` も忘れずに（点検スクリプトが検知します）

指定した案件は、記事本文の**末尾**にカード形式で自動的に並びます。

## 2.5 本文中の好きな位置に差し込みたい場合（`.mdx`）

記事ファイルの拡張子を `.md` ではなく `.mdx` にすると、本文中の好きな場所にリンクやカードを差し込めます。

```mdx
---
title: "サンプル記事"
affiliates: ["type-women-agent"]
pr: true
---

import AffLink from '../../components/AffLink.astro';
import AffCard from '../../components/AffCard.astro';

前職で悩んでいた頃、<AffLink id="type-women-agent" /> に登録してみました。

（本文の途中で、バナーやカードを大きく見せたいとき）

<AffCard id="type-women-agent" />

続きの本文...
```

- `<AffLink id="案件ID" />`: 文中の短いテキストリンク。案件名がそのままリンクテキストになる（`label="..."` で上書き可）。掲載中のリンクには自動で小さな「PR」マークが付く
- `<AffCard id="案件ID" />`: カード（またはバナー画像）を、本文中の好きな位置に差し込む。frontmatterの`affiliates`で末尾に出るものと同じ部品

`.md`のまま（frontmatterに`affiliates`を書くだけ）でも今まで通り使えます。本文に手を入れたくない記事は`.md`のままで問題ありません。

## 3. 案件を終了する

`src/data/affiliates.json` の該当案件の `status` を `"ended"` に変更してビルドし直すだけです。この案件を参照している全記事から、そのアフィリエイトリンクが自動的に外れます。`fallbackUrl` があれば通常リンクに、なければリンク自体が消えます（コピーはそのまま残ります）。

## 4. 定期点検

```bash
npm run check:affiliates          # オフライン点検（必須項目・差し替え漏れ・広告表記漏れなど）
npm run check:affiliates:fetch    # 上記に加えて、実際にリンク先へ接続確認
```

チェックする内容:

1. 案件マスタの必須項目・URLの差し替え漏れ（サンプルURLが残っていないか）
2. 終了日を過ぎた案件／30日以内に終了予定の案件
3. 記事が参照している案件IDがマスタに実在するか
4. マスタにあるがどの記事にも使われていない案件
5. `affiliates` を指定した記事に `pr: true` があるか（広告表記漏れ）
6. `--fetch` 時: リンク切れの可能性（HTTPエラー）

「要修正」が1件でもあると終了コード1で終わります。CIに組み込みたい場合はこのコマンドをワークフローに追加してください（現時点では `npm run build` には組み込んでいません＝サンプルURLが残っていてもデプロイ自体は止まりません）。

## 5. 表示の仕組み（内部構成）

| ファイル | 役割 |
|---|---|
| `src/data/affiliates.json` | 案件マスタ（唯一の真実源） |
| `src/lib/affiliates.ts` | `resolveAff(id)` / `needsPrNotice(frontmatter)` の実体。生死判定・フォールバック解決 |
| `src/components/PrNotice.astro` | 広告表記バッジ。記事本文より上に自動表示 |
| `src/components/AffCard.astro` | 記事末尾に自動で並ぶ、案件1件ぶんのカード |
| `src/components/AffLink.astro` | 本文中インライン用（`.mdx`記事で使用） |
| `scripts/check-affiliates.mjs` | 定期点検スクリプト |
| `src/pages/blog/[slug].astro` | `PrNotice` と `AffCard` を実際に記事ページへ組み込んでいる箇所 |

## 6. 今回やっていないこと（今後必要になったら）

- **LinkSwitch（もしもアフィリエイト等の自動リンク化タグ）の導入**: ASPアカウント固有の埋め込みタグが必要なため、今回は組み込んでいません。導入する場合は `src/layouts/Layout.astro` の `</body>` 直前にASP指定のスクリプトタグを追加してください。導入後は、本文中の通常リンクも広告リンク化される可能性があるため、外部サイトへ直接リンクする記事では `pr: true` を明示してください。
- **複数サービスの比較表コンポーネント**: 転職エージェント等、同テーマの案件が複数貯まってきたら追加を検討。
- **台帳Excel（案件ごとの累計額・承認率の集計）**: 別途ご要望があれば作成します。

## 7. 公開前の注意

- 本番反映前に `npm run build` が通ることを確認してください（今回のセッションでも確認済みです）
- 広告表記の要否・文言（景品表示法の指定告示）や各ASP規約上の必要表記については、最終的な適否をご自身でご確認ください
- 生成したコード・文面は参考情報です。最終判断と公開の責任は利用者にあります。社外公開物（Webサイト）にあたるため、公開前に上長確認をお願いします
