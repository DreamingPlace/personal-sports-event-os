"""A small invented event used by "Try with example data" and by the tests. Not real figures."""
from __future__ import annotations

from datetime import date, timedelta

from .model import new_book, normalize


def example_book() -> dict:
    book = new_book('示例赛事（虚构数据）', 2030)
    book['event'].update(venue='示例体育馆', agent_fee_pct='5')
    book['tiers'] = [
        {'code': 'VIP', 'name': 'VIP'}, {'code': 'A', 'name': 'A档'}, {'code': 'B', 'name': 'B档'},
        {'code': 'B遮挡', 'name': 'B档遮挡', 'blocked_of': 'B', 'blocked_discount': '100'}, {'code': 'C', 'name': 'C档'},
    ]
    book['bands'] = [{'code': 'pre', 'name': '预赛'}, {'code': 'rr', 'name': '循环赛'}, {'code': 'final', 'name': '决赛'}]
    book['prices'] = {
        'pre': {'VIP': '500', 'A': '400', 'B': '300', 'C': '100'},
        'rr': {'VIP': '800', 'A': '600', 'B': '400', 'C': '150'},
        'final': {'VIP': '1500', 'A': '1200', 'B': '800', 'C': '200'},
    }
    book['layouts'] = [
        {'code': 'four', 'name': '四面台', 'seats': {'VIP': 1000, 'A': 800, 'B': 900, 'B遮挡': 100, 'C': 600}},
        {'code': 'two', 'name': '两张球台', 'seats': {'VIP': 1100, 'A': 800, 'B': 900, 'B遮挡': 100, 'C': 600}},
    ]
    start = date(2030, 12, 1)
    sessions = []
    plan = [('pre', 'four', False), ('pre', 'four', True), ('rr', 'two', False), ('rr', 'two', True), ('final', 'two', True)]
    for i, (band, layout, china) in enumerate(plan):
        day = start + timedelta(days=i // 2)
        sessions.append({'code': f'S{i + 1}', 'date': day.isoformat(), 'start': '13:00' if i % 2 == 0 else '19:00',
                         'band': band, 'layout': layout, 'china': china, 'note': ''})
    book['sessions'] = sessions
    book['buckets'] = [
        {'id': 'broadcast', 'name': '转播遮挡', 'kind': 'hold', 'default': {'VIP': 30, 'A': 10}},
        {'id': 'security', 'name': '安保座席', 'kind': 'hold', 'default': {'C': 20}},
        {'id': 'partner', 'name': '国际组织', 'kind': 'comp', 'default': {'VIP': 100, 'A': 50}},
        {'id': 'venue', 'name': '场馆', 'kind': 'comp', 'default': {'A': 30}},
        {'id': 'sponsor', 'name': '赞助商优先购', 'kind': 'priority', 'default': {'VIP': 80, 'A': 40, 'B': 40}, 'cap': {'VIP': 100, 'A': 50, 'B': 50}},
        {'id': 'overseas', 'name': '海外平台', 'kind': 'reserve', 'default': {'VIP': 20, 'A': 20}},
    ]
    book['products'] = [{'id': 'daypass', 'name': '一日通票', 'kind': 'day', 'tier': 'B', 'quota': 50}]
    book['rounds'] = [
        {'code': 'R1', 'name': '第一轮', 'opens': '2030-11-10T15:00', 'share': {'pre': '100', 'rr': '40'}},
        {'code': 'R2', 'name': '第二轮', 'opens': '2030-11-18T15:00', 'share': {'rr': '60', 'final': '30'}},
        {'code': 'R3', 'name': '第三轮', 'opens': '2030-11-25T15:00', 'share': {'final': '70'}},
    ]
    book['forecast'].update(method='china', china_fill='95', other_fill='65')
    return normalize(book)
