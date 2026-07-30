import affiliatesData from '../data/affiliates.json';

export interface AffBanner {
  src: string;
  width?: number;
  height?: number;
  /** ASPの表示回数計測用ピクセル(あれば)。1x1の透明画像として出力される */
  impressionPixel?: string;
}

export interface AffItem {
  label: string;
  desc?: string;
  asp?: string;
  url?: string;
  fallbackUrl?: string;
  reward?: string;
  startedAt?: string;
  endsAt?: string;
  status: 'active' | 'paused' | 'ended';
  note?: string;
  /** ASP提供のバナー画像。あればテキストカードの代わりにこちらを表示 */
  banner?: AffBanner;
}

export interface ResolvedAff {
  found: boolean;
  label: string;
  desc?: string;
  href: string | null;
  rel: string;
  live: boolean;
  banner?: AffBanner;
}

const master = affiliatesData as Record<string, AffItem>;

function isExpired(item: AffItem): boolean {
  if (!item.endsAt) return false;
  const today = new Date().toISOString().slice(0, 10);
  return item.endsAt < today;
}

/** ビルド時点で実際にアフィリエイトリンクとして案内してよいか */
function isLive(item: AffItem): boolean {
  return item.status === 'active' && !isExpired(item) && !!item.url;
}

/**
 * 案件IDから表示用データを解決する。
 * - 生きている案件 → 案件URL（sponsored）
 * - 停止/終了/失効した案件 → fallbackUrl があればそちらへ（通常リンク）、なければリンクなし
 * - 未登録のID → found: false
 */
export function resolveAff(id: string, labelOverride?: string): ResolvedAff {
  const item = master[id];

  if (!item) {
    return {
      found: false,
      label: labelOverride ?? id,
      href: null,
      rel: 'noopener',
      live: false,
    };
  }

  const live = isLive(item);
  const href = live ? item.url! : (item.fallbackUrl || null);

  return {
    found: true,
    label: labelOverride ?? item.label,
    desc: item.desc,
    href,
    rel: live ? 'sponsored noopener' : 'noopener',
    live,
    // バナーはASP提供の生きたリンクとセットの創作物なので、live時のみ出す
    banner: live ? item.banner : undefined,
  };
}

/** pr: true か、affiliates が1件以上指定されていれば広告表記が必要 */
export function needsPrNotice(frontmatter: { pr?: boolean; affiliates?: string[] }): boolean {
  return !!frontmatter.pr || !!(frontmatter.affiliates && frontmatter.affiliates.length > 0);
}
