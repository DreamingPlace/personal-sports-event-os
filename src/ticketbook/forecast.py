"""Box office forecast: preview changes on a copy of the book; only `apply` writes them back."""
from __future__ import annotations

import copy
from decimal import Decimal

from .model import BookError, count, index, money, normalize, product_prices
from .ledger import compute

# What the forecast page may change, as paths into the book. Anything else is refused.
EDITABLE = {
    ('prices',): 'price', ('layouts',): 'seats', ('forecast', 'band_fill'): 'pct', ('forecast', 'session_fill'): 'pct',
    ('forecast', 'china_fill'): 'pct', ('forecast', 'other_fill'): 'pct', ('forecast', 'product_fill'): 'pct',
    ('forecast', 'method'): 'method', ('event', 'agent_fee_pct'): 'pct', ('buckets',): 'qty', ('products',): 'qty',
}


def fill_rate(book: dict, session: dict) -> Decimal:
    """Expected share of paid seats sold for one session, in %."""
    fc = book['forecast']
    own = fc['session_fill'].get(session['code'])
    if own not in (None, ''):
        return money(own)
    if fc['method'] == 'china':
        return money(fc['china_fill'] if session.get('china') else fc['other_fill'])
    band = fc['band_fill'].get(session['band'])
    return money(band) if band not in (None, '') else Decimal(100)


def forecast(book: dict) -> dict:
    """Expected box office per session, per day, per band and in total, gross and after the agent fee.

    Paid seats are public sale + priority purchase + reserves (comps and holds earn nothing); passes are counted separately.
    """
    ledger = compute(book)
    by_code = index(book['sessions'])
    sessions, by_day, by_band = [], {}, {}
    gross_full = gross = Decimal(0)
    for row in ledger['sessions']:
        s = by_code[row['code']]
        rate = fill_rate(book, s)
        full = Decimal(0)
        for r in row['tiers'].values():
            if r['price'] is None:
                continue
            full += money(r['price']) * max(0, r['public'] + r['priority'] + r['reserve'])
        expected = full * rate / 100
        sessions.append({'code': s['code'], 'date': s['date'], 'band': s['band'], 'china': s['china'], 'fill': str(rate),
                         'full': str(full), 'expected': str(expected)})
        by_day[s['date']] = by_day.get(s['date'], Decimal(0)) + expected
        by_band[s['band']] = by_band.get(s['band'], Decimal(0)) + expected
        gross_full += full
        gross += expected
    products = []
    product_rate = money(book['forecast']['product_fill'])
    for p in book['products']:
        value = sum((Decimal(units) * unit for _, units, unit in product_prices(book, p)), Decimal(0))
        expected = value * product_rate / 100
        products.append({'id': p['id'], 'name': p['name'], 'full': str(value), 'expected': str(expected)})
        gross_full += value
        gross += expected
    fee = gross * money(book['event']['agent_fee_pct']) / 100
    return {'sessions': sessions, 'products': products,
            'by_day': {k: str(v) for k, v in by_day.items()}, 'by_band': {k: str(v) for k, v in by_band.items()},
            'full_value': str(gross_full), 'gross': str(gross), 'agent_fee': str(fee), 'net': str(gross - fee),
            'problems': ledger['problems']}


def _set(book: dict, path: list, value):
    """Set one value inside the book. Lists are addressed by item code/id, e.g. ['layouts', 'main', 'seats', 'VIP']."""
    node = book
    for i, key in enumerate(path[:-1]):
        if isinstance(node, list):
            match = [item for item in node if item.get('code', item.get('id')) == key]
            if not match:
                raise BookError(f'找不到：{"/".join(map(str, path[:i + 1]))}')
            node = match[0]
        else:
            node = node.setdefault(key, {})
    node[path[-1]] = value


def _get(book: dict, path: list):
    node = book
    for key in path:
        if isinstance(node, list):
            match = [item for item in node if item.get('code', item.get('id')) == key]
            if not match:
                return None
            node = match[0]
        elif isinstance(node, dict):
            node = node.get(key)
        else:
            return None
        if node is None:
            return None
    return node


def _check_change(path: list, value):
    for prefix, kind in EDITABLE.items():
        if tuple(path[:len(prefix)]) == prefix:
            if kind == 'method':
                if value not in ('band', 'china'):
                    raise BookError('测算方式只能是 band 或 china')
            elif kind in ('qty', 'seats'):
                if count(value) < 0:
                    raise BookError(f'数量不能为负：{"/".join(map(str, path))}')
            elif value not in (None, '') and money(value) < 0:
                raise BookError(f'数值不能为负：{"/".join(map(str, path))}')
            return
    raise BookError('测算页不能修改：' + '/'.join(map(str, path)))


def candidate(book: dict, changes: list[dict]) -> dict:
    """A changed copy of the book. The original is never touched."""
    out = copy.deepcopy(book)
    for change in changes:
        path, value = list(change['path']), change.get('value')
        _check_change(path, value)
        _set(out, path, value)
    return normalize(out)


def preview(book: dict, changes: list[dict]) -> dict:
    """Forecast before and after the changes, and the list of values that would change (old → new)."""
    after_book = candidate(book, changes)
    diff = []
    for change in changes:
        path = list(change['path'])
        old, new = _get(book, path), _get(after_book, path)
        if str(old) != str(new):
            diff.append({'path': path, 'old': old, 'new': new})
    return {'before': forecast(book), 'after': forecast(after_book), 'changes': diff}


def describe(book: dict, path: list) -> str:
    """A readable label for a change, e.g. '票价 预赛 VIP'."""
    names = {'prices': '票价', 'layouts': '座席', 'buckets': '分配', 'products': '通票/套票', 'event': '赛事', 'forecast': '测算'}
    parts = [names.get(path[0], path[0])] + [str(p) for p in path[1:]]
    return ' '.join(parts)

