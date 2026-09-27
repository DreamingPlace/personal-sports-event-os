from .common import *
from .rule_base import RuleModule

class Transfer(RuleModule):
    module_id='ticketing.transfer'
    content_schema=obj(dict(allowed=BOOL))
    def applicability(self,r,c,g):
        self.cover_session_lifetime(r,c)
