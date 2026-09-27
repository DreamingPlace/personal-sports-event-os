from dataclasses import dataclass, asdict, field

@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    message: str
    source: str
    expected: object
    actual: object
    suggested_action: str = '修正工作态输入并重新验证；不要修改历史快照'

@dataclass
class GateResult:
    findings: list = field(default_factory=list)

    @property
    def status(self):
        levels={f.severity for f in self.findings}
        return 'BLOCK' if 'BLOCK' in levels else 'WARNING' if 'WARNING' in levels else 'PASS'

    def add(self, rule, source, expected, actual, message='', severity='BLOCK'):
        self.findings.append(Finding(rule,severity,message or rule,source,expected,actual))

    def to_dict(self):
        return {'status':self.status,'findings':[asdict(f) for f in self.findings]}
