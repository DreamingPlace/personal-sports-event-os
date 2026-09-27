from zoneinfo import ZoneInfo
from decimal import localcontext, ROUND_HALF_EVEN
from .data import KernelError, _shape
from .findings import GateResult
from .contract import Context

S={'type':'string','minLength':1}
MANIFEST={'type':'object','required':['project','modules'],'additionalProperties':False,'properties':{
 'project':{'type':'object','required':['id','name','timezone','version','synthetic','status','approval_ref'],
 'additionalProperties':False,'properties':{'id':S,'name':S,'timezone':S,'version':S,'synthetic':{'const':True},
 'status':{'enum':['DRAFT','APPROVED','PUBLISHED']},'approval_ref':{'type':['string','null']}}},
 'modules':{'type':'object','additionalProperties':{'type':'boolean'}}}}

def approved(status, ref):
    return status in ('APPROVED','PUBLISHED') and isinstance(ref,str) and bool(ref.strip())

def validate_project(project, registry, for_release=False):
    gate=GateResult()
    try:
        _shape(project.manifest,MANIFEST,'manifest')
        ZoneInfo(project.manifest['project']['timezone'])
        order=registry.order(project.enabled)
        for ref in project.evidence:
            if not isinstance(ref,dict) or not isinstance(ref.get('source_ref'),str) or not ref['source_ref'].strip():
                raise KernelError('Evidence必须有非空source_ref；不自动声称已经核实来源')
    except (ValueError,TypeError,KeyError) as e:
        gate.add('K001','manifest/dependencies/evidence','有效内核契约',str(e));return gate
    meta=project.manifest['project'];releasing=for_release or meta['status']=='PUBLISHED'
    if (releasing or meta['status']=='APPROVED') and not approved(meta['status'],meta['approval_ref']):
        gate.add('K002','project/approval_ref','人工批准状态及引用',meta['status'])
    for key in order:
        try:
            m=registry.get(key);state=project.states[key]
            if (state.module_version,state.schema_version)!=(m.module_version,m.schema_version):
                raise KernelError('插件或schema版本不匹配；必须显式迁移，不能静默解释')
            if not isinstance(state.data_version,str) or not state.data_version.strip():raise KernelError('缺少data_version')
            if state.status not in ('DRAFT','APPROVED','PUBLISHED'):raise KernelError('未知模块状态')
            _shape(state.payload,m.schema(),key)
            if (releasing or state.status in ('APPROVED','PUBLISHED')) and not approved(state.status,state.approval_ref):
                gate.add('K002',key,'人工批准状态及引用',state.status)
        except (ValueError,TypeError,KeyError,ArithmeticError) as e:
            gate.add('K003',key,'兼容版本及独立payload schema',str(e))
    if gate.status=='BLOCK':return gate
    context=Context(project,registry,releasing)
    for key in order:
        try:
            with localcontext() as decimal_context:
                decimal_context.prec=80
                decimal_context.rounding=ROUND_HALF_EVEN
                registry.get(key).validate(context,gate)
        except (ValueError,TypeError,KeyError,ArithmeticError,RecursionError) as e:
            gate.add('M_INPUT',key,'可验证的模块输入',str(e))
    if gate.status!='BLOCK':
        for key in order:
            try:
                m=registry.get(key)
                with localcontext() as decimal_context:
                    decimal_context.prec=80
                    decimal_context.rounding=ROUND_HALF_EVEN
                    m.cross_validate(context,gate)
                    if releasing:m.release_requirements(context,gate)
            except (ValueError,TypeError,KeyError,ArithmeticError) as e:
                gate.add('M_CROSS',key,'跨模块约束和发布条件',str(e))
    return gate
