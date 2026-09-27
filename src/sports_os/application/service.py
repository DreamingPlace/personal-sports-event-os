"""Stable application boundary for CLI and a future GUI; no stdout contracts."""
from copy import deepcopy
from decimal import Decimal
from datetime import datetime
import json
from ..kernel import Project,ModuleState,Context,Registry
from ..kernel.store import Store
from ..kernel.gate import validate_project
from ..kernel.diff import compare_versions
from ..kernel.snapshot import create_snapshot,verify_snapshot,ReleaseBlocked
from ..kernel.data import KernelError,canonical,digest
from .manifest import PROFILES,parse_manifest,render_manifest,safe_path

class ApplicationService:
    def __init__(self,workspace,registry=None):
        self.root=safe_path(workspace,'.')
        self.registry=registry if registry is not None else Registry.discover()
        self.store=Store(safe_path(self.root,'data/modular.sqlite'))

    @staticmethod
    def run_legacy(argv):
        from .legacy import main
        return main(argv)

    def migrate_v10(self,data):
        from .migration import migrate_v10
        return migrate_v10(data,self.registry)

    def demo(self,profile=None):
        from ..models.demo import make_demo,make_version_b
        a=make_demo();b=make_version_b(a)
        projects=[self.migrate_v10(d) for d in (a,b)]
        if profile is not None:
            if profile not in PROFILES:raise KernelError('未知预设')
            for p in projects:
                selected=PROFILES[profile]
                p.manifest['modules']={k:True for k in selected}
                p.states={k:v for k,v in p.states.items() if k in selected}
                if 'ticketing.rights' not in selected and 'ticketing.inventory' in selected:
                    for r in p.states['ticketing.inventory'].payload['rows']:
                        r['allocation_type']='PUBLIC'
                        if r['status']=='PAID_RESERVED':r['status']='AVAILABLE'
        for name,p in zip(('version_a','version_b'),projects):
            target=safe_path(self.root,'data/modular_demo/'+name+'.json')
            if target.exists():
                from ..kernel.data import load_json
                if canonical(load_json(target))!=canonical(p.to_dict()):raise KernelError('拒绝覆盖已修改Demo')
        if self.store.path.exists() and self.store.load().to_dict()!=projects[0].to_dict():raise KernelError('工作数据已修改，拒绝覆盖')
        for name,p in zip(('version_a','version_b'),projects):
            gate=self.validate_project(p,True)
            if gate.status=='BLOCK':raise KernelError(canonical(gate.to_dict()))
            self.write_artifact('data/modular_demo/'+name+'.json',self.json_text(p.to_dict()))
        self.save_project(projects[0]);return projects[0]

    def list_modules(self):return self.registry.list()

    def create_project(self,identity,profile=None,modules=()):
        if profile is not None and profile not in PROFILES:raise KernelError('未知预设')
        selected=tuple(PROFILES[profile]) if profile else tuple(modules)
        self.registry.order(selected)
        meta=dict(identity)
        meta.setdefault('version','1');meta.setdefault('synthetic',True);meta.setdefault('status','DRAFT');meta.setdefault('approval_ref','')
        project=Project(dict(project=meta,modules={k:True for k in selected}))
        # Only modules supply payload schemas; kernel/project creation never invents business input.
        return project

    def open_project(self):
        project=self.store.load();path=safe_path(self.root,'project.toml')
        if path.exists():project.manifest=parse_manifest(path)
        if project.manifest['project']['id']!=self.store.load().manifest['project']['id']:
            raise KernelError('manifest项目ID与工作库不符')
        return project

    def save_project(self,project):
        gate=self.validate_project(project)
        if gate.status=='BLOCK':raise KernelError('BLOCK: '+canonical(gate.to_dict()))
        self.store.save(project)
        self.write_artifact('project.toml',render_manifest(project.manifest))
        return gate

    @staticmethod
    def _configuration_changed(project):
        meta=project.manifest['project']
        meta.update(status='DRAFT',approval_ref='',version=meta['version']+'-edited')
        return project

    def enable_module(self,project,module_id,payload=None):
        out=deepcopy(project);module=self.registry.get(module_id)
        out.manifest['modules'][module_id]=True
        self.registry.order(out.enabled)
        if payload is not None:
            out.states[module_id]=ModuleState(module.module_version,module.schema_version,deepcopy(payload))
        if module_id not in out.states:raise KernelError('启用模块必须显式提供payload')
        return self._configuration_changed(out)

    def disable_module(self,project,module_id):
        out=deepcopy(project);out.manifest['modules'][module_id]=False
        self.registry.order(out.enabled)
        # Retain inactive state for deliberate re-enabling; excluded from execution and snapshots.
        return self._configuration_changed(out)

    def replace_module(self,project,old_id,new_id,payload):
        out=deepcopy(project);out.manifest['modules'][old_id]=False
        return self.enable_module(out,new_id,payload)

    def migrate_module(self,project,module_id):
        out=deepcopy(project);module=self.registry.get(module_id);state=out.states[module_id]
        state.payload=module.migrate(state.module_version,state.schema_version,deepcopy(state.payload))
        state.module_version=module.module_version;state.schema_version=module.schema_version
        state.data_version=state.data_version+'-migrated';state.status='DRAFT';state.approval_ref=None
        out.manifest['project'].update(status='DRAFT',approval_ref='',version=out.manifest['project']['version']+'-migrated')
        return out

    def validate_project(self,project,for_release=False):return validate_project(project,self.registry,for_release)

    def calculate_module(self,project,module_id):
        gate=self.validate_project(project)
        if gate.status=='BLOCK':raise KernelError('BLOCK: '+canonical(gate.to_dict()))
        return Context(project,self.registry).calculate(module_id)

    def compare_versions(self,old,new):
        from ..kernel.diff import changes
        def unpack(value):
            if isinstance(value,Project):return value,None
            if 'snapshot_id' in value:
                verify_snapshot(value)
                return Project.from_dict(value['project']),{k:value[k] for k in ('snapshot_id','created_at','content_hash','record_hash')}
            return Project.from_dict(value),None
        a,ma=unpack(old);b,mb=unpack(new)
        result=compare_versions(a,b,self.registry)
        result['snapshot_metadata']=changes(ma,mb,'snapshot')
        return result
    def create_snapshot(self,project,ack_warnings=False):return create_snapshot(project,self.registry,self.store,ack_warnings)
    def list_snapshots(self,project_id):return self.store.list_snapshots(project_id)

    def export_artifact(self,record):
        verify_snapshot(record);project=Project.from_dict(record['project'])
        gate=self.validate_project(project,True)
        if gate.status=='BLOCK' or (gate.status=='WARNING' and not record['warnings_acknowledged']):raise ReleaseBlocked('导出前门禁未通过')
        context=Context(project,self.registry,True)
        artifacts={key:self.registry.get(key).export(context) for key in project.enabled}
        document=dict(snapshot_id=record['snapshot_id'],module_index=record['module_index'],artifacts=artifacts)
        files={'snapshot.json':self.json_text(record),'artifacts.json':self.json_text(document)}
        files['manifest.json']=self.json_text(dict(snapshot_id=record['snapshot_id'],files={k:digest(v) for k,v in files.items()}))
        target=safe_path(self.root,'outputs/releases/'+record['snapshot_id'])
        if target.exists():
            if {p.name for p in target.iterdir()}!=set(files) or any(safe_path(target,k).read_text()!=v for k,v in files.items()):
                raise ReleaseBlocked('发布目录不同，拒绝覆盖')
            return target
        import tempfile,os,shutil
        target.parent.mkdir(parents=True,exist_ok=True)
        from pathlib import Path
        temporary=Path(tempfile.mkdtemp(prefix='.staging-',dir=target.parent))
        try:
            for name,text in files.items():(temporary/name).write_text(text,encoding='utf-8')
            os.rename(temporary,target)
        finally:
            if temporary.exists():shutil.rmtree(temporary)
        return target

    @staticmethod
    def json_text(value):
        def decimal(v):
            if isinstance(v,Decimal):return format(v,'f')
            if isinstance(v,datetime):return v.isoformat()
            raise TypeError(type(v).__name__)
        def keys(v):
            if isinstance(v,dict):return {(canonical(list(k)) if isinstance(k,tuple) else k):keys(x) for k,x in v.items()}
            if isinstance(v,list):return [keys(x) for x in v]
            return v
        return json.dumps(keys(value),ensure_ascii=False,indent=2,sort_keys=True,default=decimal,allow_nan=False)+'\n'

    def write_artifact(self,name,content):
        path=safe_path(self.root,name);path.parent.mkdir(parents=True,exist_ok=True)
        # Atomic replacement of working artifacts; never used for frozen release paths.
        import tempfile,os
        fd,tmp=tempfile.mkstemp(prefix='.write-',dir=path.parent)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as f:f.write(content)
            os.replace(tmp,path)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
        return path
