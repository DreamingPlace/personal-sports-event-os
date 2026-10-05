"""Stable application boundary for CLI and a future GUI; no stdout contracts."""
from copy import deepcopy
from decimal import Decimal
from datetime import datetime
import json
import re
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
        if self.store.has_draft():raise KernelError('工作区有未完成草稿，拒绝覆盖')
        if not self.store.is_empty():
            current=self.store.load()
            if current.to_dict()!=projects[0].to_dict():raise KernelError('工作数据已修改，拒绝覆盖')
            projects[0].base_revision=current.base_revision
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

    LEGACY_DRAFT='data/desktop-draft.json'

    def _adopt_legacy_draft(self):
        """v1.1.1 desktop kept drafts in a separate JSON file; move it into the store once."""
        from ..kernel.data import load_json
        path=safe_path(self.root,self.LEGACY_DRAFT)
        if not path.exists():return
        body=load_json(path)
        if digest(body['project'])!=body['content_hash']:raise KernelError('草稿hash不符')
        project=Project.from_dict(body['project'])
        if project.manifest['project']['status']!='DRAFT':raise KernelError('草稿不能声称已批准')
        if self.store.has_draft():raise KernelError('同时存在旧草稿文件和工作库草稿；请备份后删除其中一个：'+str(path))
        self.store.save_draft(project);path.unlink()

    def open_project(self):
        """Open the single working copy: an incomplete draft if one exists, otherwise the saved project."""
        self._adopt_legacy_draft()
        project=self.store.load_working()
        if self.store.has_draft():return project
        path=safe_path(self.root,'project.toml')
        if path.exists():
            manifest=parse_manifest(path)
            if manifest['project']['id']!=project.manifest['project']['id']:
                raise KernelError('manifest项目ID与工作库不符')
            if canonical(manifest)!=canonical(project.manifest):
                # External TOML edits are working changes, not a route to record approval.
                version=project.manifest['project']['version']
                project.manifest=manifest;project.manifest['project']['version']=version
                self._configuration_changed(project)
        return project

    def save_project(self,project):
        gate=self.validate_project(project)
        if gate.status=='BLOCK':raise KernelError('BLOCK: '+canonical(gate.to_dict()))
        self.store.save(project)
        self.write_artifact('project.toml',render_manifest(project.manifest))
        return gate

    @staticmethod
    def _next_revision(version):
        match=re.fullmatch(r"(.*)-r([0-9]+)",version)
        return f"{match[1]}-r{int(match[2])+1}" if match else version+"-r1"

    @classmethod
    def _configuration_changed(cls,project):
        meta=project.manifest['project']
        meta.update(status='DRAFT',approval_ref='',version=cls._next_revision(meta['version']))
        return project

    def enable_module(self,project,module_id,payload=None):
        module=self.registry.get(module_id);out=deepcopy(project)
        was_enabled=module_id in out.enabled
        out.manifest['modules'][module_id]=True
        self.registry.order(out.enabled)
        if module_id in out.states:
            if payload is not None:out=self.update_module_data(out,module_id,payload)
        elif payload is not None:
            out.states[module_id]=ModuleState(module.module_version,module.schema_version,
                                              module.prepare_revision(deepcopy(payload),'1'))
        if module_id not in out.states:raise KernelError('启用模块必须显式提供payload')
        if was_enabled or out.manifest['project']['version']!=project.manifest['project']['version']:return out
        return self._configuration_changed(out)

    def disable_module(self,project,module_id):
        if module_id not in project.enabled:return deepcopy(project)
        out=deepcopy(project);out.manifest['modules'][module_id]=False
        self.registry.order(out.enabled)
        # Retain inactive state for deliberate re-enabling; excluded from execution and snapshots.
        return self._configuration_changed(out)

    def replace_module(self,project,old_id,new_id,payload):
        out=deepcopy(project);out.manifest['modules'][old_id]=False
        out=self.enable_module(out,new_id,payload)
        if out.manifest['modules']!=project.manifest['modules'] and out.manifest['project']['version']==project.manifest['project']['version']:
            self._configuration_changed(out)
        return out

    def import_project(self,data):
        """Import untrusted working JSON as DRAFT, never as an approval transfer."""
        out=Project.from_dict(data)
        for key,state in out.states.items():
            state.data_version=self._next_revision(state.data_version)
            state.status='DRAFT';state.approval_ref=None
            if key in out.enabled:
                module=self.registry.get(key)
                if (state.module_version,state.schema_version)!=(module.module_version,module.schema_version):
                    raise KernelError('导入前须显式迁移模块：'+key)
                state.payload=module.prepare_revision(state.payload,state.data_version)
        return self._configuration_changed(out)

    def get_module_schema(self,module_id):
        return deepcopy(self.registry.get(module_id).schema())

    @staticmethod
    def empty_payload(schema):
        """Editor scaffolding, not business defaults; incomplete facts remain BLOCK."""
        if 'const' in schema:return deepcopy(schema['const'])
        if 'enum' in schema:return deepcopy(schema['enum'][0])
        kind=schema.get('type','object')
        if isinstance(kind,list):
            if 'null' in kind:return None
            kind=kind[0]
        if kind=='object':return {k:ApplicationService.empty_payload(v) for k,v in schema.get('properties',{}).items() if k in schema.get('required',[])}
        if kind=='array':return []
        if kind=='boolean':return False
        if kind in ('number','integer'):return schema.get('minimum',0)
        return ''

    def create_workspace(self,identity,modules):
        if not self.store.is_empty() or safe_path(self.root,'project.toml').exists() or safe_path(self.root,self.LEGACY_DRAFT).exists():
            raise KernelError('目录已有项目，拒绝覆盖；请选择空项目目录')
        project=self.create_project(identity,modules=modules)
        for key in self.registry.order(project.enabled):
            project=self.enable_module(project,key,self.empty_payload(self.get_module_schema(key)))
        self.save_desktop_draft(project)
        return project

    def save_desktop_draft(self,project):
        """Persist an incomplete DRAFT in the working store; never weakens save/release gates."""
        from ..kernel.data import _shape
        from ..kernel.gate import MANIFEST
        _shape(project.manifest,MANIFEST,'manifest')
        self.store.save_draft(project)

    def open_desktop_project(self):
        """Kept for protocol compatibility; the desktop and CLI open the same working copy."""
        return self.open_project()

    def has_draft(self):return self.store.has_draft()

    def discard_draft(self):
        """Drop incomplete edits and return to the last saved project."""
        self.store.discard_draft()
        return self.open_project()

    def persist_desktop_project(self,project):
        gate=self.validate_project(project)
        if gate.status=='BLOCK':
            self.save_desktop_draft(project)
            return dict(storage='DRAFT',quality=gate.to_dict())
        self.save_project(project)
        return dict(storage='SAVED',quality=gate.to_dict())

    def calculate_snapshot_module(self,project,snapshot_id,module_id):
        record=self.get_snapshot(project,snapshot_id)
        verify_snapshot(record)
        return self.calculate_module(Project.from_dict(record['project']),module_id)

    def get_snapshot(self,project,snapshot_id):
        for record in self.list_snapshots(project.manifest['project']['id']):
            if record['snapshot_id']==snapshot_id:return record
        raise KernelError('快照不存在')

    def get_module_data(self,project,module_id):
        return deepcopy(project.states[module_id].payload)

    def update_module_data(self,project,module_id,payload):
        module=self.registry.get(module_id);state=project.states[module_id]
        if (state.module_version,state.schema_version)!=(module.module_version,module.schema_version):
            raise KernelError('请先显式迁移模块')
        if canonical(state.payload)==canonical(payload):return deepcopy(project)
        out=deepcopy(project);state=out.states[module_id]
        state.data_version=self._next_revision(state.data_version)
        state.payload=module.prepare_revision(deepcopy(payload),state.data_version)
        canonical(state.payload)
        state.status='DRAFT';state.approval_ref=None
        return self._configuration_changed(out)

    def apply_changeset(self,project,module_id,changes):
        """Atomic replace of existing typed paths, e.g. ['rows', 0, 'price']."""
        payload=self.get_module_data(project,module_id)
        if not isinstance(changes,list):raise KernelError('changeset必须为数组')
        for change in changes:
            if not isinstance(change,dict):raise KernelError('每个patch必须为对象')
            if set(change)!={'path','value'} or not isinstance(change['path'],list) or not change['path']:
                raise KernelError('patch需要非空结构化path和value')
            parent=payload
            for key in change['path']:
                if isinstance(parent,list):
                    if type(key) is not int or not 0<=key<len(parent):raise KernelError('数组path越界')
                elif isinstance(parent,dict):
                    if not isinstance(key,str) or key not in parent:raise KernelError('对象path不存在')
                else:raise KernelError('path穿过标量')
                value=parent[key]
                parent=value
            parent=payload
            for key in change['path'][:-1]:parent=parent[key]
            parent[change['path'][-1]]=deepcopy(change['value'])
        return self.update_module_data(project,module_id,payload)

    @staticmethod
    def _approval_ref(ref):
        if not isinstance(ref,str) or not ref.strip():raise KernelError('必须提供明确的人工批准引用')

    def approve_module(self,project,module_id,approval_ref,data_version):
        self._approval_ref(approval_ref)
        if module_id not in project.enabled:raise KernelError('只能批准启用模块')
        state=project.states[module_id]
        if state.data_version!=data_version:raise KernelError('批准版本已过期')
        if state.status in ('APPROVED','PUBLISHED'):
            if state.approval_ref==approval_ref:return deepcopy(project)
            raise KernelError('已批准版本不可改写批准引用；先修改工作数据')
        out=deepcopy(project);state=out.states[module_id]
        state.payload=self.registry.get(module_id).prepare_revision(state.payload,data_version,approval_ref)
        state.status='APPROVED';state.approval_ref=approval_ref
        gate=self.validate_project(out)
        if gate.status=='BLOCK':raise KernelError('BLOCK: '+canonical(gate.to_dict()))
        return out

    def approve_project(self,project,approval_ref,version):
        self._approval_ref(approval_ref)
        meta=project.manifest['project']
        if meta['version']!=version:raise KernelError('批准项目版本已过期')
        if meta['status'] in ('APPROVED','PUBLISHED') and meta['approval_ref']!=approval_ref:
            raise KernelError('已批准项目不可改写批准引用')
        out=deepcopy(project);out.manifest['project'].update(status='APPROVED',approval_ref=approval_ref)
        gate=self.validate_project(out,True)
        if gate.status=='BLOCK':raise KernelError('BLOCK: '+canonical(gate.to_dict()))
        return out

    def migrate_project(self,project):
        """Explicit all-installed-module migration; persist only after every migration succeeds."""
        out=deepcopy(project)
        for key in sorted(out.states):
            state=out.states[key]
            if key not in out.enabled:continue
            module=self.registry.get(key)
            if (state.module_version,state.schema_version)!=(module.module_version,module.schema_version):
                out=self.migrate_module(out,key)
        gate=self.validate_project(out)
        if gate.status=='BLOCK':raise KernelError('BLOCK: '+canonical(gate.to_dict()))
        return out

    def migrate_module(self,project,module_id):
        out=deepcopy(project);module=self.registry.get(module_id);state=out.states[module_id]
        state.payload=module.migrate(state.module_version,state.schema_version,deepcopy(state.payload))
        state.module_version=module.module_version;state.schema_version=module.schema_version
        state.data_version=self._next_revision(state.data_version)
        state.payload=module.prepare_revision(state.payload,state.data_version)
        state.status='DRAFT';state.approval_ref=None
        return self._configuration_changed(out)

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
        import tempfile
        import os
        import shutil
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
        import tempfile
        import os
        fd,tmp=tempfile.mkstemp(prefix='.write-',dir=path.parent)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as f:f.write(content)
            os.replace(tmp,path)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
        return path
