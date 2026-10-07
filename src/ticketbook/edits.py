"""Small, explicit edits to the book, and a readable comparison of two books."""
from __future__ import annotations

import copy
from datetime import date, timedelta

from .live import validate_damai, validate_live
from .model import BUCKET_KINDS, PRODUCT_KINDS, BookError, count, money, normalize

LISTS = {'tiers': 'code', 'bands': 'code', 'layouts': 'code', 'sessions': 'code', 'buckets': 'id', 'products': 'id', 'rounds': 'code', 'damai': 'id', 'templates': 'id'}


def _find(items: list, key: str, value):
    for item in items:
        if item.get(key) == value:
            return item
    raise BookError(f'找不到：{value}')


def _node(book: dict, path: list):
    node = book
    for key in path:
        if isinstance(node, list):
            ident = 'id' if node and 'id' in node[0] and 'code' not in node[0] else 'code'
            node = _find(node, ident, key)
        else:
            if key not in node or node[key] is None:
                node[key] = {}
            node = node[key]
    return node


def apply(book: dict, ops: list[dict]) -> dict:
    """Apply edit operations to a copy of the book and return it.

    ops: {"op": "set", "path": [...], "value": v} | {"op": "add", "list": "sessions", "item": {...}}
         | {"op": "remove", "list": "sessions", "key": "S3"} | {"op": "rename", "list": "tiers", "key": "A", "to": "A1"}
    """
    out = copy.deepcopy(book)
    for op in ops:
        kind = op.get('op')
        if kind == 'set':
            path = list(op['path'])
            if not path:
                raise BookError('缺少路径')
            parent = _node(out, path[:-1])
            if op.get('value') is None and isinstance(parent, dict):
                parent.pop(path[-1], None)
            else:
                parent[path[-1]] = op['value']
        elif kind == 'add':
            name = op['list']
            key = LISTS.get(name)
            if not key:
                raise BookError('不能添加到：' + str(name))
            item = dict(op['item'])
            if not item.get(key):
                raise BookError('缺少代码')
            if any(i.get(key) == item[key] for i in out[name]):
                raise BookError(f'代码已存在：{item[key]}')
            out[name].append(item)
        elif kind == 'remove':
            name = op['list']
            key = LISTS.get(name)
            if not key:
                raise BookError('不能删除：' + str(name))
            out[name] = [i for i in out[name] if i.get(key) != op['key']]
            _drop_references(out, name, op['key'])
        elif kind == 'rename':
            _rename(out, op['list'], op['key'], op['to'])
        else:
            raise BookError('未知操作：' + str(kind))
    out = normalize(out)
    validate_types(out)
    return out


def _drop_references(book: dict, name: str, key: str):
    if name == 'tiers':
        for band in book['prices'].values():
            band.pop(key, None)
        for layout in book['layouts']:
            layout['seats'].pop(key, None)
        for b in book['buckets']:
            b['default'].pop(key, None)
            b['cap'].pop(key, None)
            for o in b['overrides'].values():
                o.pop(key, None)
    elif name == 'bands':
        book['prices'].pop(key, None)
        book['forecast']['band_fill'].pop(key, None)
        for r in book['rounds']:
            r['share'].pop(key, None)
    elif name == 'sessions':
        for b in book['buckets']:
            b['overrides'].pop(key, None)
        for sales in book['sales'].values():
            sales.pop(key, None)
        book['forecast']['session_fill'].pop(key, None)
        book['live'].pop(key, None)
    elif name == 'rounds':
        book['sales'].pop(key, None)


