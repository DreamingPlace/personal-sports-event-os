import json
import sqlite3
from pathlib import Path
from .data import canonical, KernelError
from .contract import Project, ModuleState

class Store:
    def __init__(self,path):self.path=Path(path)
    def connect(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        con=sqlite3.connect(self.path)
        con.execute('PRAGMA foreign_keys=ON')
        con.executescript('''
        CREATE TABLE IF NOT EXISTS projects(project_id TEXT PRIMARY KEY, manifest TEXT NOT NULL, evidence TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS module_state(project_id TEXT NOT NULL REFERENCES projects(project_id), module_id TEXT NOT NULL,
            module_version TEXT NOT NULL, schema_version TEXT NOT NULL, data_version TEXT NOT NULL,
            status TEXT NOT NULL, approval_ref TEXT, payload TEXT NOT NULL CHECK(json_valid(payload)), content_hash TEXT NOT NULL,
            PRIMARY KEY(project_id,module_id));
        CREATE TABLE IF NOT EXISTS snapshots(snapshot_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, record TEXT NOT NULL CHECK(json_valid(record)));
        CREATE TABLE IF NOT EXISTS snapshot_modules(snapshot_id TEXT NOT NULL REFERENCES snapshots(snapshot_id),module_id TEXT NOT NULL,
            module_version TEXT NOT NULL,schema_version TEXT NOT NULL,content_hash TEXT NOT NULL,PRIMARY KEY(snapshot_id,module_id));
        CREATE TRIGGER IF NOT EXISTS frozen_snapshot_update BEFORE UPDATE ON snapshots BEGIN SELECT RAISE(ABORT,'immutable snapshot'); END;
        CREATE TRIGGER IF NOT EXISTS frozen_snapshot_delete BEFORE DELETE ON snapshots BEGIN SELECT RAISE(ABORT,'immutable snapshot'); END;
        CREATE TRIGGER IF NOT EXISTS frozen_module_update BEFORE UPDATE ON snapshot_modules BEGIN SELECT RAISE(ABORT,'immutable snapshot module'); END;
        CREATE TRIGGER IF NOT EXISTS frozen_module_delete BEFORE DELETE ON snapshot_modules BEGIN SELECT RAISE(ABORT,'immutable snapshot module'); END;
        ''')
        return con

    def save(self,project):
        pid=project.manifest['project']['id']
        with self.connect() as con:
            con.execute('INSERT INTO projects VALUES(?,?,?) ON CONFLICT(project_id) DO UPDATE SET manifest=excluded.manifest,evidence=excluded.evidence',
                        (pid,canonical(project.manifest),canonical(project.evidence)))
            con.execute('DELETE FROM module_state WHERE project_id=?',(pid,))
            for key,state in sorted(project.states.items()):
                con.execute('INSERT INTO module_state VALUES(?,?,?,?,?,?,?,?,?)',
                    (pid,key,state.module_version,state.schema_version,state.data_version,state.status,state.approval_ref,canonical(state.payload),state.content_hash))

    def load(self,project_id=None):
        if not self.path.exists():raise KernelError('模块工作库不存在，请 create、demo 或 migrate-v10')
        with self.connect() as con:
            rows=con.execute('SELECT project_id,manifest,evidence FROM projects ORDER BY project_id').fetchall()
            if project_id is not None:rows=[r for r in rows if r[0]==project_id]
            if len(rows)!=1:raise KernelError('必须明确选择唯一项目')
            pid,manifest,evidence=rows[0];states={}
            for row in con.execute('SELECT module_id,module_version,schema_version,data_version,status,approval_ref,payload,content_hash FROM module_state WHERE project_id=?',(pid,)):
                key,mv,sv,dv,status,ref,payload,hashed=row
                state=ModuleState(mv,sv,json.loads(payload),dv,status,ref)
                if state.content_hash!=hashed:raise KernelError('工作模块hash不符：'+key)
                states[key]=state
        return Project(json.loads(manifest),states,json.loads(evidence))

    def list_snapshots(self,project_id):
        if not self.path.exists():return []
        with self.connect() as con:
            records=[json.loads(r[0]) for r in con.execute('SELECT record FROM snapshots WHERE project_id=? ORDER BY snapshot_id',(project_id,))]
            from .snapshot import verify_snapshot
            for r in records:
                verify_snapshot(r)
                actual=con.execute('SELECT module_id,module_version,schema_version,content_hash FROM snapshot_modules WHERE snapshot_id=? ORDER BY module_id',(r['snapshot_id'],)).fetchall()
                expected=[(k,v['module_version'],v['schema_version'],v['content_hash']) for k,v in sorted(r['module_index'].items())]
                if actual!=expected:raise KernelError('冻结模块索引不一致')
            return records
