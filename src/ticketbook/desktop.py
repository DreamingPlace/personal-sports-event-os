"""Desktop sidecar: JSON Lines on stdin/stdout, one request per line, one reply per line."""
from __future__ import annotations

import contextlib
import json
import sys
import traceback
from pathlib import Path

from . import __version__
from .edits import apply, compare, copy_event
from .example import example_book
from .export import forecast_table, inventory_count
from .forecast import forecast, preview, candidate
from .ledger import compute
from . import ocr
from . import report
from .live import damai_summary, live_summary, parse_damai_table
from .model import BookError, new_book
from .store import BookFile, WrongPassword

PROTOCOL = '2.0'
DESKTOP_VERSION = '0.3.0'  # keep equal to apps/desktop/src-tauri/tauri.conf.json
MAX_LINE = 8 * 1024 * 1024


class ProtocolError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class Session:
    def __init__(self):
        self.file: BookFile | None = None

    def need_file(self) -> BookFile:
        if self.file is None:
            raise ProtocolError('NO_FILE', '请先新建或打开票务总表')
        return self.file

    def state(self) -> dict:
        f = self.need_file()
        ledger, fc = compute(f.book), forecast(f.book)
        book = dict(f.book)  # the Word templates stay in the file; the screen only needs their names
        book['templates'] = [{k: v for k, v in t.items() if k != 'data'} for t in f.book['templates']]
        return {'path': str(f.path), 'book': book, 'ledger': ledger, 'forecast': fc,
                'live': live_summary(f.book, ledger), 'damai': damai_summary(f.book, fc['gross']),
                'versions': f.versions(), 'snapshots': f.snapshots(), 'log': f.data['log'][-50:]}

    @staticmethod
    def _template(f: BookFile, ident: str) -> dict:
        for t in f.book['templates']:
            if t['id'] == ident:
                return t
        raise BookError('找不到模板：' + str(ident))

    def dispatch(self, method: str, p: dict):
        if method == 'health':
            return {'protocol': PROTOCOL, 'version': __version__, 'desktop_version': DESKTOP_VERSION, 'ocr': ocr.available()}
        if method == 'create_book':
            book = example_book() if p.get('example') else new_book(p.get('name', ''), p.get('year'))
            if p.get('name'):
                book['event']['name'] = p['name']
            self.file = BookFile.create(p['path'], p['password'], book)
            return self.state()
        if method == 'open_book':
            self.file = BookFile.open(p['path'], p['password'])
            self.file.log('打开文件')
            return self.state()
        if method == 'close':
            self.file = None
            return {}
        f = self.need_file()
        if method == 'state':
            return self.state()
        if method == 'edit':
            f.replace_book(apply(f.book, p['ops']), '修改', p.get('note', ''))
            return self.state()
        if method == 'save_version':
            f.save_version(p.get('label', ''))
            return self.state()
        if method == 'compare':
            def pick(ref):
                return f.book if ref == 'CURRENT' else f.version(ref)['book']
            return compare(pick(p['old']), pick(p['new']))
        if method == 'restore':
            f.restore(p['id'])
            return self.state()
        if method == 'snapshot_save':
            f.save_snapshot((p.get('label') or '').strip())
            return self.state()
        if method == 'snapshot_compare':
            return compare(f.snapshot_book(p['id']), f.book)  # only the inventory parts differ
        if method == 'snapshot_restore':
            f.restore_snapshot(p['id'])
            return self.state()
        if method == 'snapshot_delete':
            f.delete_snapshot(p['id'])
            return self.state()
        if method == 'forecast_preview':
            return preview(f.book, p['changes'])
        if method == 'forecast_apply':
            if p.get('confirm') is not True:
                raise ProtocolError('CONFIRM', '需要确认后才能写回')
            result = candidate(f.book, p['changes'])
            f.save_version(p.get('label') or '测算写回前自动保存')
            f.replace_book(result, '测算写回', f'{len(p["changes"])} 项')
            return self.state()
        if method == 'forecast_save_scenario':
            name = (p.get('name') or '').strip()
            if not name:
                raise BookError('请输入方案名称')
            candidate(f.book, p['changes'])  # refuse invalid changes now, not when the scenario is reopened
            book = json.loads(json.dumps(f.book))
            scenarios = [s for s in book['forecast']['scenarios'] if s['name'] != name]
            scenarios.append({'name': name, 'changes': p['changes']})
            book['forecast']['scenarios'] = scenarios
            f.replace_book(book, '保存测算方案', name)
            return self.state()
        if method == 'forecast_delete_scenario':
            book = json.loads(json.dumps(f.book))
            book['forecast']['scenarios'] = [s for s in book['forecast']['scenarios'] if s['name'] != p['name']]
            f.replace_book(book, '删除测算方案', p['name'])
            return self.state()
        if method == 'live_read':
            codes = {s['code'] for s in f.book['sessions']}
            out = []
            for path in p['paths']:
                try:
                    found = ocr.read_screenshot(path)
                except BookError as exc:
                    out.append({'path': path, 'error': str(exc)})
                    continue
                found['path'] = path
                found['known'] = found['session'] in codes
                out.append(found)
            return {'results': out}
        if method == 'report_fields':
            return {'fields': report.fields(f.book)}
        if method == 'template_add':
            raw = Path(p['path']).read_bytes()
            check = report.check(f.book, raw)
            used = {t['id'] for t in f.book['templates']}
            n = len(used) + 1
            while f't{n}' in used:
                n += 1
            name = (p.get('name') or Path(p['path']).stem).strip()
            item = {'id': f't{n}', 'name': name, 'file': Path(p['path']).name, 'size': len(raw), 'markers': check['markers'],
                    'data': report.encode(raw)}
            f.replace_book(apply(f.book, [{'op': 'add', 'list': 'templates', 'item': item}]), '添加报告模板', name)
            return self.state()
        if method == 'template_check':
            return report.check(f.book, report.decode(self._template(f, p['id'])['data']))
        if method == 'report_make':
            tpl = self._template(f, p['id'])
            filled, unknown = report.fill(f.book, report.decode(tpl['data']))
            out = Path(p['path'])
            out.write_bytes(filled)
            f.log('生成报告', f'{tpl["name"]} → {out.name}')
            return {'path': str(out), 'unknown': unknown}
        if method == 'damai_read':
            return {'projects': parse_damai_table(p['text'])}
        if method == 'damai_add':
            projects = p['projects'] if 'projects' in p else parse_damai_table(p['text'])
            if not projects:
                raise BookError('没有项目数据')
            at = (p.get('at') or '').strip()
            if not at:
                raise BookError('请填写读取时间')
            used = {snap['id'] for snap in f.book['damai']}
            n = len(used) + 1
            while f'd{n}' in used:
                n += 1
            item = {'id': f'd{n}', 'at': at, 'note': p.get('note', ''), 'projects': projects}
            f.replace_book(apply(f.book, [{'op': 'add', 'list': 'damai', 'item': item}]), '记录大麦销售', at)
            return self.state()
        if method == 'export_inventory':
            out = inventory_count(f.book, p['path'], p.get('rounds'))
            f.log('导出库存盘点', Path(out).name)
            return {'path': str(out)}
        if method == 'export_forecast':
            out = forecast_table(f.book, p['path'])
            f.log('导出票房测算', Path(out).name)
            return {'path': str(out)}
        if method == 'copy_event':
            new = BookFile.create(p['path'], p['password'], copy_event(f.book, p.get('name', ''), p.get('year'), int(p.get('shift_days', 0))))
            new.log('由上一届复制', f.path.name)
            self.file = new
            return self.state()
        if method == 'change_password':
            f.change_password(p['old'], p['new'])
            return {}
        raise ProtocolError('UNKNOWN_METHOD', '未知方法：' + method)

    def handle(self, line: str) -> dict:
        rid = None
        try:
            try:
                req = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ProtocolError('PROTOCOL', '请求不是有效 JSON') from exc
            if not isinstance(req, dict) or not isinstance(req.get('method'), str):
                raise ProtocolError('PROTOCOL', '请求格式错误')
            rid = req.get('id')
            params = req.get('params') or {}
            with contextlib.redirect_stdout(sys.stderr):
                result = self.dispatch(req['method'], params)
            return {'id': rid, 'ok': True, 'result': result}
        except ProtocolError as exc:
            return {'id': rid, 'ok': False, 'error': {'code': exc.code, 'message': str(exc)}}
        except WrongPassword as exc:
            return {'id': rid, 'ok': False, 'error': {'code': 'PASSWORD', 'message': str(exc)}}
        except (BookError, FileNotFoundError, FileExistsError) as exc:
            return {'id': rid, 'ok': False, 'error': {'code': 'INPUT', 'message': str(exc)}}
        except KeyError as exc:
            return {'id': rid, 'ok': False, 'error': {'code': 'PROTOCOL', 'message': f'缺少参数：{exc.args[0]}'}}
        except Exception as exc:  # one bad request must never kill the sidecar
            print(traceback.format_exc(), file=sys.stderr)
            return {'id': rid, 'ok': False, 'error': {'code': 'UNEXPECTED', 'message': f'{type(exc).__name__}: {exc}'}}


def main():
    session = Session()
    while True:
        line = sys.stdin.buffer.readline(MAX_LINE + 1)
        if not line:
            break
        if len(line) > MAX_LINE:
            while line and not line.endswith(b'\n'):
                line = sys.stdin.buffer.readline(MAX_LINE + 1)
            reply = {'id': None, 'ok': False, 'error': {'code': 'PROTOCOL', 'message': '请求超过8MiB'}}
        else:
            reply = session.handle(line.decode('utf-8', errors='replace'))
        sys.stdout.write(json.dumps(reply, ensure_ascii=False, default=str) + '\n')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
