from collections import defaultdict
from decimal import localcontext, ROUND_HALF_EVEN
from .common import *

class Revenue(Module):
    module_id='finance.revenue'
    module_version='1.1.1'
    requires_capabilities=('capacity','demand','prices','schedule')
    optional_capabilities=('rights',)
    def schema(self):return obj({})

    def cross_validate(self,c,g):
        pools=c.provider('capacity');prices=c.provider('prices');demand=c.provider('demand')
        rights=c.provider('rights',required=False) or {}
        require(bool(demand),'需求结果不能为空')
        for key,pool in pools.items():
            require(price_key(pool) in prices,'收入缺price_class')
            if key in rights:
                r=rights[key]
                require(0<=r['quantity']<=pool['sellable_capacity'] and r['effective_unit_price']>=0,'权益标准化结果无效')
                require(r['billing_basis'] in ('ALLOCATED','REDEEMED'),'权益计费基础无效')
                require(set(r['expected_fulfillment'])==set(demand),'权益履约率必须覆盖当前Demand情景')
                require(all(0<=q<=1 for q in r['expected_fulfillment'].values()),'权益履约率越界')
        require(set(rights)<=set(pools),'权益结果引用未知容量池')
        for rates in demand.values():
            require(set(rates)==set(pools) and all(0<=q<=1 for q in rates.values()),'Demand结果必须完整且在0到1之间')
        if {'low','mid','high'}<=set(demand):
            for key in pools:
                require(demand['low'][key]<=demand['mid'][key]<=demand['high'][key],'情景需求顺序不成立')
                if key in rights:
                    q=rights[key]['expected_fulfillment'];require(q['low']<=q['mid']<=q['high'],'权益情景顺序不成立')

    def calculate(self,c):
        # Bounded input schemas (<=1e12); 80 digits keeps all finite input products exact.
        with localcontext() as context:
            context.prec=80
            context.rounding=ROUND_HALF_EVEN
            return self._calculate(c)

    def _calculate(self,c):
        pools=c.provider('capacity');prices=c.provider('prices');demand=c.provider('demand')
        rights=c.provider('rights',required=False) or {};schedule=c.provider('schedule')
        rows=[]
        for key,pool in sorted(pools.items()):
            public_price=prices[price_key(pool)];right=rights.get(key)
            quantity=right['quantity'] if right else 0
            effective=right['effective_unit_price'] if right else ZERO
            public=pool['sellable_capacity']-quantity
            row=dict(session_id=pool['session_id'],zone_id=pool['zone_id'],tier=pool['tier'],price_class_id=pool['price_class_id'],
                stage=schedule['sessions'][pool['session_id']]['stage'],physical_capacity=pool['physical_capacity'],
                sellable_capacity=pool['sellable_capacity'],public_capacity=public,paid_rights=quantity,
                price=public_price,full_revenue=D(public)*public_price+D(quantity)*effective,scenarios={})
            for name,rates in demand.items():
                q=rates[key];fulfillment=right['expected_fulfillment'][name] if right else ZERO
                public_tickets=D(public)*q;fulfilled=D(quantity)*fulfillment
                basis=right['billing_basis'] if right else None
                billed=D(quantity) if basis=='ALLOCATED' else fulfilled
                row['scenarios'][name]=dict(public_expected_tickets=public_tickets,rights_allocated=quantity,
                    rights_expected_fulfilled=fulfilled,rights_revenue_tickets=billed,
                    revenue_basis=basis,revenue_tickets=public_tickets+billed,
                    fulfilled_tickets=public_tickets+fulfilled,public_revenue=public_tickets*public_price,
                    rights_revenue=billed*effective,revenue=public_tickets*public_price+billed*effective)
            rows.append(row)
        def aggregate(items):
            physical=sum(r['physical_capacity'] for r in items);capacity=sum(r['sellable_capacity'] for r in items)
            full=sum((r['full_revenue'] for r in items),ZERO)
            result=dict(physical_seat_opportunities=physical,sellable_seat_opportunities=capacity,full_revenue=full,
                        sellable_rate=D(capacity)/physical if physical else None,full_average_price=full/capacity if capacity else None,scenarios={})
            for name in demand:
                fields=('public_expected_tickets','rights_allocated','rights_expected_fulfilled','rights_revenue_tickets',
                        'revenue_tickets','fulfilled_tickets','public_revenue','rights_revenue','revenue')
                totals={f:sum((r['scenarios'][name][f] for r in items),ZERO) for f in fields}
                bases=defaultdict(int)
                for r in items:
                    v=r['scenarios'][name]
                    if v['revenue_basis']:bases[v['revenue_basis']]+=v['rights_allocated']
                totals['revenue_basis']=dict(sorted(bases.items()))
                totals['average_price_per_revenue_ticket']=totals['revenue']/totals['revenue_tickets'] if totals['revenue_tickets'] else None
                totals['average_revenue_per_fulfilled_ticket']=totals['revenue']/totals['fulfilled_tickets'] if totals['fulfilled_tickets'] else None
                result['scenarios'][name]=totals
            return result
        groups={}
        for group,key in [('by_stage','stage'),('by_tier','tier'),('by_session','session_id')]:
            buckets=defaultdict(list)
            for row in rows:buckets[row[key]].append(row)
            groups[group]={k:aggregate(v) for k,v in sorted(buckets.items())}
        # Sensitivities are arithmetic on standardized results, not a second demand model.
        sensitivity={}
        for name,rates in demand.items():
            delta=sum((D(pools[k]['sellable_capacity']-rights.get(k,{}).get('quantity',0))*
                       (min(D(1),q+D('.01'))-q)*prices[price_key(pools[k])] for k,q in rates.items()),ZERO)
            sensitivity[name]=dict(public_demand_plus_1pp_delta=delta,
                public_price_plus_1percent_delta=sum((D(r['public_capacity'])*rates[(r['session_id'],r['zone_id'],r['tier'])]*r['price']*D('.01') for r in rows),ZERO))
        return dict(unit='DEMO_CURRENCY',totals=aggregate(rows),rows=rows,**groups,sensitivity=sensitivity,
                    notes=['全程Decimal；货币仅在显示层舍入。','权益收入按billing_basis确认；履约票张始终乘履约率。',
                           '容量票房不加通票或旅行包营业额；产品金额另行查看。',
                           '敏感性仅改变公开池价格/需求，权益合同输入保持不变，不是价格弹性预测。'])

    def export(self,c):
        return c.calculate(self.module_id)

    def migrate(self,old_version,old_schema,payload):
        require((old_version,old_schema)==('1.1.0','1'),'不支持的Revenue迁移')
        return payload
