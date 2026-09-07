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

def is_frontloaded_payday(D: date) -> bool:
    """25日が土日の場合に前倒しされた給与日（23日または24日）かどうか"""
    if D.day not in (23, 24):
        return False
    intended_25 = date(D.year, D.month, 25)
    weekday_25 = intended_25.weekday()   # 0=月 … 5=土 6=日
    if weekday_25 == 5 and D.day == 24:          # 土曜→前日(金)=24日
        return True
    if weekday_25 == 6 and D.day in (23, 24):    # 日曜→2日前(金)=23日
        return True
    return False


def detect_cycle_from_csv(csv_path: Path) -> tuple[date, date, str]:
    """CSVの最古日付から25日締めサイクル（前月25日〜当月24日）を検出する"""
    df = pd.read_csv(csv_path, encoding='cp932')
    df['日付'] = pd.to_datetime(df['日付'])
    min_date = df['日付'].min().date()

    # MoneyForwardの「月の開始日=25日」設定に合わせる。
    # 25日以降開始 → 締め月は翌月、24日以前開始 → 締め月は当月
    if min_date.day >= 25:
        label_y = min_date.year + 1 if min_date.month == 12 else min_date.year
        label_m = 1 if min_date.month == 12 else min_date.month + 1
    else:
        label_y, label_m = min_date.year, min_date.month

    if label_m == 1:
        start = date(label_y - 1, 12, 25)
    else:
        start = date(label_y, label_m - 1, 25)
    end = date(label_y, label_m, 24)

    return start, end, f"{label_y}/{label_m:02d}"


# ================================
# カテゴリマッピング (MF大項目, MF中項目) → (費目, 詳細)
# ================================

