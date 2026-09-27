from dataclasses import dataclass, asdict
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo
import re
from ..models import assert_model, ModelError, sellable, canonical
from ..models.core import moment, seating_key, _shape
from ..models.schema import obj, arr, S, RATE, I, HOLD_FIELDS
from ..revenue import calculate, product_details

RULES={
 'Q001':'结构、类型、唯一键、外键及缺失值', 'Q002':'Excel错误值与计算错误',
 'Q003':'空单元格或缺失引用', 'Q004':'硬编码摘要与派生值', 'Q005':'分项与总计',
 'Q006':'百分比闭合', 'Q007':'同一指标单位一致', 'Q008':'负可售库存',
 'Q009':'容量与付费权益边界', 'Q010':'扣减标识重复', 'Q011':'年度残留',
 'Q012':'开始结束时间与有效期', 'Q013':'赛前任务时序', 'Q014':'退款窗口重叠',
 'Q015':'退款窗口空档', 'Q016':'批准凭证', 'Q017':'草案禁止发布',
 'Q018':'同名内容冲突', 'Q019':'发布件引用规则状态', 'Q020':'统一快照引用',
 'Q021':'通票等于票价之和的声明', 'Q022':'旅行包房间数量', 'Q023':'markup与margin',
 'Q024':'库存守恒与时点', 'Q025':'产品价格与占票结构', 'Q026':'需求情景排序',
 'Q027':'活动版本一致', 'Q028':'任务完成凭证', 'Q029':'规则内容结构',
 'Q030':'可验证的公式范围', 'Q031':'Excel业务检查契约',
}

@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    message: str
    source: str
    expected: object
    actual: object
    suggested_action: str

@dataclass
class GateResult:
    findings: list

    @property
    def status(self):
        return 'BLOCK' if any(f.severity=='BLOCK' for f in self.findings) else 'WARNING' if any(f.severity=='WARNING' for f in self.findings) else 'PASS'

    def to_dict(self):
        return dict(status=self.status,findings=[asdict(f) for f in self.findings])

    def add(self,rule,severity,source,expected,actual,message=None,action='修正输入或补充明确依据，然后重新校验；不得直接改发布件'):
        self.findings.append(Finding(rule,severity,message or RULES[rule],source,expected,actual,action))

def approved(row):
    return row['status'] in ('APPROVED','PUBLISHED') and isinstance(row.get('approval_ref'),str) and bool(row['approval_ref'].strip())

CONTENT_SCHEMAS={
 'refund':obj(dict(coverage_start=S,coverage_end=S,windows=arr(obj(dict(start=S,end=S,fee_rate=RATE))))),
 'launch':obj(dict(denominator={'const':'PUBLIC_POOL'},rounds=arr(obj(dict(at=S,fraction=RATE))))),
 'transfer':obj(dict(allowed={'type':'boolean'})), 'identity':obj(dict(mode=S)),
 'rights_return':obj(dict(hours_before=I)),
}

