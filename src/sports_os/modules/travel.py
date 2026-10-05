from .common import *
from .products import Products, BASE

class Travel(Products):
    module_id='product.travel'
    allowed_types=('TRAVEL',)
    row_schema=obj(dict(BASE,travel=obj(dict(guests=I,expected_rooms=I,room_quantity=I,nights=I,
        room_cost=N,service_per_guest=N,other_cost=N,pricing_method={'enum':['markup','margin']},
        actual_method={'enum':['markup','margin']},rate=RATE,quoted_non_ticket=N))))

    def validate(self,c,g):
        super().validate(c,g)
        for p in self.rows(c):
            t=p['travel']
            require(t['room_quantity']==t['expected_rooms']>0 and t['guests']>0 and t['nights']>0,'房间/人数/房晚不成立或重复计房')
            require(all(x['ticket_quantity']==t['guests'] for x in p['included_sessions']),'每场票张必须等于人数')
            require(D(t['quoted_non_ticket'])==D(money(D(t['quoted_non_ticket']))),'非票报价最多2位小数')
            cost=D(t['room_cost'])*t['room_quantity']*t['nights']+D(t['service_per_guest'])*t['guests']+D(t['other_cost'])
            require(t['pricing_method']!='margin' or t['rate']<1,'margin率不可等于1')
            quote=cost*(1+D(t['rate'])) if t['pricing_method']=='markup' else cost/(1-D(t['rate']))
            require(t['actual_method']==t['pricing_method'] and money(quote)==money(D(t['quoted_non_ticket'])),
                    'markup=成本×(1+率)；margin=成本÷(1-率)，不是相同公式')
            if cost or t['quoted_non_ticket']:
                require(p['price'] is not None and p['price_claim']=='INDEPENDENT','含非票成本/报价的Travel必须有明确独立总价；不得用SUM_FACE_PRICES漏价')

    def cross_validate(self,c,g):
        super().cross_validate(c,g)
        details={r['product_id']:r for r in self.calculate(c)}
        for p in self.rows(c):
            result=details[p['product_id']]
            require(result['total_price']==result['ticket_amount']+D(p['travel']['quoted_non_ticket']),
                    '旅行包门票金额＋非票报价必须等于产品总价')