CAT = {
    # 食費
    ('食費', '外食'):                   ('🍔 食費',       '外食'),
    ('食費', 'コンビニ'):                ('🍔 食費',       'コンビニ'),
    ('食費', 'スーパー'):                ('🍔 食費',       'スーパー'),
    ('食費', '食料品'):                  ('🍔 食費',       'スーパー'),
    # 日用品
    ('日用品', '日用品'):                ('🧹 日用品',     ''),
    ('日用品', 'その他日用品'):           ('🧹 日用品',     ''),
    # 水道・光熱費
    ('水道・光熱費', '電気代'):           ('🚰 水道光熱費', ''),
    ('水道・光熱費', 'ガス・灯油代'):      ('🚰 水道光熱費', ''),
    ('水道・光熱費', '水道代'):           ('🚰 水道光熱費', ''),
    # 通信費
    ('通信費', '携帯電話'):              ('🛜 通信費',     ''),
    ('通信費', 'インターネット'):          ('🛜 通信費',     ''),
    # 教養・教育
    ('教養・教育', 'アプリ・サブスク'):    ('📱 サブスク費', ''),
    ('教養・教育', '保育園・幼稚園'):      ('🎓 教養・教育', '保育園'),
    ('教養・教育', '新聞・雑誌'):         ('🎓 教養・教育', 'その他'),
    ('教養・教育', '塾'):                ('🎓 教養・教育', 'その他'),
    ('教養・教育', 'その他教養・教育'):    ('🎓 教養・教育', 'その他'),
    # 趣味・娯楽
    ('趣味・娯楽', '映画・音楽・ゲーム'): ('⛺️ 趣味・娯楽', ''),
    ('趣味・娯楽', '旅行'):              ('⛺️ 趣味・娯楽', '旅行'),
    ('趣味・娯楽', '畑用品'):            ('⛺️ 趣味・娯楽', ''),
    ('趣味・娯楽', 'アウトドア'):         ('⛺️ 趣味・娯楽', ''),
    ('趣味・娯楽', 'その他趣味・娯楽'):   ('⛺️ 趣味・娯楽', ''),
    # 交通費
    ('交通費', 'タクシー'):              ('🚃 交通費',     ''),
    ('交通費', '交通費'):                ('🚃 交通費',     ''),
    # 自動車
    ('自動車', 'ガソリン'):              ('🚙 自動車',     'ガソリン'),
    ('自動車', '駐車場'):                ('🚙 自動車',     '駐車場'),
    ('自動車', '道路料金'):              ('🚙 自動車',     'ガソリン'),   # ETC等
    ('自動車', '車両'):                  ('❗️ 特別な支出', ''),
    ('自動車', 'タイヤ交換'):             ('❗️ 特別な支出', ''),
    ('自動車', 'その他自動車'):           ('🚙 自動車',     'ガソリン'),
    # 衣服・美容
    ('衣服・美容', '衣服'):              ('👕 衣服・美容', ''),
    ('衣服・美容', '美容院・理髪'):       ('👕 衣服・美容', ''),
    ('衣服・美容', '美容品'):            ('👕 衣服・美容', ''),
    ('衣服・美容', 'クリーニング'):       ('👕 衣服・美容', ''),
    ('衣服・美容', '化粧品'):            ('👕 衣服・美容', ''),
    # 健康・医療
    ('健康・医療', '医療費'):            ('🏥 健康・医療', ''),
    ('健康・医療', '薬'):                ('🏥 健康・医療', ''),
    ('健康・医療', 'ボディケア'):         ('🏥 健康・医療', ''),
    ('健康・医療', 'フィットネス'):       ('🏥 健康・医療', ''),
    ('健康・医療', '歯科'):              ('🏥 健康・医療', ''),
    ('健康・医療', 'その他健康・医療'):    ('🏥 健康・医療', ''),
    # 交際費
    ('交際費', 'プレゼント代'):          ('☕️ 交際費',     ''),
    ('交際費', '交際費'):                ('☕️ 交際費',     ''),
    ('交際費', '冠婚葬祭'):              ('☕️ 交際費',     ''),
    # 住宅
    ('住宅', '家賃・地代'):              ('🏠 住宅',       '家賃'),
    ('住宅', '地震・火災保険'):           ('💊 保険',       ''),
    ('住宅', 'その他住宅'):              ('🏠 住宅',       '家賃'),   # MFで家賃がその他住宅になる場合も家賃扱い
    ('住宅', '修繕費'):                  ('❗️ 特別な支出', ''),
    ('住宅', '住宅設備'):                ('❗️ 特別な支出', ''),
    # 保険
    ('保険', '生命保険'):                ('💊 保険',       ''),
    ('保険', '住宅・火災保険'):           ('💊 保険',       ''),
    # 特別な支出
    ('特別な支出', 'おこずかい'):         ('💳 現金・カード', 'お小遣い'),   # 表記ゆれ
    ('特別な支出', 'おこづかい'):         ('💳 現金・カード', 'お小遣い'),
    ('特別な支出', 'その他特別な支出'):    ('❗️ 特別な支出', ''),
    ('特別な支出', '家具・家電'):         ('❗️ 特別な支出', ''),
    ('特別な支出', '年会費・手数料'):      ('❗️ 特別な支出', ''),
    ('特別な支出', '医療費'):             ('🏥 健康・医療', ''),
    ('特別な支出', '旅行'):              ('⛺️ 趣味・娯楽', '旅行'),
    # 税・社会保障
    ('税・社会保障', '所得税'):           ('💲 税・社会保障', ''),
    ('税・社会保障', '住民税'):           ('💲 税・社会保障', ''),
    ('税・社会保障', '社会保険料'):       ('💲 税・社会保障', ''),
    ('税・社会保障', '固定資産税'):       ('💲 税・社会保障', ''),
    ('税・社会保障', '自動車税'):         ('💲 税・社会保障', ''),
    ('税・社会保障', 'その他税'):         ('💲 税・社会保障', ''),
    ('税・社会保障', 'ふるさと納税'):     ('💲 税・社会保障', ''),
    # 現金・カード
    ('現金・カード', '使途不明金'):       ('💳 現金・カード', '使途不明金'),
    ('現金・カード', 'アドマック経費'):    ('__skip__',     ''),   # 事業経費
    # その他（NISA → 株式投資）※__nisa__は process_csv 内で積立枠/成長枠に分割
    ('その他', 'NISA'):                  ('__nisa__',     ''),
    ('その他', '叶佳NISA'):              ('💵 株式投資',   '叶佳'),
    # 収入
    ('収入', '給与'):                    ('💰 収入',       '給与'),
    ('収入', '賞与'):                    ('💰 収入',       '給与'),
    ('収入', '事業・副業'):              ('💰 収入',       '給与'),
    ('収入', '副業'):                    ('💰 収入',       '給与'),
    ('収入', '年金'):                    ('💰 収入',       '給与'),
    ('収入', '児童手当'):                ('💰 臨時収入',   '手当等'),
    ('収入', 'お祝い金'):                ('💰 臨時収入',   '手当等'),
    ('収入', 'その他入金'):              ('💰 臨時収入',   '手当等'),
    ('収入', '一時所得'):                ('💰 臨時収入',   '手当等'),
    ('収入', '売却・解約'):              ('💰 臨時収入',   '手当等'),
    ('収入', '還付金'):                  ('💰 臨時収入',   '手当等'),
}

