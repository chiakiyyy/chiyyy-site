"""
MoneyForward ME → Google Sheets 転記
使い方: python main.py ダウンロードしたCSV.csv
"""

import os
import sys
from datetime import date
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

# ================================
# 設定
# ================================

SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', '1NaJg34QU-hCuW4Ujxrg4c2357tpbyWsPoEOVgLLSkCA')
SHEET_NAME     = '実績管理シート'

# ================================
# 日付計算
# ================================

def detect_cycle_from_csv(csv_path: Path) -> tuple[date, date, str]:
    """CSVの最新日付から25日締めサイクルを自動検出する"""
    df = pd.read_csv(csv_path, encoding='cp932')
    df['日付'] = pd.to_datetime(df['日付'])
    max_date = df['日付'].max().date()

    # 25日以前 → 当月締め、26日以降 → 翌月締め
    if max_date.day <= 25:
        label_y, label_m = max_date.year, max_date.month
    else:
        if max_date.month == 12:
            label_y, label_m = max_date.year + 1, 1
        else:
            label_y, label_m = max_date.year, max_date.month + 1

    if label_m == 1:
        start = date(label_y - 1, 12, 26)
    else:
        start = date(label_y, label_m - 1, 26)
    end = date(label_y, label_m, 25)

    return start, end, f"{label_y}/{label_m:02d}"


# ================================
# カテゴリマッピング (MF大項目, MF中項目) → (費目, 詳細)
# ================================

