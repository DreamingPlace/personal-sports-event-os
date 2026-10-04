"""Bounded JSON Lines protocol; IDs are never replayed within a process."""
import json
from ..kernel.data import KernelError

MAX_LINE=8*1024*1024

class ProtocolError(KernelError):
    def __init__(self,code,message,details=None):
        super().__init__(message);self.code=code;self.details=details or {}


def decode(line):
    def pairs(items):
        out={}
        for k,v in items:
            if k in out:raise ProtocolError('PROTOCOL','请求含重复JSON键')
            out[k]=v
        return out
    try:
        if len(line.encode())>MAX_LINE:raise ValueError('请求超过8MiB')
        value=json.loads(line,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('非有限数字')))
        if not isinstance(value,dict) or set(value)!={'id','method','params'}:raise ValueError('需要id/method/params')
        if not isinstance(value['id'],str) or not 1<=len(value['id'])<=128:raise ValueError('id必须为非空短字符串')
        if not isinstance(value['method'],str) or not isinstance(value['params'],dict):raise ValueError('method/params类型错误')
        return value
    except (ValueError,TypeError) as exc:raise ProtocolError('PROTOCOL',str(exc)) from exc
