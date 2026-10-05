from .common import *
from .rule_base import RuleModule

class Launch(RuleModule):
    module_id='ticketing.launch'
    content_schema=obj(dict(denominator={'const':'PUBLIC_POOL'},rounds=arr(obj(dict(at=S,fraction=RATE)))))
    def applicability(self,r,c,g):
        rounds=r['content']['rounds'];times=[moment(x['at']) for x in rounds];s=self.scoped_schedule(r,c)
        require(rounds and sum((D(x['fraction']) for x in rounds),ZERO)==1,'各轮比例必须闭合')
        require(all(D(x['fraction'])>0 for x in rounds),'每轮开票比例必须大于0；不开票的轮次请删除')
        require(times==sorted(set(times)),'开票轮次时间必须严格递增')
        require(s['sales_start'] is not None and s['sales_end'] is not None and s['start'] is not None,'开票需要销售期及场次')
        require(all(s['sales_start']<=t<s['sales_end'] and t<s['start'] for t in times),'开票时点超出销售期或晚于首场')
        self.cover(r,min(times),max(times))
        require(max(times)<moment(r['valid_to']),'开票时点必须在规则半开有效区间内')
