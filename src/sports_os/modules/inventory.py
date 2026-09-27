from collections import defaultdict
from .common import *

class Inventory(RowsModule):
    module_id='ticketing.inventory'
    requires_capabilities=('capacity',)
    optional_capabilities=('rights',)
    identity=('inventory_id',)
    row_schema=obj(dict(inventory_id=S,session_id=S,zone_id=S,tier=S,channel=S,
        status={'enum':['AVAILABLE','SOLD','LOCKED','PAID_RESERVED']},
        allocation_type={'enum':['PUBLIC','PAID_RIGHTS']},quantity=I,as_of=S,source_ref=S))

    def validate(self,c,g):
        super().validate(c,g)
        for r in self.rows(c):moment(r['as_of'])

    def cross_validate(self,c,g):
        pools=c.provider('capacity');rights=c.provider('rights',required=False) or {};groups=defaultdict(list)
        for r in self.rows(c):
            require(pool_key(r) in pools,'库存座区不存在');groups[pool_key(r)].append(r)
            require(r['status']!='PAID_RESERVED' or r['allocation_type']=='PAID_RIGHTS','预留标记错误')
        for key,pool in pools.items():
            rows=groups[key]
            require(sum(r['quantity'] for r in rows)==pool['sellable_capacity'],'库存互斥状态合计不等于可售池')
            require(len({moment(r['as_of']) for r in rows})<=1,'同池库存as_of不同')
            require(sum(r['quantity'] for r in rows if r['allocation_type']=='PAID_RIGHTS')==rights.get(key,{}).get('quantity',0),
                    '权益分配与Rights不一致；禁用Rights不会自动转移库存')
