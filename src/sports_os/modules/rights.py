from .common import *

class Rights(RowsModule):
    module_id='ticketing.rights'
    module_version='1.1.1'
    schema_version='2'
    requires_capabilities=('capacity','prices')
    provides=('rights',)
    identity=('session_id','zone_id','tier')
    row_schema=obj(dict(session_id=S,zone_id=S,tier=S,quantity=I,billing_basis={'enum':['ALLOCATED','REDEEMED']},
        strategy={'enum':['FACE_VALUE','FIXED_PRICE','DISCOUNT_RATE']},value=N,
        expected_fulfillment={'type':'object','additionalProperties':RATE}))

    def validate(self,c,g):
        super().validate(c,g);pools=c.provider('capacity')
        for r in self.rows(c):
            key=pool_key(r);require(key in pools,'权益引用不存在的座区')
            require(r['quantity']<=pools[key]['sellable_capacity'],'权益数量超过可售池')
            require(r['strategy']!='DISCOUNT_RATE' or r['value']<=1,'DISCOUNT_RATE表示实付比例，必须0到1')
            require(bool(r['expected_fulfillment']),'权益履约情景不可缺失')

    def calculate(self,c):
        pools=c.provider('capacity');prices=c.provider('prices');result={}
        for r in self.rows(c):
            key=pool_key(r);face=prices[price_key(pools[key])]
            effective={'FACE_VALUE':lambda:face,'FIXED_PRICE':lambda:D(r['value']),
                       'DISCOUNT_RATE':lambda:face*D(r['value'])}[r['strategy']]()
            result[key]=dict(quantity=r['quantity'],effective_unit_price=effective,billing_basis=r['billing_basis'],
                             expected_fulfillment={k:D(v) for k,v in r['expected_fulfillment'].items()})
        return result

    def migrate(self,old_version,old_schema,payload):
        require((old_version,old_schema)==('1.1.0','1'),'不支持的Rights迁移')
        for row in payload['rows']:row['billing_basis']='REDEEMED'
        return payload
