"""Actual v1.1.1 acceptance; retain the frozen v1.0/v1.1 reports."""
import io
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests.run_acceptance import RecordingResult


def main():
    stream=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),top_level_dir=str(ROOT))
    result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=RecordingResult).run(suite)
    new=[r for r in result.records if '.test_v111_hardening.' in r['test']]
    old=[r for r in result.records if r not in new]
    hard=[r for r in new if '.test_HARD_' in r['test']]
    passed=lambda rows:sum(r['result']=='PASS' for r in rows)
    ok=result.wasSuccessful() and not result.skipped and len(old)==140 and len(hard)==24
    for row in new:
        parts=row['input'].split(' | ')
        if len(parts)==3:
            row['input']=parts[1];row['expected']=parts[2]
            if row['result']=='PASS':row['actual']='实际断言通过：'+parts[2]
    report=dict(verdict='PASS' if ok else 'FAIL',base_commit='8ffdfb6b1905453e1940e968c506cfbd8d7dda5a',
        created_at=datetime.now(timezone.utc).isoformat(),python=sys.version.split()[0],
        old_count=len(old),old_pass=passed(old),new_count=len(new),new_pass=passed(new),hard_count=len(hard),
        tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),tests=result.records)
    out=ROOT/'outputs/v1_1_1';out.mkdir(parents=True,exist_ok=True)
    log=stream.getvalue().replace(str(ROOT),'<PROJECT>')
    (out/'ALL_TESTS.log').write_text(log,encoding='utf-8')
    (out/'acceptance-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# V1_1_1_TEST_REPORT','',f"验收：**{report['verdict']}**",'',
        f"base commit: `{report['base_commit']}`",'',
        f"old tests: {len(old)}; passed: {passed(old)}",f"new tests: {len(new)}; passed: {passed(new)}",'',
        f"total: {result.testsRun}; fail: {len(result.failures)}; error: {len(result.errors)}; skip: {len(result.skipped)}",'',
        f"Python {report['python']}；运行时间 {report['created_at']}。",'',
        '原140项测试文件均未修改；新增测试使用v1.0适配器生成当前合成数据，另直接读取原v1.1工作样本验证显式迁移。',
        'HARD-001～024均为独立执行的测试。实际列来自unittest断言结果，不是预填PASS；任一异常、失败或跳过均不算通过。','',
        '## 新增测试：输入 / 预期 / 实际','', '|测试项|输入|预期|实际|PASS/FAIL|','|---|---|---|---|---|']
    def table(rows):
        for r in rows:
            lines.append('|'+ '|'.join(str(r[k]).replace('|','／').replace('\n',' ') for k in ('test','input','expected','actual','result'))+'|')
    table(new)
    lines+=['','## 保留基线测试','','|测试项|输入|预期|实际|PASS/FAIL|','|---|---|---|---|---|']
    table(old)
    lines+=['','复现：`python tests/run_v111_acceptance.py`。返回0且140项原测试及24项指定硬化测试均实际执行才算PASS。',
            '完整日志与机器可读结果：outputs/v1_1_1/。本验收仅覆盖离线合成原型，不认证真实批准、票务生产系统或现场安全。']
    (ROOT/'V1_1_1_TEST_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(report['verdict'],result.testsRun,'tests;',len(old),'old;',len(new),'new')
    return 0 if ok else 1

if __name__=='__main__':raise SystemExit(main())
