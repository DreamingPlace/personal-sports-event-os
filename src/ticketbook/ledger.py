"""Inventory: one running ledger per session × tier, plus the checks that keep it honest."""
from __future__ import annotations

from decimal import ROUND_FLOOR, Decimal

from .model import BUCKET_KINDS, BookError, bucket_qty, count, index, money, price, product_sessions, round_covers, seats, tier_codes

LINES = ('seats', 'hold', 'sellable', 'comp', 'priority', 'reserve', 'product', 'public', 'sold', 'left')
LINE_NAMES = {'seats': '总座席', 'hold': '功能占用', 'sellable': '可售座席', 'comp': '权益/赠票', 'priority': '优先购',
              'reserve': '预留', 'product': '通票/套票', 'public': '公开销售', 'sold': '公开已售', 'left': '剩余'}


def problem(level: str, where: str, message: str) -> dict:
    return {'level': level, 'where': where, 'message': message}


def session_tier(book: dict, session: dict, tier: str) -> dict:
    """The ledger for one session × tier, with each bucket's share listed by name."""
    row = {line: 0 for line in LINES}
    row['seats'] = seats(book, session['layout'], tier)
    row['by_bucket'] = {}
    for bucket in book['buckets']:
        qty = bucket_qty(bucket, session, tier)
        if qty:
            row[bucket['kind']] += qty
            row['by_bucket'][bucket['id']] = qty
    for product in book['products']:
        if product['tier'] == tier and session in product_sessions(book, product):
            row['product'] += count(product['quota'])
    row['sellable'] = row['seats'] - row['hold']
    row['public'] = row['sellable'] - row['comp'] - row['priority'] - row['reserve'] - row['product']
    row['by_round'] = {}
    for rnd in book['rounds']:
        sold = count(book['sales'].get(rnd['code'], {}).get(session['code'], {}).get(tier))
        row['by_round'][rnd['code']] = sold
        row['sold'] += sold
    row['left'] = row['public'] - row['sold']
    p = price(book, session['band'], tier)
    row['price'] = None if p is None else str(p)
    return row


def release_plan(book: dict, session: dict, tier: str, public: int) -> dict:
    """Seats each sale round puts on sale for one session × tier: the round's % for that tier, if the round covers the session."""
    plan, used = {}, 0
    for rnd in book['rounds']:
        pct = rnd['share'].get(tier) if round_covers(rnd, session) else None
        if pct in (None, ''):
            plan[rnd['code']] = 0
            continue
        qty = int((Decimal(public) * money(pct) / 100).to_integral_value(ROUND_FLOOR))
        qty = max(0, min(qty, public - used))
        plan[rnd['code']] = qty
        used += qty
    return plan


def compute(book: dict) -> dict:
    """Ledger for every session × tier, per-session and event totals, and all problems found."""
    tiers = tier_codes(book)
    problems = check_structure(book)
    sessions = []
    totals = {line: 0 for line in LINES}
    for s in book['sessions']:
        rows = {t: session_tier(book, s, t) for t in tiers}
        sum_row = {line: sum(r[line] for r in rows.values()) for line in LINES}
        public_by_tier = {t: rows[t]['public'] for t in tiers}
        plan = {t: release_plan(book, s, t, max(0, public_by_tier[t])) for t in tiers}
        face = sum((money(r['price']) * (r['public'] + r['priority'] + r['reserve']) for r in rows.values() if r['price'] is not None), Decimal(0))
        sessions.append({'code': s['code'], 'date': s['date'], 'start': s['start'], 'band': s['band'], 'china': s['china'],
                         'tiers': rows, 'total': sum_row, 'release_plan': plan, 'face_value': str(face)})
        for line in LINES:
            totals[line] += sum_row[line]
        problems += check_session(book, s, rows)
    problems += check_rounds(book)
    return {'tiers': tiers, 'sessions': sessions, 'totals': totals, 'problems': problems,
            'ok': not any(p['level'] == 'error' for p in problems)}


