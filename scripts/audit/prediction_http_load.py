"""Bounded HTTP benchmark for the isolated API on port 8001, not production."""
import argparse,json,time,threading,urllib.request,urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import statistics
import numpy as np
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pid',type=int,help='PID of the isolated API process; samples CPU/RSS with psutil')
parser.add_argument('--output',type=Path,default=Path('reports/prediction-audit-2026-11-20/http-load.json'))
args=parser.parse_args()
process=None
if args.pid:
    import psutil
    process=psutil.Process(args.pid)
    if 'isolated_e2e_server.py' not in ' '.join(process.cmdline()):
        raise ValueError('Resource measurement must target the isolated API harness')

def cpu_seconds():
    times=process.cpu_times()
    return times.user+times.system

base='http://localhost:8001'
for attempt in range(20):
    try:
        urllib.request.urlopen(base+'/health',timeout=1).close()
        break
    except (OSError,urllib.error.URLError):
        time.sleep(.5)
else:
    raise RuntimeError('Isolated API unavailable')
results={}
for model in ['lightgbm','lstm']:
    def run(_):
        start=time.perf_counter()
        try:
            with urllib.request.urlopen(base+f'/api/predict/signal?symbol=VIC&model_type={model}',timeout=30) as response:
                data=json.load(response)
            assert data['symbol']=='VIC' and data['model_type'].lower()==model
            assert abs(sum(data['probabilities'].values())-1)<.001
            return {'ok':True,'seconds':time.perf_counter()-start}
        except Exception as error:
            return {'ok':False,'seconds':time.perf_counter()-start,'error':type(error).__name__}
    first=run(0)
    levels=[]
    for concurrency in [1,5,10]:
        rss=[]
        stop=threading.Event()
        def sample():
            while not stop.is_set():
                rss.append(process.memory_info().rss)
                stop.wait(.05)
        if process:
            before_cpu=cpu_seconds()
            sampler=threading.Thread(target=sample,daemon=True);sampler.start()
        level_start=time.perf_counter()
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            rows=list(executor.map(run,range(concurrency*2)))
        wall=time.perf_counter()-level_start
        level={'concurrency':concurrency,'requests':len(rows),'errors':sum(not r['ok'] for r in rows),'p50_seconds':statistics.median(r['seconds'] for r in rows),'p95_seconds':float(np.quantile([r['seconds'] for r in rows],.95))}
        if process:
            stop.set();sampler.join()
            level.update(cpu_seconds=round(cpu_seconds()-before_cpu,4),wall_seconds=wall,
                         peak_sampled_rss_mib=max(rss)/1024**2,resource_samples=len(rss))
            level['average_cpu_cores']=level['cpu_seconds']/wall
        levels.append(level)
        if any(not row['ok'] for row in rows):break
    results[model]={'first_request':first,'levels':levels}
args.output.write_text(json.dumps({'results':results,'environment':'Isolated uvicorn/SQLite on 8001, same production artifacts, auto-sync disabled','limitations':['LSTM first request follows LightGBM first request; imports and OS file cache partly warm.','Bounded request counts; no SLA or sustained-load claim.','RSS sampled every 50ms; CPU is process user+system time delta, divided by wall time for average cores; no GPU measurement.']},indent=2))
print(json.dumps(results,indent=2))
