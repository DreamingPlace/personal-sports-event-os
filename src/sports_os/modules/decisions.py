from .common import *

class Decisions(RowsModule):
    module_id='project.decisions'
    identity=('decision_id',)
    row_schema=obj(dict(decision_id=S,issue=S,options=arr(S),decision=S,reason=S,
        approved_by_role=S,effective_at=S,source_ref=S,confirmed=BOOL,changed_paths=arr(S)))
    def validate(self,c,g):
        super().validate(c,g)
        for row in self.rows(c):moment(row['effective_at'])
    def canonical_row(self,row):return dict(row,changed_paths=sorted(row['changed_paths']))
