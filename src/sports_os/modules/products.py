from .common import *

COMPONENT=obj(dict(session_id=S,zone_id=S,tier=S,ticket_quantity=I))
BASE=dict(product_id=S,product_type={'enum':['SINGLE','PASS','TRAVEL']},included_sessions=arr(COMPONENT),
          price={'type':['number','null'],'minimum':0,'maximum':10**12},price_claim={'enum':['INDEPENDENT','SUM_FACE_PRICES']})

class Products(RowsModule):
    requires_capabilities=('capacity','prices')
    identity=('product_id',)
    row_schema=obj(BASE)
    allowed_types=()

    def canonical_row(self,row):
        return dict(row,included_sessions=sorted(row['included_sessions'],key=pool_key))

    def validate(self,c,g):
        super().validate(c,g)
        for r in self.rows(c):
            require(r['product_type'] in self.allowed_types,'产品类型不属于此模块')
            if r['price'] is not None:require(D(r['price'])==D(money(D(r['price']))),'产品总价最多2位小数')
            require(bool(r['included_sessions']),'产品占票映射为空')
            unique(r['included_sessions'],pool_key)
            require(all(x['ticket_quantity']>0 for x in r['included_sessions']),'每份占票数必须为正')
            if r['product_type']=='SINGLE':require(sum(x['ticket_quantity'] for x in r['included_sessions'])==1,'单场票只占一张')

    def calculate(self,c):
        pools=c.provider('capacity');prices=c.provider('prices');out=[]
        for p in self.rows(c):
            face=sum((prices[price_key(pools[pool_key(x)])]*x['ticket_quantity'] for x in p['included_sessions']),ZERO)
            price=face if p['price'] is None else D(p['price'])
            out.append(dict(product_id=p['product_id'],ticket_quantity=sum(x['ticket_quantity'] for x in p['included_sessions']),
                            ticket_amount=face,non_ticket_amount=price-face,total_price=price))
        return out

    def export(self,c):
        return dict(inputs=c.payload(self.module_id),calculated=c.calculate(self.module_id))

    def cross_validate(self,c,g):
        pools=c.provider('capacity')
        for p in self.rows(c):
            for x in p['included_sessions']:
                require(pool_key(x) in pools,'产品占票引用不存在')
                require(x['ticket_quantity']<=pools[pool_key(x)]['sellable_capacity'],'单份占票超过可售池')
        details={x['product_id']:x for x in self.calculate(c)}
        for p in self.rows(c):
            result=details[p['product_id']]
            require(p['price'] is not None or p['price_claim']=='SUM_FACE_PRICES','独立产品漏价')
            require(p['price_claim']!='SUM_FACE_PRICES' or result['total_price']==result['ticket_amount'],'声称票价之和但价格不符')

class Pass(Products):
    module_id='product.pass'
    allowed_types=('SINGLE','PASS')
