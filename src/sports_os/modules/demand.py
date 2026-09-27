from .common import *

RATES={'type':'object','additionalProperties':RATE}

class MultiplicativeDemandModel(Module):
    module_id='demand.multiplicative'
    provides=('demand',)
    requires_capabilities=('capacity',)
    def schema(self):
        return obj(dict(scenarios={'type':'object','additionalProperties':obj(dict(session_rates=RATES,tier_rates=RATES))}))
    def validate(self,c,g):
        pools=c.provider('capacity');p=c.payload(self.module_id)['scenarios']
        require(bool(p),'需求情景不可为空')
        for rates in p.values():
            require(set(rates['session_rates'])=={r['session_id'] for r in pools.values()},'场次需求必须完整，不能猜默认值')
            require(set(rates['tier_rates'])=={r['tier'] for r in pools.values()},'票档需求必须完整')
    def calculate(self,c):
        pools=c.provider('capacity')
        return {scenario:{key:D(r['session_rates'][seat['session_id']])*D(r['tier_rates'][seat['tier']]) for key,seat in pools.items()}
                for scenario,r in c.payload(self.module_id)['scenarios'].items()}

class DirectDemandModel(Module):
    module_id='demand.direct'
    provides=('demand',)
    requires_capabilities=('capacity',)
    def schema(self):
        return obj(dict(scenarios={'type':'object','additionalProperties':arr(obj(dict(session_id=S,zone_id=S,tier=S,rate=RATE)))}))
    def validate(self,c,g):
        pools=c.provider('capacity');scenarios=c.payload(self.module_id)['scenarios']
        require(bool(scenarios),'情景不可为空')
        for rows in scenarios.values():require(set(unique(rows,pool_key))==set(pools),'直接需求必须覆盖所有容量池且不重复')
    def calculate(self,c):
        return {name:{pool_key(r):D(r['rate']) for r in rows} for name,rows in c.payload(self.module_id)['scenarios'].items()}
    def diff(self,a,b):
        def keyed(p):return {n:{'/'.join(pool_key(r)):r['rate'] for r in rows} for n,rows in p['scenarios'].items()}
        return changes(keyed(a),keyed(b))
