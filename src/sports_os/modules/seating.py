from .common import *

HOLDS=('functional_hold','broadcast_hold','free_rights','other_hold')
def sellable(row):return row['physical_capacity']-sum(row[k] for k in HOLDS)

class Seating(RowsModule):
    module_id='ticketing.seating'
    requires_capabilities=('schedule','prices')
    provides=('capacity',)
    identity=('session_id','zone_id','tier')
    row_schema=obj(dict(session_id=S,zone_id=S,tier=S,price_class_id=S,physical_capacity=I,
        visibility={'enum':['CLEAR','RESTRICTED']},**{k:I for k in HOLDS},deduction_refs=obj({k:arr(S) for k in HOLDS})))

    def validate(self,c,g):
        super().validate(c,g)
        sessions=c.provider('schedule')['sessions'];prices=c.provider('prices')
        for r in self.rows(c):
            require(r['session_id'] in sessions and price_key(r) in prices,'座席缺场次或price_class')
            require(0<=sellable(r)<=r['physical_capacity'],'负库存或可售大于物理')
            refs=[x for v in r['deduction_refs'].values() for x in v]
            require(len(refs)==len(set(refs)),'重复扣减来源')
            for k in HOLDS:require(not r[k] or r['deduction_refs'][k],'正数扣减缺来源')

    def calculate(self,c):
        return {pool_key(r):dict(r,sellable_capacity=sellable(r)) for r in self.rows(c)}

    def canonical_row(self,row):return dict(row,sellable_capacity=sellable(row))
