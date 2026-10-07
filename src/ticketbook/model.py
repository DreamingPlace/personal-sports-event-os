"""The ticket book: one JSON document per event.

Everything the app knows about an event lives in one plain dict, so it can be saved,
versioned and compared as a whole. Money is kept as strings and read with Decimal.
"""
from __future__ import annotations

import copy
from decimal import Decimal, InvalidOperation

SCHEMA = 1
BUCKET_KINDS = ('hold', 'comp', 'priority', 'reserve')
BUCKET_KIND_NAMES = {'hold': '功能占用', 'comp': '权益/赠票', 'priority': '优先购', 'reserve': '预留'}
PRODUCT_KINDS = ('day', 'full', 'package')


class BookError(ValueError):
    """Input the book cannot accept (wrong type, unknown code)."""


def money(value) -> Decimal:
    if value is None or value == '':
        return Decimal(0)
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise BookError(f'不是有效金额：{value}') from exc


def count(value) -> int:
    if value is None or value == '':
        return 0
    if isinstance(value, bool):
        raise BookError(f'不是有效数量：{value}')
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise BookError(f'不是有效数量：{value}') from exc
    if number != number.to_integral_value():
        raise BookError(f'数量须为整数：{value}')
    return int(number)


def new_book(name: str = '', year: int | None = None) -> dict:
    return {
        'schema': SCHEMA,
        'event': {'name': name, 'year': year, 'venue': '', 'agent_fee_pct': '0'},
        'tiers': [],
        'bands': [],
        'prices': {},
        'layouts': [],
        'sessions': [],
        'buckets': [],
        'products': [],
        'rounds': [],
        'sales': {},
        'live': {},
        'damai': [],
        'templates': [],
        'forecast': {'method': 'band', 'band_fill': {}, 'china_fill': '95', 'other_fill': '65',
                     'session_fill': {}, 'product_fill': '100', 'scenarios': []},
    }


def normalize(book: dict) -> dict:
    """Fill in missing keys so older or hand-made books open without errors."""
    if not isinstance(book, dict):
        raise BookError('票务总表格式错误')
    base = new_book()
    out = copy.deepcopy(book)
    for key, value in base.items():
        out.setdefault(key, copy.deepcopy(value))
    for key, value in base['event'].items():
        out['event'].setdefault(key, value)
    for key, value in base['forecast'].items():
        out['forecast'].setdefault(key, copy.deepcopy(value))
    for tier in out['tiers']:
        tier.setdefault('name', tier['code'])
        tier.setdefault('blocked_of', None)
        tier.setdefault('blocked_discount', '0')
    for band in out['bands']:
        band.setdefault('name', band['code'])
    for layout in out['layouts']:
        layout.setdefault('name', layout['code'])
        layout.setdefault('seats', {})
    for session in out['sessions']:
        session.setdefault('date', '')
        session.setdefault('start', '')
        session.setdefault('china', False)
        session.setdefault('note', '')
    for bucket in out['buckets']:
        bucket.setdefault('default', {})
        bucket.setdefault('bands', None)
        bucket.setdefault('overrides', {})
        bucket.setdefault('cap', {})
    for product in out['products']:
        product.setdefault('price', None)
        product.setdefault('extra', '0')
        product.setdefault('days', None)
    for rnd in out['rounds']:
        rnd.setdefault('opens', '')
        rnd.setdefault('share', {})
    return out


def index(items: list, key: str = 'code') -> dict:
    return {item[key]: item for item in items}


def tier_codes(book: dict) -> list[str]:
    return [t['code'] for t in book['tiers']]


def price(book: dict, band: str, tier: str) -> Decimal | None:
    """Price for one band × tier. A view-blocked tier without its own price is its base tier minus the discount."""
    explicit = book['prices'].get(band, {}).get(tier)
    if explicit not in (None, ''):
        return money(explicit)
    t = index(book['tiers']).get(tier)
    if t and t.get('blocked_of'):
        base = price(book, band, t['blocked_of'])
        if base is not None:
            return base - money(t.get('blocked_discount'))
    return None


def seats(book: dict, layout: str, tier: str) -> int:
    lay = index(book['layouts']).get(layout)
    return count(lay['seats'].get(tier)) if lay else 0


def bucket_qty(bucket: dict, session: dict, tier: str) -> int:
    """A bucket's seats in one session × tier: the per-session override if set, else the default rule."""
    override = bucket['overrides'].get(session['code'], {})
    if tier in override and override[tier] not in (None, ''):
        return count(override[tier])
    bands = bucket.get('bands')
    if bands and session['band'] not in bands:
        return 0
    return count(bucket['default'].get(tier))


def product_sessions(book: dict, product: dict) -> list[dict]:
    if product['kind'] == 'full':
        return list(book['sessions'])
    days = product.get('days')
    return [s for s in book['sessions'] if not days or s['date'] in days]


def product_prices(book: dict, product: dict) -> list[tuple[str, int, Decimal]]:
    """(label, units, unit price) lines for a product: one line per day for day passes/packages, one for a full pass.

    The unit price is the set price if any, else the sum of the covered sessions' prices in the product's tier, plus extras.
    """
    sessions = product_sessions(book, product)
    groups = {'全程': sessions} if product['kind'] == 'full' else {}
    if product['kind'] != 'full':
        for s in sessions:
            groups.setdefault(s['date'], []).append(s)
    lines = []
    for label, group in groups.items():
        if product.get('price') not in (None, ''):
            unit = money(product['price'])
        else:
            unit = sum((price(book, s['band'], product['tier']) or Decimal(0) for s in group), Decimal(0)) + money(product.get('extra'))
        lines.append((label, count(product['quota']), unit))
    return lines
