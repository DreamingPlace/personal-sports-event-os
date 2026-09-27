from .common import *
from .rule_base import RuleModule

class Transfer(RuleModule):
    module_id='ticketing.transfer'
    content_schema=obj(dict(allowed=BOOL))
    def applicability(self,r,c,g):
        schedule=c.provider('schedule')
        # A prohibition must remain valid as long as a transferable ticket can be used.
        self.cover(r,schedule['sales_start'],schedule['end'])
