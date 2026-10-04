"""Exercise the bundled binary with an empty PATH; Python here is only the test runner."""
import json,os,select,subprocess,sys,tempfile
from pathlib import Path
binary=Path(sys.argv[1]).resolve()
checks=[]
with tempfile.TemporaryDirectory(prefix='sports-packaged-') as workspace:
    def start():
        return subprocess.Popen([str(binary)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,
                                env={'PATH':'/nonexistent','HOME':os.environ['HOME'],'LANG':'en_US.UTF-8','TMPDIR':tempfile.gettempdir()})
    process=start();counter=0
    def call(method,**params):
        global counter
        counter+=1;rid=str(counter)
        process.stdin.write(json.dumps(dict(id=rid,method=method,params=params))+'\n');process.stdin.flush()
        if not select.select([process.stdout],[],[],30)[0]:raise TimeoutError(method)
        response=json.loads(process.stdout.readline());assert response['id']==rid,response
        return response
    def ok(method,**params):
        response=call(method,**params);assert response['ok'],response
        return response['result']
    try:
        assert len(ok('health')['modules'])==19;checks.append('empty PATH / Registry 19')
        state=ok('create_demo',workspace=workspace);checks.append('create Demo')
        first=ok('create_snapshot')['snapshot'];sid=first['snapshot_id']
        old=ok('calculate_module',module_id='finance.revenue',snapshot_id=sid)
        data=ok('get_module_data',module_id='ticketing.pricing');data['rows'][0]['price']=731
        state=ok('update_module_data',module_id='ticketing.pricing',payload=data)
        assert state['project']['manifest']['project']['status']=='DRAFT';checks.append('edit / APPROVED -> DRAFT')
        assert not call('create_snapshot')['ok'];checks.append('BLOCK forbids snapshot')
        assert ok('validate_project')['status']=='PASS';checks.append('preview Quality Gate')
        current=ok('calculate_module',module_id='finance.revenue')
        assert current!=old
        assert ok('calculate_module',module_id='finance.revenue',snapshot_id=sid)==old;checks.append('working vs frozen Revenue')
        state=ok('approve_module',module_id='ticketing.pricing',approval_ref='SYNTHETIC-BUNDLE',data_version=state['project']['modules']['ticketing.pricing']['data_version'])
        ok('approve_project',approval_ref='SYNTHETIC-BUNDLE',version=state['project']['manifest']['project']['version']);checks.append('manual module/project approval')
        second=ok('create_snapshot')['snapshot'];assert sid!=second['snapshot_id'];checks.append('second snapshot')
        assert ok('get_snapshot',snapshot_id=sid)==first;checks.append('original snapshot unchanged')
        assert ok('compare_versions',old=sid,new='WORKING')['business']
        assert ok('compare_versions',old=sid,new=second['snapshot_id'])['business'];checks.append('both diff modes')
        process.stdin.close();process.wait(timeout=10);process=start()
        state=ok('open_project',workspace=workspace);assert state['project']['manifest']['project']['status']=='APPROVED'
        assert len(ok('list_snapshots'))==2;assert ok('get_snapshot',snapshot_id=sid)==first;checks.append('process restart/open retains approval and both snapshots')
    finally:
        if process.poll() is None:process.stdin.close();process.wait(timeout=10)
print(json.dumps(dict(status='PASS',binary=str(binary),runtime_path='/nonexistent',registry_count=19,checks=checks),indent=2))
