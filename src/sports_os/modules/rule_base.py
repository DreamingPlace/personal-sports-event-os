from .common import *

SCOPE=obj(dict(type={'enum':['ALL','SESSION']},session_ids=arr(S)),optional=('session_ids',))

class RuleModule(ApprovedRowsModule):
    module_version='1.1.1'
    schema_version='2'
    requires_capabilities=('schedule',)
    identity=('rule_id',)
    content_schema=None

    def schema(self):
        row=obj(dict(rule_id=S,version=S,scope=SCOPE,content=self.content_schema,valid_from=S,valid_to=S,status=STATUS,approval_ref=NULL_S))
        return obj(dict(rows=arr(row)))

    def session_ids(self,r,c):
        available=set(c.provider('schedule')['sessions']);scope=r['scope']
        if scope['type']=='ALL':
            require('session_ids' not in scope,'ALL不得附加session_ids过滤器')
            return available
        ids=scope.get('session_ids',[])
        require(bool(ids) and len(ids)==len(set(ids)),'SESSION需要非空且唯一session_ids')
        require(set(ids)<=available,'Scope引用不存在的Session')
        return set(ids)

    def scoped_schedule(self,r,c):
        schedule=c.provider('schedule');ids=self.session_ids(r,c)
        sessions={k:v for k,v in schedule['sessions'].items() if k in ids}
        return dict(schedule,sessions=sessions,
                    start=min((moment(s['start_time']) for s in sessions.values()),default=None),
                    end=max((moment(s['end_time']) for s in sessions.values()),default=None))

    def validate(self,c,g):
        super().validate(c,g);rows=self.rows(c);intervals=[]
        require(bool(rows),'已启用规则模块需要至少一条明确规则')
        for r in rows:
            require(r['version']==c.project.states[self.module_id].data_version,'规则版本与模块数据版本不一致')
            lo,hi=moment(r['valid_from']),moment(r['valid_to'])
            require(hi>lo,'规则有效期为空或倒置')
            sessions=self.session_ids(r,c)
            for ids,a,b in intervals:
                require(not (sessions & ids and max(lo,a)<min(hi,b)),'规则Scope适用Session与有效期重叠，不能唯一决策')
            intervals.append((sessions,lo,hi))
            approval(r,c,g,self.module_id+'/'+r['rule_id'])
        for r in rows:self.applicability(r,c,g)

    def applicability(self,r,c,g):
        raise NotImplementedError('规则模块必须定义实际适用期间')

    def cover(self,r,lo,hi):
        require(lo is not None and hi is not None and lo<=hi,'业务适用期间缺失或倒置')
        require(moment(r['valid_from'])<=lo and hi<=moment(r['valid_to']),'已批准规则未覆盖实际业务期间')

    def cover_session_lifetime(self,r,c):
        """Adjacent rule versions may jointly cover each scoped session, without gaps."""
        schedule=self.scoped_schedule(r,c);lo=schedule['sales_start']
        require(lo is not None,'规则需要销售开始时间')
        for sid,session in schedule['sessions'].items():
            end=moment(session['end_time']);cursor=lo
            require(lo<=end,'销售开始晚于Scope内场次结束，规则业务期间倒置')
            intervals=sorted((moment(x['valid_from']),moment(x['valid_to'])) for x in self.rows(c) if sid in self.session_ids(x,c))
            for a,b in intervals:
                if b<=cursor:continue
                if a>cursor:break
                cursor=b
            require(cursor>=end,'规则有效期未连续覆盖适用Session的销售至结束期间')

    def canonical_row(self,row):
        scope=row['scope']
        if scope['type']=='SESSION':scope=dict(scope,session_ids=sorted(scope['session_ids']))
        return dict(row,scope=scope)

    def migrate(self,old_version,old_schema,payload):
        require((old_version,old_schema)==('1.1.0','1'),'不支持的Rule迁移')
        for row in payload['rows']:row['scope']={'type':'ALL'}
        return payload
