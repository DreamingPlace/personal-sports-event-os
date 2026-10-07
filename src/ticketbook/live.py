"""Match-day entry figures (from Damai's on-site screen) and Damai sales snapshots.

Live figures are kept per session as the numbers last read off Damai's entry screen; days and the whole event are
worked out from them. Damai sales snapshots are the project rows of Damai's "票房销售统计" page, kept with the time
they were read, so the sales curve can be followed day by day.
"""
from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal

from .model import BookError, count, money

AGES = ('u18', '18-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50+')
AGE_NAMES = {'u18': '18岁以下', '18-24': '18-24岁', '25-29': '25-29岁', '30-34': '30-34岁', '35-39': '35-39岁',
             '40-44': '40-44岁', '45-49': '45-49岁', '50+': '50岁以上'}
DAMAI_FIELDS = ('plan_qty', 'sold_qty', 'today_qty', 'left_qty', 'plan_amount', 'sold_amount', 'today_amount', 'left_amount')


def pct(part, whole) -> str | None:
    """part / whole as a percentage string with 2 decimals, or None when whole is 0."""
    whole = Decimal(whole)
    if not whole:
        return None
    return str((Decimal(part) * 100 / whole).quantize(Decimal('0.01'), ROUND_HALF_UP))


def issued(row: dict) -> int:
    """Tickets the ticket book has given out for a session: comps, priority, reserves, passes and public sales."""
    return row['comp'] + row['priority'] + row['reserve'] + row['product'] + row['sold']


def _weighted(entries: list[dict], key) -> str | None:
    """Average of a percentage over sessions, weighted by people checked in. key(entry) -> pct string or None."""
    total, weight = Decimal(0), 0
    for e in entries:
        value = key(e)
        if value in (None, ''):
            continue
        total += money(value) * count(e.get('checked'))
        weight += count(e.get('checked'))
    if not weight:
        return None
    return str((total / weight).quantize(Decimal('0.1'), ROUND_HALF_UP))


def _sum_up(entries: list[dict]) -> dict:
    checked = sum(count(e.get('checked')) for e in entries)
    realname = sum(count(e.get('realname')) for e in entries)
    total = sum(count(e.get('total')) for e in entries)
    return {
        'checked': checked, 'realname': realname, 'total': total,
        'rate': pct(checked, total),
        'female_pct': _weighted(entries, lambda e: e.get('female_pct')),
        'local_pct': _weighted(entries, lambda e: e.get('local_pct')),
        'age': {a: _weighted(entries, lambda e, a=a: (e.get('age') or {}).get(a)) for a in AGES},
    }


def live_summary(book: dict, ledger: dict) -> dict:
    """Per session, per day and whole-event entry figures, set against what the ticket book says was issued."""
    by_code = {s['code']: s for s in ledger['sessions']}
    sessions, days = [], {}
    for s in book['sessions']:
        entry = book['live'].get(s['code'])
        book_issued = issued(by_code[s['code']]['total'])
        row = {'code': s['code'], 'date': s['date'], 'start': s['start'], 'entered': bool(entry), 'issued': book_issued}
        if entry:
            row.update(_sum_up([entry]))
            row['at'] = entry.get('at', '')
            row['origins'] = entry.get('origins') or []
            row['local_name'] = entry.get('local_name', '')
            row['no_show'] = count(entry.get('total')) - count(entry.get('checked'))
            row['diff'] = count(entry.get('total')) - book_issued
            days.setdefault(s['date'], []).append(entry)
        sessions.append(row)
    entries = [book['live'][s['code']] for s in book['sessions'] if book['live'].get(s['code'])]
    return {
        'sessions': sessions,
        'days': [{'date': d, 'sessions': len(e), **_sum_up(e)} for d, e in sorted(days.items())],
        'overall': {'sessions': len(entries), **_sum_up(entries)},
        'age_names': AGE_NAMES,
    }


