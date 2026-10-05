from .common import *

LIFECYCLE=('price_version','status','approval_ref')


class Pricing(RowsModule):
    module_id='ticketing.pricing'
    module_version='1.2.0'
    schema_version='2'
    requires_capabilities=('schedule',)
    provides=('prices',)
    identity=('session_id','price_class_id')
    # Approval and data_version live only in ModuleState; rows carry business facts only.
    row_schema=obj(dict(session_id=S,price_class_id=S,price=N,valid_from=S))

    def validate(self,c,g):
        super().validate(c,g);sessions=c.provider('schedule')['sessions']
        for r in self.rows(c):
            require(r['session_id'] in sessions,'价格场次外键不存在')
            require(D(r['price'])==D(money(D(r['price']))),'票价最多两位小数')
            require(moment(r['valid_from'])<=moment(sessions[r['session_id']]['start_time']),'价格开始晚于场次')

    def calculate(self,c):return {price_key(r):D(r['price']) for r in self.rows(c)}

    def migrate(self,old_version,old_schema,payload):
        require((old_version,old_schema)==('1.1.0','1'),'不支持的Pricing迁移')
        return strip_lifecycle(payload,LIFECYCLE)
