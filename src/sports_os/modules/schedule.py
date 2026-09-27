from .common import *
from zoneinfo import ZoneInfo

class Schedule(RowsModule):
    module_id='core.schedule'
    provides=('schedule',)
    identity=('session_id',)
    row_schema=obj(dict(session_id=S,event_id=S,stage=S,start_time=S,end_time=S))

    def schema(self):
        return obj(dict(rows=arr(self.row_schema),sales_start=S,sales_end=S),optional=('sales_start','sales_end'))

    def validate(self,c,g):
        super().validate(c,g)
        meta=c.project.manifest['project'];rows=self.rows(c)
        for s in rows:
            require(s['event_id']==meta['id'],'场次event_id不属于项目')
            require(moment(s['end_time'])>moment(s['start_time']),'结束早于开始')
        p=c.payload(self.module_id)
        require(('sales_start' in p)==('sales_end' in p),'销售期需要完整起止')
        if 'sales_start' in p:
            require(rows and moment(p['sales_start'])<moment(p['sales_end'])<=max(moment(s['end_time']) for s in rows),'销售期须非空且不晚于末场结束')

    def calculate(self,c):
        p=c.payload(self.module_id);rows=unique(p['rows'],lambda s:s['session_id'])
        return dict(sessions=rows,start=min((moment(s['start_time']) for s in rows.values()),default=None),
                    end=max((moment(s['end_time']) for s in rows.values()),default=None),
                    sales_start=moment(p['sales_start']) if 'sales_start' in p else None,
                    sales_end=moment(p['sales_end']) if 'sales_end' in p else None)