def check_structure(book: dict) -> list[dict]:
    out = []
    tiers, bands, layouts = index(book['tiers']), index(book['bands']), index(book['layouts'])
    for name, items in (('票档', book['tiers']), ('比赛阶段', book['bands']), ('座席布局', book['layouts']), ('场次', book['sessions'])):
        codes = [i['code'] for i in items]
        for code in sorted({c for c in codes if codes.count(c) > 1}):
            out.append(problem('error', code, f'{name}代码重复：{code}'))
    for t in book['tiers']:
        if t.get('blocked_of') and t['blocked_of'] not in tiers:
            out.append(problem('error', t['code'], f'遮挡票档 {t["code"]} 的原票档 {t["blocked_of"]} 不存在'))
    for s in book['sessions']:
        if s['band'] not in bands:
            out.append(problem('error', s['code'], f'{s["code"]} 的比赛阶段 {s["band"]} 不存在'))
        if s['layout'] not in layouts:
            out.append(problem('error', s['code'], f'{s["code"]} 的座席布局 {s["layout"]} 不存在'))
    for b in book['buckets']:
        if b['kind'] not in BUCKET_KINDS:
            out.append(problem('error', b['name'], f'分配类别未知：{b["kind"]}'))
    for p in book['products']:
        if p['tier'] not in tiers:
            out.append(problem('error', p['name'], f'{p["name"]} 的票档 {p["tier"]} 不存在'))
    return out


def check_session(book: dict, s: dict, rows: dict) -> list[dict]:
    out = []
    code = s['code']
    names = {t['code']: t['name'] for t in book['tiers']}
    for tier, r in rows.items():
        where = f'{code} {names.get(tier, tier)}'
        if r['sellable'] < 0:
            out.append(problem('error', where, f'{where} 功能占用超出总座席 {-r["sellable"]} 张'))
        elif r['public'] < 0:
            out.append(problem('error', where, f'{where} 分配超出可售座席 {-r["public"]} 张'))
        if r['sold'] > max(r['public'], 0):
            out.append(problem('error', where, f'{where} 已售 {r["sold"]} 张，超过公开销售 {max(r["public"], 0)} 张'))
        if r['seats'] and r['price'] is None:
            out.append(problem('error', where, f'{where} 没有票价（比赛阶段 {s["band"]}）'))
        elif r['price'] is not None and money(r['price']) < 0:
            out.append(problem('error', where, f'{where} 票价为负数'))
    for bucket in book['buckets']:
        for tier, cap in bucket['cap'].items():
            if cap in (None, ''):
                continue
            qty = rows.get(tier, {}).get('by_bucket', {}).get(bucket['id'], 0)
            if qty > count(cap):
                out.append(problem('warning', f'{code} {names.get(tier, tier)}', f'{code} {names.get(tier, tier)} {bucket["name"]} {qty} 张，超过上限 {count(cap)} 张'))
    return out


def check_rounds(book: dict) -> list[dict]:
    out = []
    sessions = {s['code'] for s in book['sessions']}
    for r in book['rounds']:
        unknown = [c for c in (r.get('sessions') or []) if c not in sessions]
        if unknown:
            out.append(problem('error', r['code'], f'放票轮次 {r.get("name") or r["code"]} 的场次不存在：{"、".join(unknown)}'))
    for s in book['sessions']:
        over = []
        for t in book['tiers']:
            total = sum((money(r['share'].get(t['code'])) for r in book['rounds'] if round_covers(r, s)), Decimal(0))
            if total > 100:
                over.append(f'{t["name"]} {total}%')
        if over:
            out.append(problem('warning', s['code'], f'{s["code"]} 各轮放票比例合计超过 100%：{"、".join(over)}'))
    return out


def as_of(book: dict, rounds: list[str] | None) -> dict:
    """A copy of the book counting only the sales of the given rounds (for an inventory count at a past date)."""
    if rounds is None:
        return book
    unknown = set(rounds) - {r['code'] for r in book['rounds']}
    if unknown:
        raise BookError('未知轮次：' + '、'.join(sorted(unknown)))
    copy_ = dict(book)
    copy_['sales'] = {k: v for k, v in book['sales'].items() if k in rounds}
    return copy_
