from datetime import timedelta
from .common import *
from .rule_base import RuleModule

class RightsReturn(RuleModule):
    module_id='ticketing.rights_return'
    content_schema=obj(dict(hours_before=I))
    def applicability(self,r,c,g):
        schedule=self.scoped_schedule(r,c);rows=schedule['sessions'].values()
        deadlines=[moment(s['start_time'])-timedelta(hours=r['content']['hours_before']) for s in rows]
        require(bool(deadlines),'权益回流需要场次')
        require(schedule['sales_start'] is not None and schedule['sales_start']<=min(deadlines),'登记开始不能晚于回流节点')
        self.cover(r,schedule['sales_start'],max(deadlines))
        require(max(deadlines)<moment(r['valid_to']),'回流节点必须落在半开有效区间内')