CAT = {
    # 食費
    ('食費', '外食'):                   ('🍔食費',       '外食'),
    ('食費', 'コンビニ'):                ('🍔食費',       'コンビニ'),
    ('食費', 'スーパー'):                ('🍔食費',       'スーパー'),
    ('食費', '食料品'):                  ('🍔食費',       'スーパー'),
    # 日用品
    ('日用品', '日用品'):                ('🧹日用品',     ''),
    ('日用品', 'その他日用品'):           ('🧹日用品',     ''),
    # 水道・光熱費
    ('水道・光熱費', '電気代'):           ('🚰水道光熱費', ''),
    ('水道・光熱費', 'ガス・灯油代'):      ('🚰水道光熱費', ''),
    ('水道・光熱費', '水道代'):           ('🚰水道光熱費', ''),
    # 通信費
    ('通信費', '携帯電話'):              ('🛜通信費',     ''),
    ('通信費', 'インターネット'):          ('🛜通信費',     ''),
    # 教養・教育
    ('教養・教育', 'アプリ・サブスク'):    ('🎓教養・教育', 'サブスク'),
    ('教養・教育', '保育園・幼稚園'):      ('🎓教養・教育', '保育園'),
    ('教養・教育', '新聞・雑誌'):         ('🎓教養・教育', 'その他'),
    ('教養・教育', '塾'):                ('🎓教養・教育', 'その他'),
    ('教養・教育', 'その他教養・教育'):    ('🎓教養・教育', 'その他'),
    # 趣味・娯楽
    ('趣味・娯楽', '映画・音楽・ゲーム'): ('⛺️趣味・娯楽', ''),
    ('趣味・娯楽', '旅行'):              ('✈️旅行',       ''),
    ('趣味・娯楽', '畑用品'):            ('⛺️趣味・娯楽', ''),
    ('趣味・娯楽', 'アウトドア'):         ('⛺️趣味・娯楽', ''),
    ('趣味・娯楽', 'その他趣味・娯楽'):   ('⛺️趣味・娯楽', ''),
    # 交通費
    ('交通費', 'タクシー'):              ('🚃交通費',     ''),
    ('交通費', '交通費'):                ('🚃交通費',     ''),
    # 自動車
    ('自動車', 'ガソリン'):              ('🚙自動車',     'ガソリン'),
    ('自動車', '駐車場'):                ('🚙自動車',     '駐車場'),
    ('自動車', '道路料金'):              ('🚙自動車',     'ガソリン'),   # ETC等
    ('自動車', '車両'):                  ('❗️特別な支出', ''),
    ('自動車', 'タイヤ交換'):             ('❗️特別な支出', ''),
    ('自動車', 'その他自動車'):           ('🚙自動車',     'ガソリン'),
    # 衣服・美容
    ('衣服・美容', '衣服'):              ('👕衣服・美容', ''),
    ('衣服・美容', '美容院・理髪'):       ('👕衣服・美容', ''),
    ('衣服・美容', '美容品'):            ('👕衣服・美容', ''),
    ('衣服・美容', 'クリーニング'):       ('👕衣服・美容', ''),
    ('衣服・美容', '化粧品'):            ('👕衣服・美容', ''),
    # 健康・医療
    ('健康・医療', '医療費'):            ('🏥健康・医療', ''),
    ('健康・医療', '薬'):                ('🏥健康・医療', ''),
    ('健康・医療', 'ボディケア'):         ('🏥健康・医療', ''),
    ('健康・医療', 'フィットネス'):       ('🏥健康・医療', ''),
    ('健康・医療', '歯科'):              ('🏥健康・医療', ''),
    ('健康・医療', 'その他健康・医療'):    ('🏥健康・医療', ''),
    # 交際費
    ('交際費', 'プレゼント代'):          ('☕️交際費',     ''),
    ('交際費', '交際費'):                ('☕️交際費',     ''),
    ('交際費', '冠婚葬祭'):              ('☕️交際費',     ''),
    # 住宅
    ('住宅', '家賃・地代'):              ('🏠住宅',       '家賃'),
    ('住宅', '地震・火災保険'):           ('🏡保険',       ''),
    ('住宅', 'その他住宅'):              ('❗️特別な支出', ''),
    # 保険
    ('保険', '生命保険'):                ('🏡保険',       ''),
    ('保険', '住宅・火災保険'):           ('🏡保険',       ''),
    # 特別な支出
    ('特別な支出', 'おこずかい'):         ('👨おこづかい', ''),   # 表記ゆれ
    ('特別な支出', 'おこづかい'):         ('👨おこづかい', ''),
    ('特別な支出', 'その他特別な支出'):    ('❗️特別な支出', ''),
    ('特別な支出', '家具・家電'):         ('❗️特別な支出', ''),
    ('特別な支出', '年会費・手数料'):      ('❗️特別な支出', ''),
    # 現金・カード
    ('現金・カード', '使途不明金'):       ('💳現金・カード', ''),
    ('現金・カード', 'アドマック経費'):    ('__skip__',     ''),   # 事業経費
    # その他（NISA → スキップ）
    ('その他', 'NISA'):                  ('__skip__',     ''),
    ('その他', '叶佳NISA'):              ('__skip__',     ''),
    # 収入
    ('収入', '給与'):                    ('💰収入',       '給与'),
    ('収入', '事業・副業'):              ('💰収入',       '給与'),
    ('収入', '児童手当'):                ('💰収入',       '手当等'),
    ('収入', 'お祝い金'):                ('💰収入',       '手当等'),
    ('収入', 'その他入金'):              ('💰収入',       '手当等'),
    ('収入', '一時所得'):                ('💰収入',       '手当等'),
}

# 大項目のみのフォールバック
CAT_MAJOR = {
    '食費':       ('🍔食費',       '外食'),
    '日用品':     ('🧹日用品',     ''),
    '水道・光熱費': ('🚰水道光熱費', ''),
    '通信費':     ('🛜通信費',     ''),
    '教養・教育':  ('🎓教養・教育', 'その他'),
    '趣味・娯楽':  ('⛺️趣味・娯楽', ''),
    '交通費':     ('🚃交通費',     ''),
    '自動車':     ('🚙自動車',     'ガソリン'),
    '衣服・美容':  ('👕衣服・美容', ''),
    '健康・医療':  ('🏥健康・医療', ''),
    '交際費':     ('☕️交際費',     ''),
    '住宅':       ('🏠住宅',       ''),
    '保険':       ('🏡保険',       ''),
    '特別な支出':  ('❗️特別な支出', ''),
    '現金・カード': ('💳現金・カード', ''),
    'その他':     ('__skip__',     ''),
    '収入':       ('💰収入',       '給与'),
    '税・社会保障': ('💲税・社会保障', ''),
}


def map_cat(major: str, minor: str) -> tuple[str, str]:
    key = (major, minor)
    if key in CAT:
        return CAT[key]
    if (major, '') in CAT:
        return CAT[(major, '')]
    if major in CAT_MAJOR:
        return CAT_MAJOR[major]
    return (f'❓{major}', minor)

