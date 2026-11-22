"""Prepare/start the disposable training API; never mount production paths."""
import argparse,json,os,shutil,subprocess,tempfile
from pathlib import Path
from dotenv import dotenv_values


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name',default='vn-stock-core-training-audit-20261122')
    parser.add_argument('--port',type=int,default=8002)
    args=parser.parse_args()
    assert args.name.startswith('vn-stock-core-training-audit-')
    root=Path.cwd();output=root/'reports/prediction-core-completion-2026-11-22'
    env=os.environ.copy()
    for candidate in [root/'.env',root/'apps/ml/.env']:
        if candidate.exists():
            for key,value in dotenv_values(candidate).items():
                if key.startswith('SSI_') and value and not env.get(key):env[key]=value
    for key in ['SSI_CONSUMER_ID','SSI_CONSUMER_SECRET']:assert env.get(key),key+' missing'
    name=args.name
    old=subprocess.run(['docker','inspect',name],capture_output=True,text=True)
    if old.returncode==0:
        state=json.loads(old.stdout)[0]
        assert state['State']['Status']=='created' and not state['Mounts']
        subprocess.run(['docker','rm',name],check=True,capture_output=True)
    command=['docker','create','--name',name,'--user','0:0','--publish',f'127.0.0.1:{args.port}:8000',
        '--env','CORE_TRAINING_SANDBOX=1','--env','DATABASE_URL=sqlite+aiosqlite:////tmp/core-audit.db',
        '--env','ENVIRONMENT=development','--env','AUTO_SYNC_ON_STARTUP=false',
        '--env','JWT_SECRET_KEY=core-audit-isolated-only-jwt-signing-key-2026',
        '--env','INTERNAL_WORKER_SECRET=core-audit-isolated-worker-only-2026',
        '--env','CORS_ORIGINS=["http://localhost:3002","http://127.0.0.1:3002"]',
        '--env','FRONTEND_PUBLIC_URL=http://localhost:3002',
        '--env','SSI_CONSUMER_ID','--env','SSI_CONSUMER_SECRET','--env','SSI_API_URL',
        '--entrypoint','python','infra-vn_stock_api:core-runtime-172','/tmp/bootstrap.py']
    subprocess.run(command,env=env,check=True,capture_output=True)
    state=json.loads(subprocess.check_output(['docker','inspect',name]))[0]
    assert not state['Mounts']
    with tempfile.TemporaryDirectory(prefix='stock-core-copy-') as workspace:
        workspace=Path(workspace)
        shutil.copytree(root/'apps/ml/data',workspace/'data')
        shutil.copytree(output/'serving-artifact-copy',workspace/'models')
        subprocess.run(['docker','cp',str(workspace),name+':/tmp/core-copy'],check=True,capture_output=True)
    subprocess.run(['docker','cp','scripts/audit/prediction_training_sandbox.py',name+':/tmp/bootstrap.py'],check=True,capture_output=True)
    subprocess.run(['docker','start',name],check=True,capture_output=True)
    (output/'training-sandbox.json').write_text(json.dumps({'container':name,'image':state['Image'],
        'mounts':state['Mounts'],'url':f'http://localhost:{args.port}',
        'credentials':'Isolated fake account seeded by bootstrap; SSI values passed only as runtime environment.',
        'initial_source':'Copies of current raw data and frozen serving artifacts; two observations trimmed in private copies to force SSI refresh.'},indent=2))
    print(f'Started isolated training API at localhost:{args.port}; no production mounts.')


if __name__=='__main__':main()
