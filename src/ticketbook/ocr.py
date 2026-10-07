"""Reading Damai's on-site screen ("现场监控平台") from a screenshot, on this computer.

OCR runs locally with RapidOCR (an offline model, installed with `pip install .[ocr]`); nothing is uploaded.
The screen has a fixed layout, so each figure is found next to its label. Small text (gender, age, origin)
is read again from an enlarged, higher-contrast copy of the lower panel. Whatever is read is shown to the
user to check before it is saved; anything not found is left empty rather than guessed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .live import AGES
from .model import BookError

AGE_PATTERNS = (('u18', r'以下'), ('18-24', r'18\D?24'), ('25-29', r'25\D?29'), ('30-34', r'30\D?34'), ('35-39', r'35\D?39'),
                ('40-44', r'40\D?44'), ('45-49', r'45\D?49'), ('50+', r'50.*上|以上'))
PCT = re.compile(r'^(\d{1,3}(?:\.\d+)?)\s*%$')


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float
    text: str

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2


def available() -> bool:
    try:
        import rapidocr_onnxruntime  # noqa: F401
        import PIL  # noqa: F401
    except ImportError:
        return False
    return True


_engine = None


def _ocr(image, scale: float = 1.0, dx: float = 0, dy: float = 0) -> list[Box]:
    global _engine
    import numpy as np
    from rapidocr_onnxruntime import RapidOCR
    if _engine is None:
        _engine = RapidOCR()
    result, _ = _engine(np.array(image.convert('RGB')))
    boxes = []
    for points, text, _conf in result or []:
        xs, ys = [p[0] for p in points], [p[1] for p in points]
        boxes.append(Box(min(xs) / scale + dx, min(ys) / scale + dy, (max(xs) - min(xs)) / scale, (max(ys) - min(ys)) / scale, text.strip()))
    return boxes


def read_screenshot(path: str) -> dict:
    """OCR one screenshot of the live screen and pick out the figures."""
    if not available():
        raise BookError('本机还没有安装文字识别组件（rapidocr_onnxruntime）')
    from PIL import Image, ImageOps
    try:
        image = Image.open(path)
        image.load()
    except (OSError, ValueError) as exc:
        raise BookError(f'打不开图片：{path}') from exc
    boxes = _ocr(image)
    lower = _find(boxes, r'年龄分布|观众性别')
    if lower:
        # The lower panel's labels are tiny on a phone screenshot: read it again enlarged.
        top = max(0, lower.y - lower.h)
        bottom = min(image.height, lower.y + lower.h * 14)
        base = [b for b in boxes if b.cy < top]
        result = None
        for k in (4, 3):  # a second size picks up what the first misread
            crop = image.convert('L').crop((0, int(top), image.width, int(bottom)))
            crop = ImageOps.autocontrast(crop.resize((crop.width * k, crop.height * k), Image.BICUBIC))
            found = parse_boxes(base + _ocr(crop, k, 0, top))
            result = found if result is None else _merge(result, found)
            if not result['missing']:
                break
        return result
    return parse_boxes(boxes)


def _merge(first: dict, second: dict) -> dict:
    """Keep the first reading; fill its gaps from the second."""
    entry = dict(first['entry'])
    for key, value in second['entry'].items():
        if key == 'age':
            entry['age'] = {**value, **entry.get('age', {})}
        else:
            entry.setdefault(key, value)
    missing = [m for m in first['missing'] if m in second['missing']]
    return {'session': first['session'] or second['session'], 'entry': entry, 'missing': missing,
            'warnings': first['warnings'] or second['warnings']}


def _find(boxes: list[Box], pattern: str) -> Box | None:
    for b in boxes:
        if re.search(pattern, b.text):
            return b
    return None


def _number(text: str) -> int | None:
    digits = re.sub(r'[,.，。\s]', '', text).removesuffix('人')
    return int(digits) if re.fullmatch(r'\d{1,7}', digits) else None


def _pct(text: str) -> str | None:
    m = PCT.match(text.replace(' ', ''))
    if not m or float(m.group(1)) > 100:
        return None
    return m.group(1)


def _below(boxes: list[Box], label: Box) -> int | None:
    """The number written just under a label, in the same column."""
    best = None
    for b in boxes:
        n = _number(b.text)
        if n is None or b.cy <= label.cy or b.cy - label.cy > label.h * 4:
            continue
        if abs(b.x - label.x) > label.w:
            continue
        if best is None or b.cy < best[0]:
            best = (b.cy, n)
    return best[1] if best else None


def parse_boxes(boxes: list[Box]) -> dict:
    """Figures from OCR text boxes of the live screen. Returns {'session', 'entry', 'missing', 'warnings'}."""
    entry: dict = {}
    warnings: list[str] = []
    session = None
    for b in boxes:
        m = re.search(r'(?<![A-Za-z])S\s?(\d{1,2})(?!\d)', b.text)
        if m and ('杯' in b.text or '赛' in b.text or len(b.text) <= 4):
            session = 'S' + m.group(1)
            break
    for b in boxes:
        m = re.search(r'(20\d{2})-(\d{2})-(\d{2})\s*(\d{2}):(\d{2})', b.text)
        if m:
            entry['at'] = f'{m.group(1)}-{m.group(2)}-{m.group(3)}T{m.group(4)}:{m.group(5)}'
            break
    for key, pattern in (('checked', r'已验票'), ('realname', r'已实名'), ('total', r'总票数')):
        label = _find(boxes, pattern)
        value = _below(boxes, label) if label else None
        if value is not None:
            entry[key] = value
    rate_label = _find(boxes, r'到场率')
    shown_rate = None
    if rate_label:
        for b in boxes:
            p = _pct(b.text)
            if p and abs(b.cx - rate_label.cx) < rate_label.w * 2 and 0 < b.cy - rate_label.cy < rate_label.h * 4:
                shown_rate = p
                break
    if shown_rate and entry.get('total') and entry.get('checked') is not None:
        worked = entry['checked'] * 100 / entry['total']
        if abs(worked - float(shown_rate)) > 0.05:
            warnings.append(f'屏幕到场率 {shown_rate}% 与 已验票/总票数 算出的 {worked:.2f}% 不一致，请核对这三个数')

    gender, age_label = _find(boxes, r'性别'), _find(boxes, r'年龄分布')
    source = _find(boxes, r'来源分布') or _find(boxes, r'市内') or _find(boxes, r'人员分布')
    if gender and age_label:
        middle = (gender.x + age_label.x) / 2
        for b in boxes:
            p = _pct(b.text)
            if p and gender.x - gender.w < b.cx < age_label.x and b.cy > gender.cy:
                if b.cx < middle and 'female_pct' not in entry:
                    entry['female_pct'] = p
                elif b.cx >= middle and 'female_pct' not in entry:
                    entry['female_pct'] = _trim(100 - float(p))
    if age_label:
        right = source.x if source else float('inf')
        labels = []
        for b in boxes:
            if b.cy > age_label.cy and age_label.x - age_label.w < b.x < right:
                for key, pattern in AGE_PATTERNS:
                    if re.search(pattern, b.text) and key not in [k for k, _ in labels]:
                        labels.append((key, b))
                        break
        values = [b for b in boxes if _pct(b.text) and b.cy > age_label.cy + age_label.h * 0.5
                  and age_label.x + age_label.w < b.cx < right]
        rows = sorted(labels, key=lambda kb: kb[1].cy)
        step = _row_step(rows)
        for b in values:
            key = _nearest_age(rows, b, step)
            if key and key not in entry.setdefault('age', {}):
                entry['age'][key] = _pct(b.text)
    if source:
        # The local share sits in the panel's header row, after the local city's name (or after "省/市内人员分布").
        row = sorted((b for b in boxes if b.x > source.x and abs(b.cy - source.cy) < source.h), key=lambda b: b.x)
        for b in row:
            value = _pct(b.text) or (b.text if re.fullmatch(r'\d{1,2}', b.text) else None)
            if value:
                entry['local_pct'] = value
                break
        if '市内' in source.text:
            entry['local_name'] = '省/市内'
        else:
            city = [b for b in row if b.x > source.x + source.w and re.search(r'[\u4e00-\u9fff]', b.text) and '分布' not in b.text]
            if city:
                entry['local_name'] = city[0].text
    ages = entry.get('age', {})
    if len(ages) == len(AGES) and abs(sum(float(v) for v in ages.values()) - 100) > 3:
        warnings.append('年龄分布加起来不是 100%，可能有一个数读错，请核对')
    missing = [k for k in ('checked', 'realname', 'total', 'female_pct', 'local_pct') if k not in entry]
    missing += [f'age:{a}' for a in AGES if a not in entry.get('age', {})]
    return {'session': session, 'entry': entry, 'missing': missing, 'warnings': warnings}


def _trim(value: float) -> str:
    return f'{value:.2f}'.rstrip('0').rstrip('.')


def _row_step(rows: list) -> float:
    if len(rows) < 2:
        return 0
    first, last = rows[0], rows[-1]
    gap = AGES.index(last[0]) - AGES.index(first[0])
    return (last[1].cy - first[1].cy) / gap if gap else 0


def _nearest_age(rows: list, value: Box, step: float) -> str | None:
    """The age row a percentage belongs to: the label on the same line, or the row its height falls on."""
    for key, label in rows:
        if abs(label.cy - value.cy) < max(label.h, value.h) * 0.6:
            return key
    if step and rows:
        key, label = rows[0]
        index = AGES.index(key) + round((value.cy - label.cy) / step)
        if 0 <= index < len(AGES):
            return AGES[index]
    return None