# ================================
# スプレッドシート行構造（初期化用）
# ================================

SHEET_ROWS = [
    # (費目, 詳細, 分類)  ※分類はサンプルシートの表記に合わせる
    # ── 収入 ──────────────────────────────────────
    ('💰収入',        '給与',    '収入・予算内'),
    ('💰収入',        '手当等',  '収入・予算内'),
    # ── 敵1: 毎月・固定費 ──────────────────────────
    ('🏠住宅',       '家賃',    '1毎月・固定'),
    ('🚰水道光熱費',  '',        '1毎月・固定'),
    ('🛜通信費',      '',        '1毎月・固定'),
    ('🎓教養・教育',  '保育園',  '1毎月・固定'),
    ('🎓教養・教育',  'サブスク', '1毎月・固定'),
    ('🏡保険',        '',        '1毎月・固定'),
    ('💲税・社会保障', '',        '1毎月・固定'),
    # ── 敵2: 毎月・変動費 ──────────────────────────
    ('🍔食費',        '外食',    '2毎月・変動'),
    ('🍔食費',        'コンビニ', '2毎月・変動'),
    ('🍔食費',        'スーパー', '2毎月・変動'),
    ('🧹日用品',      '',        '2毎月・変動'),
    ('🚙自動車',      'ガソリン', '2毎月・変動'),
    ('🚙自動車',      '駐車場',  '2毎月・変動'),
    ('🚃交通費',      '',        '2毎月・変動'),
    ('👕衣服・美容',  '',        '2毎月・変動'),
    ('🏥健康・医療',  '',        '2毎月・変動'),
    ('👨おこづかい',  '',        '2毎月・変動'),
    ('💳現金・カード', '',        '2毎月・変動'),
    # ── 敵3: 不定期・固定費 ────────────────────────
    ('🎓教養・教育',  'その他',  '3不定・固定'),
    # ── 敵4: 不定期・変動費 ────────────────────────
    ('⛺️趣味・娯楽',  '',        '4不定・変動'),
    ('✈️旅行',        '',        '4不定・変動'),
    ('☕️交際費',      '',        '4不定・変動'),
    ('❗️特別な支出',  '',        '4不定・変動'),
]

# ================================
# 未分類チェック
# ================================

def check_unmapped(csv_path: Path):
    """未分類・未定義カテゴリの取引を一覧表示する"""
    df = pd.read_csv(csv_path, encoding='cp932')
    df = df[df['計算対象'] == 1]
    df = df[df['振替'] == 0]

    issues = []
    for _, row in df.iterrows():
        major = str(row['大項目']).strip()
        minor = str(row['中項目']).strip() if str(row['中項目']) != 'nan' else ''
        if major == '未分類':
            issues.append(f"  [未分類] {row['日付']}  {row['内容']}  ¥{abs(float(row['金額（円）'])):,.0f}")
        elif map_cat(major, minor)[0].startswith('❓'):
            issues.append(f"  [未定義] {major}>{minor}  {row['内容']}")

    if issues:
        print(f"\n⚠️ 要確認 {len(issues)}件（MoneyForwardでカテゴリ設定を）:")
        for s in issues:
            print(s)
    else:
        print("  カテゴリ確認OK ✅")

# ================================
# CSV 処理
# ================================

def process_csv(csv_path: Path, start: date, end: date) -> dict:
    """CSVを処理して {(費目, 詳細): 金額} を返す"""
    df = pd.read_csv(csv_path, encoding='cp932')
    df = df[df['計算対象'] == 1]
    df = df[df['振替'] == 0]
    df['日付'] = pd.to_datetime(df['日付'])
    df = df[(df['日付'].dt.date >= start) & (df['日付'].dt.date <= end)]

    result = {}
    for _, row in df.iterrows():
        major  = str(row['大項目']).strip()
        minor  = str(row['中項目']).strip() if pd.notna(row['中項目']) else ''
        amount = float(row['金額（円）'])

        fee, detail = map_cat(major, minor)
        if fee == '__skip__':
            continue

        if major == '収入':
            # 収入はプラス金額をそのまま集計
            key = (fee, detail)
            result[key] = result.get(key, 0) + amount
        else:
            # 支出はマイナス金額のみ（プラスは振込など）
            if amount >= 0:
                continue
            key = (fee, detail)
            result[key] = result.get(key, 0) + abs(amount)

    print(f"\n【{start} 〜 {end} の集計】")
    for (fee, detail), amt in sorted(result.items()):
        print(f"  {(fee + ' ' + detail).strip():30s}  ¥{amt:>10,.0f}")

    return result

