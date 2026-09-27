from .common import *
from .rule_base import RuleModule

class Identity(RuleModule):
    module_id='ticketing.identity'
    content_schema=obj(dict(mode=S))
    def applicability(self,r,c,g):
        self.cover_session_lifetime(r,c)