def validate_live(book: dict):
    for code, entry in book['live'].items():
        if not isinstance(entry, dict):
            raise BookError(f'入场数据格式错误：{code}')
        for key in ('checked', 'realname', 'total'):
            if count(entry.get(key)) < 0:
                raise BookError(f'入场人数不能为负：{code}')
        for key in ('female_pct', 'local_pct'):
            _percent(entry.get(key), code)
        for value in (entry.get('age') or {}).values():
            _percent(value, code)
        for origin in entry.get('origins') or []:
            _percent(origin.get('pct'), code)


def _percent(value, where: str):
    if value in (None, ''):
        return
    number = money(value)
    if number < 0 or number > 100:
        raise BookError(f'百分比须在 0 到 100 之间：{where} {value}')


def validate_damai(book: dict):
    for snap in book['damai']:
        for p in snap.get('projects', []):
            for key in DAMAI_FIELDS:
                if key.endswith('_qty'):
                    count(p.get(key))
                else:
                    money(p.get(key))


# ---- Reading the Damai sales table from copied text --------------------------------------------------------------

_NUMBER = r'-?\d[\d,]*(?:\.\d+)?'


def _numbers(text: str) -> list[str]:
    return [n.replace(',', '') for n in re.findall(_NUMBER, text)]


def parse_damai_table(text: str) -> list[dict]:
    """Project rows from the "票房销售统计" table as copied from the Damai page (select the table, copy, paste).

    Each project row has its project ID and name, then a 数量 line and a 金额 line, each with four figures:
    planned, sold in total, sold today, left. Browsers copy a table either one row per line or one cell per line,
    so the row is found from its 数量/金额 labels: the ID is the first long number after the previous row's figures.
    """
    text = text.replace('\u3000', ' ').replace('\xa0', ' ')
    rows, pos = [], 0
    four = r'((?:\s*' + _NUMBER + r'%?[^\d\-数金]*?){4})'
    for qty in re.finditer(r'数量[（(]?张?[）)]?' + four, text):
        amount = re.compile(r'金额[（(]?元?[）)]?' + four).search(text, qty.end())
        head = text[pos:qty.start()]
        ident = re.search(r'(?<![\d.,])(\d{8,12})(?![\d.,])', head)
        if not amount or not ident:
            continue
        q, a = _numbers(qty.group(1))[:4], _numbers(amount.group(1))[:4]
        pos = amount.end()
        rows.append({'id': ident.group(1), 'name': _project_name(head[ident.end():]),
                     'plan_qty': count(q[0]), 'sold_qty': count(q[1]), 'today_qty': count(q[2]), 'left_qty': count(q[3]),
                     'plan_amount': a[0], 'sold_amount': a[1], 'today_amount': a[2], 'left_amount': a[3]})
    if not rows:
        raise BookError('没有从粘贴内容里读到项目。请在大麦“票房销售统计”页选中整个表格后复制，再粘贴。')
    return rows


def _project_name(text: str) -> str:
    """The first piece of text in the row that is not a date, a number or a column label."""
    for part in re.split(r'[\t\n]+', text):
        part = part.strip()
        if not part or re.fullmatch(r'[\d\s\-:至.,%]+', part):
            continue
        return part
    return ''


def damai_summary(book: dict, gross: str | None = None) -> dict:
    """Each snapshot with totals; the latest one also compared with the planned figures in the ticket book."""
    snaps = []
    for snap in sorted(book['damai'], key=lambda s: s.get('at', '')):
        projects = snap.get('projects', [])
        total = {k: (sum(count(p.get(k)) for p in projects) if k.endswith('_qty') else str(sum((money(p.get(k)) for p in projects), Decimal(0))))
                 for k in DAMAI_FIELDS}
        total['rate'] = pct(total['sold_qty'], total['plan_qty'])
        rows = [{**p, 'rate': pct(count(p.get('sold_qty')), count(p.get('plan_qty')))} for p in projects]
        snaps.append({'id': snap['id'], 'at': snap.get('at', ''), 'note': snap.get('note', ''), 'projects': rows, 'total': total})
    latest = snaps[-1] if snaps else None
    return {'snapshots': snaps, 'latest': latest,
            'vs_forecast': pct(money(latest['total']['sold_amount']), money(gross)) if latest and gross not in (None, '') and money(gross) else None}