def _rename(book: dict, name: str, old: str, new: str):
    if not new:
        raise BookError('新代码不能为空')
    if any(i.get('code') == new for i in book.get(name, [])):
        raise BookError(f'代码已存在：{new}')
    _find(book[name], 'code', old)['code'] = new

    def move(d: dict):
        if old in d:
            d[new] = d.pop(old)

    if name == 'tiers':
        for band in book['prices'].values():
            move(band)
        for layout in book['layouts']:
            move(layout['seats'])
        for t in book['tiers']:
            if t.get('blocked_of') == old:
                t['blocked_of'] = new
        for b in book['buckets']:
            move(b['default'])
            move(b['cap'])
            for o in b['overrides'].values():
                move(o)
        for p in book['products']:
            if p['tier'] == old:
                p['tier'] = new
        for sales in book['sales'].values():
            for s in sales.values():
                move(s)
    elif name == 'bands':
        move(book['prices'])
        move(book['forecast']['band_fill'])
        for s in book['sessions']:
            if s['band'] == old:
                s['band'] = new
        for r in book['rounds']:
            move(r['share'])
        for b in book['buckets']:
            if b.get('bands'):
                b['bands'] = [new if x == old else x for x in b['bands']]
    elif name == 'layouts':
        for s in book['sessions']:
            if s['layout'] == old:
                s['layout'] = new
    elif name == 'sessions':
        for b in book['buckets']:
            move(b['overrides'])
        for sales in book['sales'].values():
            move(sales)
        move(book['forecast']['session_fill'])
        move(book['live'])
    elif name == 'rounds':
        move(book['sales'])
    else:
        raise BookError('不能改代码：' + name)


def validate_types(book: dict):
    """Refuse values that are not numbers where numbers are needed, so bad input never reaches the ledger."""
    for band, row in book['prices'].items():
        for tier, value in row.items():
            if value not in (None, '') and money(value) < 0:
                raise BookError(f'票价不能为负：{band} {tier}')
    for layout in book['layouts']:
        for tier, value in layout['seats'].items():
            if count(value) < 0:
                raise BookError(f'座席数不能为负：{layout["code"]} {tier}')
    for b in book['buckets']:
        if b['kind'] not in BUCKET_KINDS:
            raise BookError('分配类别未知：' + str(b['kind']))
        for part in [b['default'], b['cap'], *b['overrides'].values()]:
            for value in part.values():
                if count(value) < 0:
                    raise BookError(f'数量不能为负：{b["name"]}')
    for p in book['products']:
        if p['kind'] not in PRODUCT_KINDS:
            raise BookError('产品类型未知：' + str(p['kind']))
        count(p['quota'])
    for sales in book['sales'].values():
        for row in sales.values():
            for value in row.values():
                if count(value) < 0:
                    raise BookError('已售数量不能为负')
    money(book['event']['agent_fee_pct'])
    validate_live(book)
    validate_damai(book)


def flatten(value, prefix=()) -> dict:
    """{path tuple: leaf value}; list items are keyed by their code/id so reordering is not a change."""
    out = {}
    if isinstance(value, dict):
        for k, v in value.items():
            out.update(flatten(v, prefix + (str(k),)))
    elif isinstance(value, list) and value and all(isinstance(i, dict) and ('code' in i or 'id' in i) for i in value):
        for item in value:
            out.update(flatten(item, prefix + (str(item.get('code', item.get('id'))),)))
    else:
        out[prefix] = value
    return out


def compare(old: dict, new: dict) -> list[dict]:
    a, b = flatten(old), flatten(new)
    rows = []
    for path in sorted(set(a) | set(b)):
        if path and path[0] == 'forecast' and len(path) > 1 and path[1] == 'scenarios':
            continue
        if path and path[0] == 'templates' and path[-1] == 'data':
            continue  # the Word file itself; its name and size still show
        if str(a.get(path)) != str(b.get(path)):
            rows.append({'path': list(path), 'old': a.get(path), 'new': b.get(path)})
    return rows


def copy_event(book: dict, name: str, year: int | None, shift_days: int) -> dict:
    """Start next year's event from this one: same structure, dates moved, sales and scenarios cleared."""
    out = copy.deepcopy(book)
    out['event']['name'] = name
    out['event']['year'] = year
    out['sales'] = {}
    out['live'] = {}
    out['damai'] = []
    out['forecast']['scenarios'] = []

    def move(day: str) -> str:
        if not day:
            return day
        try:
            return (date.fromisoformat(day) + timedelta(days=shift_days)).isoformat()
        except ValueError:
            return day

    for s in out['sessions']:
        s['date'] = move(s['date'])
    for p in out['products']:
        if p.get('days'):
            p['days'] = [move(d) for d in p['days']]
    for r in out['rounds']:
        if r.get('opens'):
            d, _, t = r['opens'].partition('T')
            r['opens'] = move(d) + (('T' + t) if t else '')
    return normalize(out)
