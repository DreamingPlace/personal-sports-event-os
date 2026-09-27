from .common import *
from .rule_base import RuleModule

class Refund(RuleModule):
    module_id='ticketing.refund'
    content_schema=obj(dict(coverage_start=S,coverage_end=S,windows=arr(obj(dict(start=S,end=S,fee_rate=RATE)))))
    def applicability(self,r,c,g):
        p=r['content'];lo,hi=moment(p['coverage_start']),moment(p['coverage_end'])
        windows=sorted((moment(w['start']),moment(w['end'])) for w in p['windows'])
        require(lo<hi and windows,'退款覆盖期和窗口不能为空')
        cursor=lo
        for a,b in windows:
            require(a==cursor,'退款窗口重叠或空档')
            require(a<b<=hi,'退款窗口倒置或超出范围');cursor=b
        require(cursor==hi,'退款末尾出现空档')
        self.cover(r,lo,hi)
