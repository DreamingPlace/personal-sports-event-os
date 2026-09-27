"""Thin CLI over ApplicationService. No direct business-engine imports."""
import argparse
import json
import sys
import sqlite3
from .application import ApplicationService
from .application.manifest import safe_path,PROFILES,render_manifest
from .kernel.data import load_json


def parser():
    p=argparse.ArgumentParser(description='Sports Event OS Modular Kernel v1.1.1 — synthetic/offline')
    sub=p.add_subparsers(dest='command',required=True)
    for name in ['demo','create','validate','revenue','calculate','diff','snapshot','load','export-data','modules','enable','disable','replace','snapshots','migrate-v10','migrate-module','update','patch','approve-module','approve-project','migrate-project']:
        q=sub.add_parser(name);q.add_argument('--workspace',default='.')
        if name in ('demo','create'):q.add_argument('--profile',choices=sorted(PROFILES))
        if name=='create':
            q.add_argument('--id',required=True);q.add_argument('--name',required=True);q.add_argument('--timezone',default='UTC')
        if name in ('validate','revenue','calculate','snapshot'):q.add_argument('--data')
        if name=='validate':q.add_argument('--for-release',action='store_true')
        if name=='snapshot':q.add_argument('--ack-warnings',action='store_true')
        if name=='diff':q.add_argument('version_a');q.add_argument('version_b')
        if name in ('load','migrate-v10'):q.add_argument('input')
        if name in ('enable','disable','calculate','migrate-module','update','patch','approve-module'):q.add_argument('module_id')
        if name=='enable':q.add_argument('--payload')
        if name in ('update','patch'):q.add_argument('input')
        if name in ('approve-module','approve-project'):
            q.add_argument('--approval-ref',required=True);q.add_argument('--version',required=True)
        if name=='replace':
            q.add_argument('old_id');q.add_argument('new_id');q.add_argument('--payload',required=True)
    return p


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if '--legacy' in argv:
        argv.remove('--legacy');return ApplicationService.run_legacy(argv)
    args=parser().parse_args(argv)
    try:
        app=ApplicationService(args.workspace)
        read=lambda p:load_json(safe_path(app.root,p))
        emit=lambda name,value:app.write_artifact('outputs/'+name,app.json_text(value))
        if args.command=='modules':print(app.json_text(app.list_modules()));return 0
        if args.command=='demo':
            project=app.demo(args.profile);print('PASS — 完全虚构模块项目：'+project.manifest['project']['name']);return 0
        if args.command=='create':
            project=app.create_project(dict(id=args.id,name=args.name,timezone=args.timezone),args.profile)
            # Profile recommendations are editable. Empty module data are not invented.
            if project.enabled:
                path=emit('project-skeleton.json',project.to_dict())
                app.write_artifact('project.toml',render_manifest(project.manifest))
                print('DRAFT — 预设已写入；请按各模块schema补充payload后load：'+str(path));return 0
            app.save_project(project);print('PASS — 已创建无业务模块Kernel项目（DRAFT）');return 0
        if args.command in ('load','migrate-v10'):
            raw=read(args.input);project=app.migrate_v10(raw) if args.command=='migrate-v10' else app.import_project(raw)
            gate=app.save_project(project);print(gate.status);return 0
        if args.command=='diff':
            def version(name):
                path=safe_path(app.root,'data/modular_demo/'+name+'.json' if name in ('version_a','version_b') else name)
                return load_json(path)
            result=app.compare_versions(version(args.version_a),version(args.version_b));emit('V1_1_DIFF.json',result)
            print(app.json_text(result));return 0
        project=app.import_project(read(args.data)) if getattr(args,'data',None) else app.open_project()
        if args.command=='export-data':print(emit('working-project.json',project.to_dict()));return 0
        if args.command=='snapshots':print(app.json_text(app.list_snapshots(project.manifest['project']['id'])));return 0
        if args.command in ('enable','disable','replace','migrate-module'):
            if args.command=='enable':project=app.enable_module(project,args.module_id,read(args.payload) if args.payload else None)
            elif args.command=='disable':project=app.disable_module(project,args.module_id)
            elif args.command=='replace':project=app.replace_module(project,args.old_id,args.new_id,read(args.payload))
            else:project=app.migrate_module(project,args.module_id)
            app.save_project(project);print('PASS — 工作态配置已更新；历史snapshot未变；需重新批准');return 0
        if args.command=='migrate-project':
            project=app.migrate_project(project);app.save_project(project)
            print('PASS — 显式迁移完成；变化模块及项目需要人工重新批准');return 0
        if args.command in ('update','patch','approve-module','approve-project'):
            if args.command=='update':project=app.update_module_data(project,args.module_id,read(args.input))
            elif args.command=='patch':project=app.apply_changeset(project,args.module_id,read(args.input))
            elif args.command=='approve-module':project=app.approve_module(project,args.module_id,args.approval_ref,args.version)
            else:project=app.approve_project(project,args.approval_ref,args.version)
            app.save_project(project)
            print(app.json_text(dict(project=project.manifest['project'],modules={k:dict(data_version=s.data_version,status=s.status) for k,s in project.states.items()})))
            return 0
        gate=app.validate_project(project,args.command=='snapshot' or getattr(args,'for_release',False))
        emit('V1_1_QUALITY_GATE.json',gate.to_dict())
        if args.command=='validate':print(app.json_text(gate.to_dict()));return 2 if gate.status=='BLOCK' else 0
        if gate.status=='BLOCK':print(app.json_text(gate.to_dict()));return 2
        if args.command in ('revenue','calculate'):
            key='finance.revenue' if args.command=='revenue' else args.module_id
            result=app.calculate_module(project,key);emit('V1_1_'+key+'.json',result);print(app.json_text(result));return 0
        if args.command=='snapshot':
            record=app.create_snapshot(project,args.ack_warnings);path=app.export_artifact(record)
            print('PASS — '+record['snapshot_id']+'\n'+str(path));return 0
    except (ValueError,KeyError,TypeError,OSError,sqlite3.DatabaseError) as e:
        print('ERROR / BLOCK — '+str(e));return 2
    return 0