# ================================
# Google Sheets 更新
# ================================

def get_gs_client():
    """Google Sheets クライアント（サービスアカウント）"""
    import gspread

    here    = Path(__file__).parent
    key_p   = here / 'service_account.json'

    if not key_p.exists():
        print("❌ service_account.json が見つかりません。")
        print(f"   Google Cloud Console でサービスアカウントのJSONキーを作成し")
        print(f"   {key_p} に保存してください。")
        sys.exit(1)

    return gspread.service_account(filename=str(key_p))


def init_sheet(ws):
    """行構造を初期化（A5が空のときのみ）"""
    if ws.cell(5, 1).value:
        return
    print("スプレッドシートの行構造を初期化中...")
    data = [[fee, detail, cls] for fee, detail, cls in SHEET_ROWS]
    ws.update(f'A5:C{4 + len(data)}', data)
    print(f"  {len(data)}行を初期化しました。")


def find_col_for_month(ws, year: int, month: int) -> int | None:
    """シートのヘッダー行（4行目）を読み、対象年月の列番号を返す"""
    import re
    row4 = ws.row_values(4)
    for i, val in enumerate(row4, 1):
        m = re.match(r'(\d{4})[./](\d{1,2})$', val.strip())
        if m and int(m.group(1)) == year and int(m.group(2)) == month:
            return i
    return None


def col_to_letter(col: int) -> str:
    """列番号 → アルファベット（例: 5→E, 27→AA）"""
    result = ''
    while col:
        col, rem = divmod(col - 1, 26)
        result = chr(65 + rem) + result
    return result


def update_sheet(result: dict, year: int, month: int, label: str):
    gc = get_gs_client()
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(SHEET_NAME)

    init_sheet(ws)

    col = find_col_for_month(ws, year, month)
    if col is None:
        print(f"⚠️ シートに {label} の列が見つかりません。")
        print(f"   スプレッドシートの開始月を確認してください。")
        return

    a_vals = ws.col_values(1)
    b_vals = ws.col_values(2)
    row_map = {}
    for i, (a, b) in enumerate(zip(a_vals, b_vals)):
        row_map[(a.strip(), b.strip())] = i + 1

    col_letter = col_to_letter(col)
    print(f"\n{col_letter}列（{label}）を更新中...")

    updates = []
    for (fee, detail), amount in result.items():
        key = (fee, detail)
        if key not in row_map:
            for (a, b), r in row_map.items():
                if a == fee and b == '':
                    key = (a, b)
                    break
        if key in row_map:
            cell = f'{col_letter}{row_map[key]}'
            updates.append({'range': cell, 'values': [[int(amount)]]})

    if updates:
        ws.batch_update([{'range': u['range'], 'values': u['values']} for u in updates])
        print(f"  {len(updates)}件のセルを更新しました。")
    else:
        print("  更新対象なし。")

    print(f"\n✅ 完了！")
    print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")

# ================================
# エントリポイント
# ================================

def main():
    print("=" * 50)
    print(" MoneyForward CSV → Google Sheets 転記")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\n使い方: python main.py ダウンロードしたCSV.csv")
        print("\nMoneyForwardからCSVをダウンロードして渡してください。")
        print("月は自動で検出します（25日締め）。")
        sys.exit(0)

    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"❌ ファイルが見つかりません: {csv_path}")
        sys.exit(1)

    print(f"\nCSV: {csv_path.name}")
    start, end, label = detect_cycle_from_csv(csv_path)

    label_y = int(label.split('/')[0])
    label_m = int(label.split('/')[1])

    print(f"対象サイクル : {label}  ({start} 〜 {end})")

    check_unmapped(csv_path)

    result = process_csv(csv_path, start, end)
    update_sheet(result, label_y, label_m, label)


if __name__ == '__main__':
    main()
