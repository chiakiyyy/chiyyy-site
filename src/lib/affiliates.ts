import affiliatesData from '../data/affiliates.json';

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
}

export interface ResolvedAff {
  found: boolean;
  label: string;
  desc?: string;
  href: string | null;
  rel: string;
  live: boolean;
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
  };
}

/** pr: true か、affiliates が1件以上指定されていれば広告表記が必要 */
export function needsPrNotice(frontmatter: { pr?: boolean; affiliates?: string[] }): boolean {
  return !!frontmatter.pr || !!(frontmatter.affiliates && frontmatter.affiliates.length > 0);
}
