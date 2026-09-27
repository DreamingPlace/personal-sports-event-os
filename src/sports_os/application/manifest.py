import json
import tomllib
from pathlib import Path
from ..kernel.data import KernelError

PROFILES={
 'non-ticketed-event':('core.schedule','core.venue','project.tasks'),
 'ticketed-indoor-event':('core.schedule','core.venue','ticketing.pricing','ticketing.seating','ticketing.inventory','demand.multiplicative','finance.revenue'),
 'multi-session-tournament':('core.schedule','core.venue','ticketing.pricing','ticketing.seating','ticketing.inventory','demand.multiplicative','finance.revenue','product.pass'),
}

def parse_manifest(path):
    with Path(path).open('rb') as f:return tomllib.load(f)

def render_manifest(manifest):
    lines=['[project]']
    for key,value in manifest['project'].items():
        # TOML has no null; empty approval is still invalid when marked approved.
        value='' if value is None else value
        lines.append(f'{key} = {json.dumps(value,ensure_ascii=False)}')
    lines+=['','[modules]']
    for key,value in sorted(manifest['modules'].items()):lines.append(f'{json.dumps(key)} = {str(value).lower()}')
    return '\n'.join(lines)+'\n'

def safe_path(workspace,path):
    root=Path(workspace).resolve()
    if root==Path('/Volumes') or Path('/Volumes') in root.parents:raise KernelError('不得读写/Volumes；使用独立本地工作目录')
    target=Path(path);target=(target if target.is_absolute() else root/target).resolve()
    if target!=root and root not in target.parents:raise KernelError('路径超出工作目录（含符号链接）')
    return target
