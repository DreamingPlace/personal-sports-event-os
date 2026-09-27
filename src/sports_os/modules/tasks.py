from .common import *

class Tasks(RowsModule):
    module_id='project.tasks'
    optional_dependencies=('core.schedule',)
    identity=('task_id',)
    row_schema=obj(dict(task_id=S,title=S,owner_role=S,due_at=S,depends_on=arr(S),
        status={'enum':['TODO','DOING','DONE']},acceptance=S,proof=NULL_S,
        phase={'enum':['PRE_EVENT','DURING_EVENT','POST_EVENT']}))
    def validate(self,c,g):
        super().validate(c,g);rows=unique(self.rows(c),lambda r:r['task_id'])
        active=set();done=set()
        def visit(key):
            require(key in rows,'任务依赖不存在');require(key not in active,'任务依赖循环')
            if key in done:return
            active.add(key)
            for dep in rows[key]['depends_on']:visit(dep)
            active.remove(key);done.add(key)
        for key,t in rows.items():
            visit(key);moment(t['due_at'])
            require(t['status']!='DONE' or (t['proof'] and t['proof'].strip()),'完成任务缺证据')
    def cross_validate(self,c,g):
        if not c.enabled('core.schedule'):return
        s=c.provider('schedule')
        for t in self.rows(c):
            due=moment(t['due_at'])
            if t['phase']=='PRE_EVENT':require(s['start'] is not None and due<s['start'],'赛前任务时序错误')
            if t['phase']=='POST_EVENT':require(s['end'] is not None and due>=s['end'],'赛后任务时序错误')