# 大項目のみのフォールバック
CAT_MAJOR = {
    '食費':       ('🍔 食費',       'スーパー'),
    '日用品':     ('🧹 日用品',     ''),
    '水道・光熱費': ('🚰 水道光熱費', ''),
    '通信費':     ('🛜 通信費',     ''),
    '教養・教育':  ('🎓 教養・教育', 'その他'),
    '趣味・娯楽':  ('⛺️ 趣味・娯楽', ''),
    '交通費':     ('🚃 交通費',     ''),
    '自動車':     ('🚙 自動車',     'ガソリン'),
    '衣服・美容':  ('👕 衣服・美容', ''),
    '健康・医療':  ('🏥 健康・医療', ''),
    '交際費':     ('☕️ 交際費',     ''),
    '住宅':       ('🏠 住宅',       '家賃'),
    '保険':       ('💊 保険',       ''),
    '特別な支出':  ('❗️ 特別な支出', ''),
    '現金・カード': ('💳 現金・カード', '使途不明金'),
    'その他':     ('__skip__',     ''),
    '収入':       ('💰 収入',       '給与'),
    '税・社会保障': ('💲 税・社会保障', ''),
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
    # (費目, 詳細, 分類)  ※費目は list シート、分類は記入サンプルの表記に合わせる
    # ── 収入 ──────────────────────────────────────
    ('💰 収入',        '給与',      '収入・予算内'),
    ('💰 臨時収入',    '手当等',    '収入・予算内'),
    # ── 敵1: 毎月・固定費 ──────────────────────────
    ('🏠 住宅',        '家賃',      '1 毎月・固定'),
    ('🚰 水道光熱費',  '',          '1 毎月・固定'),
    ('🛜 通信費',      '',          '1 毎月・固定'),
    ('🎓 教養・教育',  '保育園',    '1 毎月・固定'),
    ('📱 サブスク費',  '',          '1 毎月・固定'),
    ('💊 保険',        '',          '1 毎月・固定'),
    ('🚙 自動車',      '駐車場',    '1 毎月・固定'),
    ('💳 現金・カード', 'お小遣い',  '1 毎月・固定'),
    # ── 敵2: 毎月・変動費 ──────────────────────────
    ('🍔 食費',        'スーパー',  '2 毎月・変動'),
    ('🍔 食費',        'コンビニ',  '2 毎月・変動'),
    ('🍔 食費',        '外食',      '2 毎月・変動'),
    ('🧹 日用品',      '',          '2 毎月・変動'),
    ('🚙 自動車',      'ガソリン',  '2 毎月・変動'),
    ('🚃 交通費',      '',          '2 毎月・変動'),
    ('👕 衣服・美容',  '',          '2 毎月・変動'),
    ('🏥 健康・医療',  '',          '2 毎月・変動'),
    ('💳 現金・カード', '使途不明金', '2 毎月・変動'),
    # ── 敵3: 不定期・固定費 ────────────────────────
    ('🎓 教養・教育',  'その他',    '3 不定・固定'),
    ('💲 税・社会保障', '',          '3 不定・固定'),
    # ── 敵4: 不定期・変動費 ────────────────────────
    ('⛺️ 趣味・娯楽',  '',          '4 不定・変動'),
    ('⛺️ 趣味・娯楽',  '旅行',      '4 不定・変動'),
    ('☕️ 交際費',      '',          '4 不定・変動'),
    ('❗️ 特別な支出',  '',          '4 不定・変動'),
    # ── 投資 ──────────────────────────────────────
    ('💵 株式投資',    '積立枠',    '投資'),
    ('💵 株式投資',    '成長枠',    '投資'),
    ('💵 株式投資',    '叶佳',      '投資'),
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

def process_csv(csv_path: Path, start: date, end: date,
                carry_in: dict | None = None) -> tuple[dict, dict]:
    """
    CSVを処理して (result, deferred) を返す。
      result   : {(費目, 詳細): 金額}  今月分
      deferred : {(費目, 詳細): 金額}  翌サイクルへ繰り越す前倒し給与
    carry_in があれば前サイクルから繰り越された給与を今月に加算する。
    """
    df = pd.read_csv(csv_path, encoding='cp932')
    df = df[df['計算対象'] == 1]
    df = df[df['振替'] == 0]
    df['日付'] = pd.to_datetime(df['日付'])
    df = df[(df['日付'].dt.date >= start) & (df['日付'].dt.date <= end)]

    result      = dict(carry_in) if carry_in else {}
    deferred    = {}
    nisa_amounts = []   # ('その他', 'NISA') エントリを一時収集して後で積立枠/成長枠に分割

    for _, row in df.iterrows():
        major  = str(row['大項目']).strip()
        minor  = str(row['中項目']).strip() if pd.notna(row['中項目']) else ''
        amount = float(row['金額（円）'])

        fee, detail = map_cat(major, minor)
        if fee == '__skip__':
            continue
        if fee == '__nisa__':
            nisa_amounts.append(abs(amount))
            continue
        if fee.startswith('❓'):
            print(f"  ⚠️ 未定義カテゴリ → 特別な支出として計上: {major}>{minor}  {row['内容']}  ¥{abs(amount):,.0f}")
            fee, detail = '❗️ 特別な支出', ''

        if major == '収入':
            if amount <= 0:
                continue
            key = (fee, detail)
            # 給与・賞与は25日前倒しチェック（MF中項目が給与/賞与のみ対象）
            if minor in ('給与', '賞与') and detail == '給与':
                D = row['日付'].date()
                if is_frontloaded_payday(D):
                    print(f"  📅 前倒し給与を翌サイクルへ繰り越し: {D}  ¥{amount:,.0f}")
                    deferred[key] = deferred.get(key, 0) + amount
                    continue
            result[key] = result.get(key, 0) + amount
        else:
            if amount >= 0:
                continue
            key = (fee, detail)
            result[key] = result.get(key, 0) + abs(amount)

    # NISA を積立枠（金額大）/ 成長枠（残り）に分割
    if nisa_amounts:
        nisa_sorted = sorted(nisa_amounts, reverse=True)
        result[('💵 株式投資', '積立枠')] = result.get(('💵 株式投資', '積立枠'), 0) + nisa_sorted[0]
        if len(nisa_sorted) > 1:
            result[('💵 株式投資', '成長枠')] = result.get(('💵 株式投資', '成長枠'), 0) + sum(nisa_sorted[1:])

    if carry_in:
        print(f"  💴 前サイクル繰り越し給与を加算: ¥{sum(carry_in.values()):,.0f}")

    print(f"\n【{start} 〜 {end} の集計】")
    for (fee, detail), amt in sorted(result.items()):
        print(f"  {(fee + ' ' + detail).strip():30s}  ¥{amt:>10,.0f}")
    if deferred:
        for (fee, detail), amt in deferred.items():
            print(f"  → 翌サイクル繰り越し: {(fee + ' ' + detail).strip()}  ¥{amt:,.0f}")

    return result, deferred

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
    """行構造を更新（A:C列を常に最新のSHEET_ROWSで上書き）"""
    print("スプレッドシートの行構造を更新中...")
    data = [[fee, detail, cls] for fee, detail, cls in SHEET_ROWS]
    ws.update(f'A5:C{4 + len(data)}', data)
    print(f"  {len(data)}行を書き込みました。")


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

    # 明細行（5行目〜）のみ。下部の集計表と費目名が衝突しないよう範囲を限定する
    detail_rows = ws.get(f'A5:B{4 + len(SHEET_ROWS)}')
    row_map = {}
    for i, row in enumerate(detail_rows):
        a = row[0].strip() if len(row) > 0 else ''
        b = row[1].strip() if len(row) > 1 else ''
        row_map[(a, b)] = i + 5

    col_letter = col_to_letter(col)
    print(f"\n{col_letter}列（{label}）を更新中...")

    # 書き込み前に列をクリア（古い実行のゴミ値を除去）
    clear_range = f'{col_letter}5:{col_letter}{4 + len(SHEET_ROWS)}'
    ws.batch_clear([clear_range])

    updates = []
    missing = []
    for (fee, detail), amount in result.items():
        key = (fee, detail)
        if key not in row_map:
            # 詳細違いは同じ費目の最初の行に寄せる
            key = next(((a, b) for (a, b) in row_map if a == fee), key)
        if key in row_map:
            cell = f'{col_letter}{row_map[key]}'
            updates.append({'range': cell, 'values': [[int(amount)]]})
        else:
            missing.append(f'{fee} {detail}'.strip())

    if missing:
        print(f"  ⚠️ シートに行が無く転記できませんでした: {', '.join(missing)}")

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

CARRY_FILE = Path(__file__).parent / 'carry.json'


def load_carry() -> dict:
    """前回繰り越し給与を carry.json から読み込む"""
    import json
    if not CARRY_FILE.exists():
        return {}
    with open(CARRY_FILE, encoding='utf-8') as f:
        raw = json.load(f)
    # JSON のキーは文字列なので tuple に戻す: "fee|||detail" → (fee, detail)
    return {tuple(k.split('|||')): v for k, v in raw.items()}


def save_carry(carry: dict):
    """繰り越し給与を carry.json に保存する"""
    import json
    raw = {'|||'.join(k): v for k, v in carry.items()}
    with open(CARRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)


def main():
    print("=" * 50)
    print(" MoneyForward CSV → Google Sheets 転記")
    print("=" * 50)

    args = sys.argv[1:]

    if not args:
        print("\n使い方: python main.py CSV.csv")
        print("\n前月に25日前倒し給与があった場合は carry.json に自動保存され")
        print("次回実行時に自動で翌月へ繰り越されます。")
        sys.exit(0)

    csv_paths = []
    for a in args:
        p = Path(a)
        if not p.exists():
            print(f"❌ ファイルが見つかりません: {p}")
            sys.exit(1)
        csv_paths.append(p)

    # 時系列順にソート
    csv_paths.sort(key=lambda p: detect_cycle_from_csv(p)[2])

    # 前回の繰り越しを読み込む
    carry = load_carry()
    if carry:
        print(f"\n📂 carry.json から前月繰り越し給与を読み込み: ¥{sum(carry.values()):,.0f}")

    for csv_path in csv_paths:
        print(f"\nCSV: {csv_path.name}")
        start, end, label = detect_cycle_from_csv(csv_path)
        label_y = int(label.split('/')[0])
        label_m = int(label.split('/')[1])

        print(f"対象サイクル : {label}  ({start} 〜 {end})")
        check_unmapped(csv_path)

        result, carry = process_csv(csv_path, start, end, carry_in=carry)
        update_sheet(result, label_y, label_m, label)

    # 繰り越しを保存（翌月の実行に引き継ぐ）
    if carry:
        save_carry(carry)
        print(f"\n💾 carry.json に繰り越し給与を保存: ¥{sum(carry.values()):,.0f}")
        print("   翌月のCSVを実行すると自動で引き継がれます。")
    else:
        # 繰り越しなし → ファイルを削除してクリア
        if CARRY_FILE.exists():
            CARRY_FILE.unlink()
            print("\n✅ 繰り越し給与なし（carry.json をクリア）")


if __name__ == '__main__':
    main()
