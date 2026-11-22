"""Exercise a real worker against the isolated training API, never production."""
import argparse,json,subprocess,time,urllib.request
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scope',choices=['CORE','VN30'],default='CORE')
    parser.add_argument('--report-prefix',default='worker-integration')
    args=parser.parse_args()
    root=Path('reports/prediction-core-completion-2026-11-22')
    sandbox=json.loads((root/'training-sandbox.json').read_text())
    name=sandbox['container'];base=sandbox['url']
    assert name.startswith('vn-stock-core-training-audit-') and base=='http://localhost:8003'
    def get(path):
        with urllib.request.urlopen(base+path,timeout=60) as response:return json.load(response)
    before=[get('/api/predict/signal?symbol=VIC&model_type='+kind) for kind in ['lightgbm','lstm']]
    generations={p['model_type']:p['training_info']['artifact_generation'] for p in before}
    command=['docker','run','--rm','--network','container:'+name,
        '--env','INTERNAL_WORKER_SECRET=core-audit-isolated-worker-only-2026',
        '--mount',f'type=bind,src={Path("infra/scripts/retrain_worker.py").resolve()},dst=/worker.py,readonly',
        'python:3.11-alpine','python','/worker.py','--once','--scope',args.scope,'--api-url','http://127.0.0.1:8000']
    start=time.monotonic()
    with (root/f'{args.report_prefix}.log').open('w') as log:
        worker=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        while worker.poll() is None:
            if time.monotonic()-start>900:
                raise TimeoutError('Worker still running; inspect its handle/container before restarting')
            time.sleep(2)
    assert worker.returncode==0,(root/f'{args.report_prefix}.log').read_text()
    after=[get('/api/predict/signal?symbol='+symbol+'&model_type='+kind)
           for symbol in ['VIC','HPG'] for kind in ['lightgbm','lstm']]
    for prediction in after:
        info=prediction['training_info']
        assert info['artifact_generation']!=generations[prediction['model_type']]
        assert info['serving_status']=='healthy'
        assert info['scope']==args.scope and info['symbols_count']==(5 if args.scope=='CORE' else 30)
        assert info['runtime_versions']['scikit-learn']=='1.7.2'
        assert len(prediction['trajectory'])==3
        assert abs(sum(prediction['probabilities'].values())-1)<.001
    assert len({p['training_info']['artifact_generation'] for p in after})==1
    subprocess.run(['docker','cp',name+':/tmp/core-ssi-calls.jsonl',str(root/f'{args.report_prefix}-ssi-trace.jsonl')],check=True,capture_output=True)
    calls=[json.loads(line) for line in (root/f'{args.report_prefix}-ssi-trace.jsonl').read_text().splitlines()]
    assert any(c['status']=='success' and c['kind']=='stock' for c in calls)
    report={'sandbox':sandbox,'worker_exit_code':worker.returncode,'seconds':round(time.monotonic()-start,3),
        'before':before,'after':after,'real_ssi_calls':calls,
        'scope':args.scope,'limitations':['This verifies pipeline operation, not independent model quality.','No production artifact or data directory is mounted.']}
    (root/f'{args.report_prefix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({'worker_exit':worker.returncode,'seconds':report['seconds'],
        'old_generations':generations,'new_generation':after[0]['training_info']['artifact_generation'],
        'real_ssi_calls':len(calls),'scope':args.scope,'symbols_count':after[0]['training_info']['symbols_count']}))


if __name__=='__main__':main()
