"""Shared module utilities, not a central business schema or dispatcher."""
from decimal import Decimal, ROUND_HALF_UP
from ..kernel.contract import Module
from ..kernel.data import KernelError, moment
from ..kernel.diff import changes

S={'type':'string','minLength':1}
I={'type':'integer','minimum':0,'maximum':10**12}
N={'type':'number','minimum':0,'maximum':10**12}
RATE={'type':'number','minimum':0,'maximum':1}
BOOL={'type':'boolean'}
NULL_S={'type':['string','null']}
STATUS={'enum':['DRAFT','APPROVED','PUBLISHED','RETIRED']}
D=lambda x:Decimal(str(x))
ZERO=Decimal(0)

def obj(properties,optional=()):
    return dict(type='object',properties=properties,required=[k for k in properties if k not in optional],additionalProperties=False)

def arr(items):return dict(type='array',items=items)
def money(value):return format(value.quantize(Decimal('.01'),rounding=ROUND_HALF_UP),'f')
def pool_key(row):return (row['session_id'],row['zone_id'],row['tier'])
def price_key(row):return (row['session_id'],row['price_class_id'])

def unique(rows,key):
    keys=[key(r) for r in rows]
    if len(keys)!=len(set(keys)):raise KernelError('重复业务键')
    return dict(zip(keys,rows))

def require(condition,message):
    if not condition:raise KernelError(message)

def approval(row,context,gate,source):
    active=context.project.states[source.split('/')[0]] if source.split('/')[0] in context.project.states else None
    must=context.for_release or (active and active.status in ('APPROVED','PUBLISHED')) or row['status'] in ('APPROVED','PUBLISHED')
    if must and not (row['status'] in ('APPROVED','PUBLISHED') and isinstance(row.get('approval_ref'),str) and row['approval_ref'].strip()):
        gate.add('APPROVAL',source,'批准状态与非空approval_ref',row['status'])

class RowsModule(Module):
    row_schema=None
    identity=()

    def schema(self):return obj({'rows':arr(self.row_schema)})
    def rows(self,context):return context.payload(self.module_id)['rows']
    def key(self,row):return tuple(row[k] for k in self.identity)
    def validate(self,context,gate):unique(self.rows(context),self.key)
    def canonical_row(self,row):return row
    def diff(self,old,new):
        def keyed(payload):return {'/'.join(map(str,self.key(r))):self.canonical_row(r) for r in payload['rows']}
        return changes(keyed(old),keyed(new))
    def export(self,context):return context.payload(self.module_id)

class ApprovedRowsModule(RowsModule):
    version_field='version'

    def prepare_revision(self,payload,data_version,approval_ref=None):
        from copy import deepcopy
        payload=deepcopy(payload)
        for row in payload['rows']:
            row[self.version_field]=data_version
            row['status']='APPROVED' if approval_ref else 'DRAFT'
            row['approval_ref']=approval_ref
        return payload
