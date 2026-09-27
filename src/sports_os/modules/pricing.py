from .common import *

class Pricing(RowsModule):
    module_id='ticketing.pricing'
    dependencies=('core.schedule',)
    provides=('prices',)
    identity=('session_id','price_class_id')
    row_schema=obj(dict(session_id=S,price_class_id=S,price=N,price_version=S,status=STATUS,valid_from=S,approval_ref=NULL_S))

    def validate(self,c,g):
        super().validate(c,g);sessions=c.provider('schedule')['sessions']
        version=c.project.states[self.module_id].data_version
        for r in self.rows(c):
            require(r['session_id'] in sessions,'价格场次外键不存在')
            require(r['price_version']==version,'价格版本与模块数据版本不同')
            require(D(r['price'])==D(money(D(r['price']))),'票价最多两位小数')
            require(moment(r['valid_from'])<=moment(sessions[r['session_id']]['start_time']),'价格开始晚于场次')
            approval(r,c,g,self.module_id+'/'+r['price_class_id'])

    def calculate(self,c):return {price_key(r):D(r['price']) for r in self.rows(c)}
