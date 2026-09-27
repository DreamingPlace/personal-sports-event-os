from .common import *

class RuleModule(RowsModule):
    dependencies=('core.schedule',)
    identity=('rule_id',)
    content_schema=None

    def schema(self):
        row=obj(dict(rule_id=S,version=S,content=self.content_schema,valid_from=S,valid_to=S,status=STATUS,approval_ref=NULL_S))
        return obj(dict(rows=arr(row)))

    def validate(self,c,g):
        super().validate(c,g)
        require(len(self.rows(c))==1,'每个已启用规则模块在v1.1只允许一条全局规则')
        for r in self.rows(c):
            require(r['version']==c.project.states[self.module_id].data_version,'规则版本与模块数据版本不一致')
            require(moment(r['valid_to'])>moment(r['valid_from']),'规则有效期为空或倒置')
            approval(r,c,g,self.module_id+'/'+r['rule_id'])
            self.applicability(r,c,g)

    def applicability(self,r,c,g):
        raise NotImplementedError('规则模块必须定义实际适用期间')

    def cover(self,r,lo,hi):
        require(lo is not None and hi is not None and lo<=hi,'业务适用期间缺失或倒置')
        require(moment(r['valid_from'])<=lo and hi<=moment(r['valid_to']),'已批准规则未覆盖实际业务期间')