def _validate(data,for_release=False):
    g=GateResult([])
    try:
        assert_model(data)
    except (ModelError,TypeError,ValueError,KeyError,RecursionError) as e:
        g.add('Q001','BLOCK','$','有效的Event Master v1结构',str(e))
        return g
    zone=ZoneInfo(data['event']['timezone']);year=data['event']['year']
    sessions={s['session_id']:s for s in data['sessions']}
    end=max(moment(s['end_time']) for s in sessions.values())
    start=min(moment(s['start_time']) for s in sessions.values())
    releasing=for_release or data['status']=='PUBLISHED' or data['event']['status']=='PUBLISHED'
    types=[r['rule_type'] for r in data['rules']]
    if (releasing or data['status']=='APPROVED') and (set(types)!=set(CONTENT_SCHEMAS) or len(types)!=len(set(types))):
        g.add('Q029','BLOCK','rules','v1每类全局规则恰好一条：'+','.join(CONTENT_SCHEMAS),types,
              '批准版本不能缺少关键规则或同时引用相互竞争的全局规则')
    if releasing and (not approved(data) or data['event']['status'] not in ('APPROVED','PUBLISHED')):
        g.add('Q017','BLOCK','status/approval_ref','APPROVED/PUBLISHED且有人工批准引用',data['status'])
    if data['status'] in ('APPROVED','PUBLISHED') and not approved(data):
        g.add('Q016','BLOCK','approval_ref','非空批准引用',data['approval_ref'])
    for s in sessions.values():
        src=f"sessions/{s['session_id']}"
        if moment(s['end_time']) <= moment(s['start_time']):
            g.add('Q012','BLOCK',src,'end_time > start_time',[s['start_time'],s['end_time']])
        for field in ('start_time','end_time'):
            if moment(s[field]).astimezone(zone).year!=year:
                g.add('Q011','BLOCK',f'{src}/{field}',year,s[field])
    seatmap={seating_key(s):s for s in data['seating']}
    for s in data['seating']:
        src='seating/'+'/'.join(seating_key(s));capacity=sellable(s)
        if capacity<0:g.add('Q008','BLOCK',src,'sellable_capacity >= 0',capacity)
        if capacity>s['physical_capacity'] or s['paid_rights']>capacity:
            g.add('Q009','BLOCK',src,'0 <= paid_rights <= sellable <= physical',dict(sellable=capacity,physical=s['physical_capacity'],paid=s['paid_rights']))
        refs=[r for values in s['deduction_refs'].values() for r in values]
        if len(refs)!=len(set(refs)):
            g.add('Q010','BLOCK',src,'扣减来源ID在同一场次座区互斥',refs)
        for field in HOLD_FIELDS:
            if s[field]>0 and not s['deduction_refs'][field]:
                g.add('Q003','BLOCK',f'{src}/deduction_refs/{field}','正数扣减有来源ID',[])
    inventory=defaultdict(list)
    for inv in data['inventory']:inventory[seating_key(inv)].append(inv)
    for key,s in seatmap.items():
        pool=inventory[key];quantity=sum(r['quantity'] for r in pool);capacity=sellable(s)
        if quantity != capacity:
            g.add('Q024','BLOCK','inventory/'+'/'.join(key),capacity,quantity,'库存各互斥状态之和必须等于可售总池（不是物理总量）')
        if len({moment(r['as_of']) for r in pool})>1:
            g.add('Q024','BLOCK','inventory/'+'/'.join(key),'同一池使用同一as_of',[r['as_of'] for r in pool])
        reserved=sum(r['quantity'] for r in pool if r['allocation_type']=='PAID_RIGHTS')
        if any(r['status']=='PAID_RESERVED' and r['allocation_type']!='PAID_RIGHTS' for r in pool):
            g.add('Q024','BLOCK','inventory/'+'/'.join(key),'PAID_RESERVED必须属于PAID_RIGHTS','公共池误标付费预留')
        if reserved != s['paid_rights']:
            g.add('Q024','BLOCK','inventory/'+'/'.join(key)+'/PAID_RESERVED',s['paid_rights'],reserved)
    for p in data['prices']:
        src=f"prices/{p['session_id']}/{p['tier']}"
        if p['price']<0:g.add('Q009','BLOCK',src+'/price','非负价格',p['price'])
        if Decimal(str(p['price'])).quantize(Decimal('.01'))!=Decimal(str(p['price'])):
            g.add('Q009','BLOCK',src+'/price','票价最多2位小数',p['price'])
        if p['price_version']!=data['price_version']:
            g.add('Q027','BLOCK',src+'/price_version',data['price_version'],p['price_version'])
        if (p['status'] in ('APPROVED','PUBLISHED') or releasing or data['status']=='APPROVED') and not approved(p):
            g.add('Q016','BLOCK',src,'有效批准状态且有approval_ref',dict(status=p['status'],approval_ref=p['approval_ref']))
        if moment(p['valid_from'])>moment(sessions[p['session_id']]['start_time']):
            g.add('Q012','BLOCK',src+'/valid_from','不晚于该场开始',p['valid_from'])
    for r in data['rules']:
        src=f"rules/{r['rule_id']}";c=r['content']
        if r['version']!=data['rules_version']:
            g.add('Q027','BLOCK',src+'/version',data['rules_version'],r['version'])
        if r['status'] in ('APPROVED','PUBLISHED') and not approved(r):
            g.add('Q016','BLOCK',src,'批准凭证非空',r['approval_ref'])
        if (releasing or data['status']=='APPROVED') and not approved(r):
            g.add('Q019','BLOCK',src,'仅引用已批准规则',r['status'])
        if moment(r['valid_to'])<=moment(r['valid_from']):
            g.add('Q012','BLOCK',src,'valid_to > valid_from',[r['valid_from'],r['valid_to']])
        try:
            _shape(c,CONTENT_SCHEMAS[r['rule_type']],src+'/content')
            if r['rule_type']=='refund':
                lo,hi=moment(c['coverage_start']),moment(c['coverage_end'])
                windows=sorted([(moment(w['start']),moment(w['end'])) for w in c['windows']])
                if hi<=lo or not windows:raise ModelError('退款覆盖期必须非空且起点早于终点')
                cursor=lo
                for a,b in windows:
                    if b<=a:g.add('Q012','BLOCK',src+'/windows','end > start',[a.isoformat(),b.isoformat()])
                    if a<cursor:g.add('Q014','BLOCK',src+'/windows',cursor.isoformat(),a.isoformat(),'退款窗口重叠或超出覆盖起点')
                    if a>cursor:g.add('Q015','BLOCK',src+'/windows',cursor.isoformat(),a.isoformat(),'退款窗口存在空档')
                    if b>hi:g.add('Q014','BLOCK',src+'/windows',hi.isoformat(),b.isoformat(),'窗口超出声明覆盖终点')
                    cursor=max(cursor,b)
                if cursor<hi:g.add('Q015','BLOCK',src+'/windows',hi.isoformat(),cursor.isoformat(),'覆盖终点前存在空档')
                if lo<moment(r['valid_from']) or hi>moment(r['valid_to']):
                    g.add('Q012','BLOCK',src,'退款覆盖期位于规则有效期内',[c['coverage_start'],c['coverage_end']])
            if r['rule_type']=='launch':
                total=sum(Decimal(str(x['fraction'])) for x in c['rounds'])
                if total != Decimal(1):g.add('Q006','BLOCK',src+'/rounds',1,str(total),'各轮使用同一公开池分母，比例之和必须为1')
                times=[moment(x['at']) for x in c['rounds']]
                if times!=sorted(set(times)) or any(t>=start for t in times):
                    g.add('Q012','BLOCK',src+'/rounds','时点严格递增，且早于赛事开始',[x['at'] for x in c['rounds']])
        except (ModelError,KeyError,TypeError,ValueError) as e:
            g.add('Q029','BLOCK',src,'该规则类型的完整结构和有效时间',str(e))
    for t in data['tasks']:
        if t['phase']=='PRE_EVENT' and moment(t['due_at'])>=start:
            g.add('Q013','BLOCK',f"tasks/{t['task_id']}",'赛前准备截止早于赛事首场',t['due_at'])
        if t['phase']=='POST_EVENT' and moment(t['due_at'])<end:
            g.add('Q013','BLOCK',f"tasks/{t['task_id']}",'赛后任务不早于赛事结束',t['due_at'])
        if t['status']=='DONE' and not (t['proof'] and t['proof'].strip()):
            g.add('Q028','BLOCK',f"tasks/{t['task_id']}/proof",'非空完成证据',t['proof'])
    details={p['product_id']:p for p in product_details(data)}
    for p in data['products']:
        src=f"products/{p['product_id']}";face=Decimal(details[p['product_id']]['ticket_face_value'])
        if p['price_claim']=='SUM_FACE_PRICES' and p['price'] is not None and Decimal(str(p['price']))!=face:
            g.add('Q021','BLOCK',src+'/price',str(face),p['price'],'声称等于逐场票价总和，但数值不一致')
        if p['price'] is None and p['price_claim']!='SUM_FACE_PRICES':
            g.add('Q025','BLOCK',src+'/price','独立定价必须给数字',None)
        if p['price'] is not None and p['price']<0:
            g.add('Q025','BLOCK',src+'/price','价格非负',p['price'])
        for comp in p['included_sessions']:
            if comp['ticket_quantity']>sellable(seatmap[seating_key(comp)]):
                g.add('Q025','BLOCK',src+'/included_sessions','单份占票不超过对应池',comp['ticket_quantity'])
        if p['product_type']=='TRAVEL':
            t=p['travel']
            if t['room_quantity']!=t['expected_rooms'] or t['guests']<=0 or t['nights']<=0 or t['expected_rooms']<=0:
                g.add('Q022','BLOCK',src+'/travel','实际计费房数=产品声明房数；人数/房数/房晚为正',t)
            if any(c['ticket_quantity']!=t['guests'] for c in p['included_sessions']):
                g.add('Q025','BLOCK',src+'/included_sessions','每场占票数=旅行人数',p['included_sessions'])
            cost=Decimal(str(t['room_cost']))*t['room_quantity']*t['nights']+Decimal(str(t['service_per_guest']))*t['guests']+Decimal(str(t['other_cost']))
            rate=Decimal(str(t['rate']))
            if any(t[k]<0 for k in ('room_cost','service_per_guest','other_cost')) or (t['pricing_method']=='margin' and rate>=1):
                g.add('Q023','BLOCK',src+'/travel','非负成本且margin率小于1',t)
            else:
                quote=cost*(1+rate) if t['pricing_method']=='markup' else cost/(1-rate)
                if t['actual_method']!=t['pricing_method'] or abs(quote-Decimal(str(t['quoted_non_ticket'])))>Decimal('.005'):
                    g.add('Q023','BLOCK',src+'/travel',str(quote),t['quoted_non_ticket'],
                          'markup=成本×(1+率)，margin=成本÷(1-率)，不能混用',action='确认计费基数和目标方法，不仅改文字标签')
                if p['price'] is not None and abs(Decimal(str(p['price']))-face-Decimal(str(t['quoted_non_ticket'])))>Decimal('.005'):
                    g.add('Q025','BLOCK',src+'/price',str(face+Decimal(str(t['quoted_non_ticket']))),p['price'],'旅行售价须与票面部分＋旅游报价闭合')
    for seat in data['seating']:
        sid,tier=seat['session_id'],seat['tier']
        rates=[data['scenarios'][k]['session_rates'][sid]*data['scenarios'][k]['tier_rates'][tier] for k in ('low','mid','high')]
        if rates!=sorted(rates):g.add('Q026','BLOCK',f'scenarios/{sid}/{tier}','low <= mid <= high',rates)
    paid=[data['scenarios'][k]['paid_rights_rate'] for k in ('low','mid','high')]
    if paid!=sorted(paid):g.add('Q026','BLOCK','scenarios/paid_rights_rate','low <= mid <= high',paid)
    evidence=data['quality_evidence']
    for cell in evidence['cells']:
        v=cell['value']
        if isinstance(v,str) and re.search(r'#REF!|#DIV/0!|#VALUE!|#NAME\?|#N/A|#NUM!|#NULL!',v):
            g.add('Q002','BLOCK',cell['source'],'无Excel错误',v)
        if v is None or (isinstance(v,str) and not v.strip()):g.add('Q003','BLOCK',cell['source'],'所声明必填引用非空',v)
    for check in evidence['totals']:
        expected=sum(Decimal(str(v)) for v in check['components'])
        if expected!=Decimal(str(check['declared'])):g.add('Q005','BLOCK',check['source'],str(expected),check['declared'])
    for check in evidence['percentages']:
        total=sum(Decimal(str(v)) for v in check['values'])
        if total!=Decimal(str(check['expected'])):g.add('Q006','BLOCK',check['source'],check['expected'],str(total))
    units=defaultdict(set)
    for m in evidence['metrics']:units[m['metric_id']].add(m['unit'])
    for m in evidence['metrics']:
        if len(units[m['metric_id']])>1:g.add('Q007','WARNING',m['source'],'同一metric_id只有一种单位',sorted(units[m['metric_id']]),'订单／票张／份／人数不能互换')
    for doc in evidence['documents']:
        years=set(re.findall(r'(?<!\d)(20\d{2})(?=年|\b)',doc['text']))
        old=sorted(y for y in years if int(y)!=year)
        if old:g.add('Q011','BLOCK' if doc['critical'] else 'WARNING',doc['source'],year,old,'发现非本届年度；历史比较文本可标非关键但仍需审核')
        if re.search(r'最终|正式|\bFINAL\b',doc['text'],re.I) and not approved(data):
            g.add('Q017','BLOCK',doc['source'],'正式/最终标签需要批准',data['status'])
    named=defaultdict(set)
    for n in evidence['named_models']:named[n['name']].add(n['content'])
    for n in evidence['named_models']:
        if len(named[n['name']])>1:g.add('Q018','BLOCK',n['source'],'同名指向相同内容或有明确版本ID',n['name'])
    for ref in evidence['output_refs']:
        if ref['snapshot_id']!=data['snapshot_id'] or data['snapshot_id'] is None:
            g.add('Q020','BLOCK',ref['source'],data['snapshot_id'],ref['snapshot_id'])
    if evidence['summaries']:
        try:
            result=calculate(data)
            for c in evidence['summaries']:
                v=result
                try:
                    for key in c['metric'].split('.'):v=v[key]
                    expected=Decimal(str(v))
                except (KeyError,TypeError,ValueError,InvalidOperation):
                    g.add('Q003','BLOCK',c['source'],'可解析的派生指标路径',c['metric']);continue
                if expected!=Decimal(str(c['value'])):g.add('Q004','BLOCK',c['source'],str(expected),c['value'])
                elif c['mode']=='HARDCODED':g.add('Q004','WARNING',c['source'],'用派生值输出而非手抄',c['value'],'当前数值相符，但硬编码摘要会失去联动')
        except ModelError as e:g.add('Q004','BLOCK','quality_evidence/summaries','可计算模型',str(e))
    checked=set(RULES)-{'Q030','Q031'}
    for rule in sorted(checked-{f.rule_id for f in g.findings}):
        g.add(rule,'PASS','$','无适用违规','未发现适用违规',action='无；PASS仅覆盖本次结构化输入与声明的检查契约')
    return g

def validate(data,for_release=False):
    try:
        return _validate(data,for_release)
    except (ArithmeticError,OverflowError) as e:
        result=GateResult([])
        result.add('Q001','BLOCK','$','可在Decimal范围内安全计算的输入',str(e),
                   '输入导致算术失败，不能生成可靠发布结果')
        return result
