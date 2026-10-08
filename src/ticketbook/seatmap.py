"""Reading a venue's seat map: seats and zone names from the seat sheet (PDF or Excel), tiers from a coloured picture.

The seat sheet (每个座位一个格子) gives exact zone names and seat counts. The coloured picture gives each seat's colour,
i.e. its tier. The two are drawn differently, so zones are matched by shape: both are split into blocks of touching
seats, the blocks are lined up by position and size, and each zone takes the colour of the picture blocks matched to it.
Nothing is saved until the user has checked the result and chosen a tier for each colour.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

from .model import BookError

ZONE_NAME = re.compile(r'(区|厢|台|席)$')


# --- seat sheet ---------------------------------------------------------------------------------------------------
def read_sheet(path) -> dict:
    """{'zones': [{'name', 'seats'}], 'points': [(x, y)], 'zone_of': [zone index per point]} from a PDF or Excel seat sheet."""
    suffix = Path(path).suffix.lower()
    if suffix == '.pdf':
        points, labels = _pdf_points(path)
    elif suffix in ('.xlsx', '.xlsm'):
        points, labels = _xlsx_points(path)
    else:
        raise BookError('座位表请用 PDF 或 Excel（.xlsx）')
    if not points:
        raise BookError('座位表里没有找到座位')
    if not labels:
        raise BookError('座位表里没有找到区域名称（如“101区”“VIP1号包厢”）')
    blocks = _blocks(points)
    stray = [b for b in blocks if len(b) == 1]  # a lone number away from every other seat is a note, not a seat
    if stray:
        keep = sorted(i for b in blocks if len(b) > 1 for i in b)
        points = [points[i] for i in keep]
        blocks = _blocks(points)
    names = [name for name, _, _ in labels]
    zone_of = [0] * len(points)
    for members in blocks:
        xs, ys = [points[i][0] for i in members], [points[i][1] for i in members]
        box = (min(xs), max(xs), min(ys), max(ys))
        zone = min(range(len(labels)), key=lambda i: _gap(box, labels[i]))
        for i in members:
            zone_of[i] = zone
    counts = Counter(zone_of)
    zones = [{'name': name, 'seats': counts.get(i, 0)} for i, name in enumerate(names)]
    return {'zones': zones, 'points': points, 'zone_of': zone_of, 'blocks': blocks, 'ignored': len(stray)}


def _gap(box, label) -> float:
    """Squared distance from a label to a block of seats (0 when the label sits over the block)."""
    x0, x1, y0, y1 = box
    _, lx, ly = label
    return max(x0 - lx, 0, lx - x1) ** 2 + max(y0 - ly, 0, ly - y1) ** 2


def _pdf_points(path):
    try:
        import pdfplumber
    except ImportError as exc:
        raise BookError('读取 PDF 需要 pdfplumber') from exc
    with pdfplumber.open(str(path)) as pdf:
        if not pdf.pages:
            raise BookError('PDF 没有页面')
        page = pdf.pages[0]
        chars = [c for c in page.chars if c['text'].strip()]
        coloured = [r for r in page.rects if r.get('fill') and _is_colour(r.get('non_stroking_color'))]
    if not chars:
        raise BookError('PDF 里没有文字，可能是图片；请用 Excel 导出的 PDF')
    sizes = Counter(round(c['size'], 1) for c in chars)
    big = max(sizes)
    labels = _join_labels([c for c in chars if c['size'] > big * 0.75])
    small = [c for c in chars if c['size'] <= big * 0.75]

    def in_colour(x, y):
        return any(r['x0'] <= x <= r['x1'] and r['top'] <= y <= r['bottom'] for r in coloured)
    # one seat per cell: characters of one number sit side by side, closer than half a character
    cells = []
    for c in sorted(small, key=lambda c: (round(c['top'], 1), c['x0'])):
        if cells and abs(cells[-1]['top'] - c['top']) < 0.3 and -c['width'] * 0.1 < c['x0'] - cells[-1]['x1'] < c['width'] * 0.2:
            cells[-1] = {**cells[-1], 'x1': c['x1'], 'text': cells[-1]['text'] + c['text']}
        else:
            cells.append(dict(c))
    points = []
    for c in cells:
        x, y = (c['x0'] + c['x1']) / 2, (c['top'] + c['bottom']) / 2
        if not in_colour(x, y):  # coloured cells hold row numbers (排号), not seats
            points.append((x, y))
    return points, labels


def _is_colour(value) -> bool:
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        return False
    return max(value) - min(value) > 0.08


def _join_labels(chars):
    """Zone names from large characters: neighbours on one line, or a column of characters written top to bottom."""
    chars = sorted(chars, key=lambda c: (c['x0'], c['top']))
    used, labels = set(), []
    for i, start in enumerate(chars):
        if i in used:
            continue
        group, used = [start], used | {i}
        grew = True
        while grew:
            grew = False
            for j, c in enumerate(chars):
                if j in used:
                    continue
                for g in group:
                    h = g['bottom'] - g['top']
                    line = abs(c['top'] - g['top']) < h * 0.3 and min(abs(c['x0'] - g['x1']), abs(g['x0'] - c['x1'])) < h * 0.8
                    column = abs((c['x0'] + c['x1']) / 2 - (g['x0'] + g['x1']) / 2) < h * 0.5 and \
                        min(abs(c['top'] - g['bottom']), abs(g['top'] - c['bottom'])) < h * 0.5
                    if line or column:
                        group.append(c)
                        used.add(j)
                        grew = True
                        break
        x0, x1 = min(g['x0'] for g in group), max(g['x1'] for g in group)
        y0, y1 = min(g['top'] for g in group), max(g['bottom'] for g in group)
        group.sort(key=(lambda g: (g['top'], g['x0'])) if y1 - y0 > x1 - x0 else (lambda g: (g['x0'], g['top'])))
        text = re.sub(r'\s+', '', ''.join(g['text'] for g in group))
        if ZONE_NAME.search(text):
            labels.append((text, (x0 + x1) / 2, (y0 + y1) / 2))
    return labels


def _xlsx_points(path):
    from openpyxl import load_workbook
    try:
        sheet = load_workbook(str(path), data_only=True).worksheets[0]
    except Exception as exc:  # openpyxl raises several types for broken files
        raise BookError('不是有效的 Excel 文件') from exc
    widths, x = {}, 0.0
    for col in range(1, sheet.max_column + 2):
        letter = sheet.cell(row=1, column=col).column_letter
        w = sheet.column_dimensions[letter].width if letter in sheet.column_dimensions else None
        widths[col] = (x, w or 8.43)
        x += w or 8.43
    heights, y = {}, 0.0
    for row in range(1, sheet.max_row + 2):
        h = sheet.row_dimensions[row].height if row in sheet.row_dimensions else None
        heights[row] = (y, (h or 15) / 7)  # points to roughly the width unit
        y += (h or 15) / 7
    merged = {}
    for rng in sheet.merged_cells.ranges:
        merged[(rng.min_row, rng.min_col)] = (rng.max_row, rng.max_col)
    points, labels = [], []
    for row in sheet.iter_rows():
        for cell in row:
            value = cell.value
            if value is None or str(value).strip() == '':
                continue
            r2, c2 = merged.get((cell.row, cell.column), (cell.row, cell.column))
            cx = (widths[cell.column][0] + widths[c2][0] + widths[c2][1]) / 2
            cy = (heights[cell.row][0] + heights[r2][0] + heights[r2][1]) / 2
            text = str(value).strip()
            if ZONE_NAME.search(text):
                labels.append((re.sub(r'\s+', '', text), cx, cy))
            elif re.fullmatch(r'\d{1,3}', text) and not _filled(cell):
                points.append((cx, cy))
    return points, labels


def _filled(cell) -> bool:
    """Coloured cells hold row numbers or headers, not seats."""
    fill = cell.fill
    if not fill or fill.fill_type in (None, 'none'):
        return False
    rgb = getattr(fill.fgColor, 'rgb', None)
    return isinstance(rgb, str) and rgb[-6:].upper() not in ('FFFFFF', '000000')


def _blocks(points) -> list[list[int]]:
    """Groups of seats that touch: neighbours within 1.6 seat spacings across and 1.4 row spacings down."""
    if not points:
        return []
    sx, sy = _spacing(points)
    rx, ry = sx * 1.56, sy * 1.39
    cell = defaultdict(list)
    for i, (x, y) in enumerate(points):
        cell[(int(x // rx), int(y // ry))].append(i)
    parent = list(range(len(points)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for i, (x, y) in enumerate(points):
        gx, gy = int(x // rx), int(y // ry)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in cell.get((gx + dx, gy + dy), []):
                    if j > i and abs(points[j][0] - x) <= rx and abs(points[j][1] - y) <= ry:
                        parent[find(i)] = find(j)
    groups = defaultdict(list)
    for i in range(len(points)):
        groups[find(i)].append(i)
    return list(groups.values())


def _spacing(points) -> tuple[float, float]:
    """Typical gap to the next seat in the same row, and to the next row (rows may run either way, so take the
    smaller nearest-neighbour distance along each axis)."""
    rows, cols = defaultdict(list), defaultdict(list)
    for x, y in points:
        rows[round(y, 0)].append(x)
        cols[round(x, 0)].append(y)

    def typical(groups):
        gaps = []
        for values in groups.values():
            values.sort()
            gaps += [b - a for a, b in zip(values, values[1:]) if b - a > 1e-6]
        gaps.sort()
        return gaps[len(gaps) // 4] if gaps else 1.0  # lower quartile: next seat, not the aisle
    return typical(rows), typical(cols)


# --- coloured picture ---------------------------------------------------------------------------------------------
def read_picture(path) -> dict:
    """{'points': [(x, y)], 'colour_of': [colour index], 'colours': [{'rgb', 'seats', 'legend'}]} from a coloured seat map."""
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise BookError('读取座位图片需要本机文字识别组件') from exc
    raw = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(raw, cv2.IMREAD_COLOR)
    if img is None:
        raise BookError('无法打开图片')
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = ((hsv[..., 1] > 90) & (hsv[..., 2] > 120)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, stats, cent = cv2.connectedComponentsWithStats(mask, 8)
    areas = stats[1:, cv2.CC_STAT_AREA]
    areas = areas[areas > 20]
    if not len(areas):
        raise BookError('图片里没有找到彩色座位')
    typical = float(np.median(areas))
    seats, legend = [], []
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        if 0.4 * typical < a < 2.5 * typical:
            seats.append(i)
        elif a > 20 * typical and w > 2 * h and (lab[y:y + h, x:x + w] == i).mean() > 0.9:
            legend.append(i)  # solid colour bars, as in a 图例
    if not seats:
        raise BookError('图片里没有找到彩色座位')

    def colour(i):
        x, y, w, h, _ = stats[i]
        part = lab[y:y + h, x:x + w] == i
        return [int(v) for v in np.median(img[y:y + h, x:x + w][part], axis=0)[::-1]], \
            float(np.median(hsv[y:y + h, x:x + w][part][:, 0]))
    found = [colour(i) for i in seats]
    groups = _hue_groups([hue for _, hue in found])
    colours = []
    for g in sorted(set(groups)):
        members = [found[k][0] for k in range(len(found)) if groups[k] == g]
        rgb = [int(sum(c[j] for c in members) / len(members)) for j in range(3)]
        colours.append({'rgb': rgb, 'seats': len(members), 'legend': ''})
    # legend names: text left of each solid bar, read only when the reader is installed
    for i in legend:
        rgb, hue = colour(i)
        k = min(range(len(colours)), key=lambda c: sum((colours[c]['rgb'][j] - rgb[j]) ** 2 for j in range(3)))
        if sum((colours[k]['rgb'][j] - rgb[j]) ** 2 for j in range(3)) < 60 ** 2:
            x, y, w, h, _ = stats[i]
            colours[k]['legend'] = _read_text(img[max(0, y - h):y + 2 * h, max(0, x - 3 * w):x])
    points = [(float(cent[i][0]), float(cent[i][1])) for i in seats]
    return {'points': points, 'colour_of': groups, 'colours': colours}


def _hue_groups(hues: list[float]) -> list[int]:
    """Colour group per seat: hues sorted and split where they jump (red wraps round at 180)."""
    hues = [h - 180 if h > 165 else h for h in hues]
    distinct = sorted(set(round(h) for h in hues))
    edges, start = [], distinct[0]
    for a, b in zip(distinct, distinct[1:]):
        if b - a > 8:
            edges.append((start, a))
            start = b
    edges.append((start, distinct[-1]))
    return [next(k for k, (lo, hi) in enumerate(edges) if lo <= round(h) <= hi) for h in hues]


def _read_text(crop) -> str:
    from . import ocr
    if not ocr.available() or crop.size == 0:
        return ''
    try:
        from rapidocr_onnxruntime import RapidOCR
        result, _ = RapidOCR()(crop)
    except Exception:  # a legend name is only a hint; the user picks tiers anyway
        return ''
    return ''.join(t for _, t, _ in (result or [])).strip()


# --- putting the two together -------------------------------------------------------------------------------------
def combine(sheet: dict, picture: dict | None) -> dict:
    """Each zone of the sheet with its seats and the picture colour most of its seats have (None without a picture)."""
    zones = [dict(z, colour=None, colours={}, sure=False) for z in sheet['zones']]
    if not picture:
        return {'zones': zones, 'colours': [], 'ignored': sheet.get('ignored', 0)}
    blocks_a = sheet['blocks']
    pts_b = picture['points']
    blocks_b = _blocks(pts_b)
    na, nb = _normalise(sheet['points']), _normalise(pts_b)

    def centre(points, members):
        return (sum(points[i][0] for i in members) / len(members), sum(points[i][1] for i in members) / len(members))
    ca = [centre(na, m) for m in blocks_a]
    cb = [centre(nb, m) for m in blocks_b]
    shift = [(0.0, 0.0)] * len(blocks_a)
    match = {}
    import math
    for _ in range(4):  # match, then let confident matches correct the position of their neighbours, and match again
        pairs = []
        for a, (ax, ay) in enumerate(ca):
            ax, ay = ax + shift[a][0], ay + shift[a][1]
            for b, (bx, by) in enumerate(cb):
                d = math.hypot(ax - bx, ay - by)
                if d < 0.15:
                    pairs.append((d / 0.03 + abs(math.log(len(blocks_a[a]) / len(blocks_b[b]))) * 4, a, b))
        pairs.sort()
        used_a, used_b, match = set(), set(), {}
        for cost, a, b in pairs:
            if a not in used_a and b not in used_b:
                used_a.add(a)
                used_b.add(b)
                match[a] = (b, cost)
        good = [(a, (cb[b][0] - ca[a][0], cb[b][1] - ca[a][1])) for a, (b, cost) in match.items() if cost < 2.5]
        if not good:
            break
        for a, (ax, ay) in enumerate(ca):
            near = sorted(good, key=lambda g: (ca[g[0]][0] - ax) ** 2 + (ca[g[0]][1] - ay) ** 2)[:4]
            shift[a] = (sum(g[1][0] for g in near) / len(near), sum(g[1][1] for g in near) / len(near))
    tally = defaultdict(Counter)
    sure = defaultdict(lambda: True)
    for a, members in enumerate(blocks_a):
        zone = sheet['zone_of'][members[0]]
        if a in match:
            b, cost = match[a]
            tally[zone].update(picture['colour_of'][i] for i in blocks_b[b])
            sure[zone] = sure[zone] and cost < 4
        else:
            sure[zone] = False
    for i, z in enumerate(zones):
        if tally[i]:
            z['colours'] = {str(k): v for k, v in tally[i].items()}
            z['colour'] = tally[i].most_common(1)[0][0]
            z['sure'] = sure[i] and tally[i].most_common(1)[0][1] >= 0.9 * sum(tally[i].values())
    return {'zones': zones, 'colours': picture['colours'], 'ignored': sheet.get('ignored', 0)}


def _normalise(points):
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    x0, y0 = min(xs), min(ys)
    w, h = (max(xs) - x0) or 1, (max(ys) - y0) or 1
    return [((x - x0) / w, (y - y0) / h) for x, y in points]


def picture_zones(picture: dict) -> dict:
    """Without a seat sheet: each block of touching seats in the picture is a zone, named 区域1, 区域2… from top left."""
    blocks = _blocks(picture['points'])
    pts = picture['points']
    blocks.sort(key=lambda m: (round(min(pts[i][1] for i in m) / 50), min(pts[i][0] for i in m)))
    zones = []
    for k, members in enumerate(blocks, 1):
        tally = Counter(picture['colour_of'][i] for i in members)
        zones.append({'name': f'区域{k}', 'seats': len(members), 'colour': tally.most_common(1)[0][0],
                      'colours': {str(c): v for c, v in tally.items()}, 'sure': len(tally) == 1})
    return {'zones': zones, 'colours': picture['colours'], 'ignored': 0}


def read(sheet_path=None, picture_path=None) -> dict:
    """Zones with seats and colours from a seat sheet, a coloured picture, or both."""
    if not sheet_path and not picture_path:
        raise BookError('请选择座位表（Excel/PDF）或座位图片')
    picture = read_picture(picture_path) if picture_path else None
    result = combine(read_sheet(sheet_path), picture) if sheet_path else picture_zones(picture)
    result['total'] = sum(z['seats'] for z in result['zones'])
    return result
