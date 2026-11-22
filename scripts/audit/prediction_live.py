"""Read-only smoke audit against the running API; no live sync or retraining."""
import json,time,urllib.request,urllib.error
from pathlib import Path
out=Path('reports/prediction-audit-2026-11-20')
base='http://localhost:8000'
def get(path,body=None):
 start=time.perf_counter()
 try:
  req=urllib.request.Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
  with urllib.request.urlopen(req,timeout=60) as r:return r.status,json.load(r),time.perf_counter()-start
 except urllib.error.HTTPError as e:return e.code,json.load(e),time.perf_counter()-start
symbols=get('/api/stocks/symbols')[1]
rows=[]
for symbol in [s['symbol'] for s in symbols if s.get('is_core') or s.get('is_vn30')]:
 h=get(f'/api/stocks/history?symbol={symbol}&limit=1')[1]
 for model in ['lightgbm','lstm']:
  status,p,elapsed=get(f'/api/predict/signal?symbol={symbol}&model_type={model}')
  errors=[]
  if status==200:
   if p['data_as_of_date']!=h['bars'][-1]['date']:errors.append('date mismatch')
   if abs(p['current_price']-h['bars'][-1]['close'])>.011:errors.append('price mismatch')
   if abs(sum(p['probabilities'].values())-1)>.001:errors.append('probabilities')
   if len(p['trajectory'])!=3:errors.append('trajectory')
  rows.append({'symbol':symbol,'model':model,'status':status,'seconds':elapsed,'errors':errors,'date':p.get('data_as_of_date')})
checks=[]
for path,body in [('/api/predict/signal?symbol=../bad',None),('/api/predict/signal?symbol=VIC&model_type=bad',None),('/api/v1/predict/status',None),('/api/predict/retrain',{}),('/api/stocks/sync',{})]:
 code,data,elapsed=get(path,body);checks.append({'path':path,'status':code,'seconds':elapsed})
for model in ['lightgbm','lstm']:
 single=get(f'/api/predict/signal?symbol=VIC&model_type={model}')[1]
 code,post,_=get('/api/predict/signal',{'symbol':'VIC','model_type':model})
 batch=get(f'/api/predict/batch?model_type={model}')[1]
 matching=next((p for p in batch.get('predictions',[]) if p['symbol']=='VIC'),{})
 checks.append({'model':model,'get_post_equal':single.get('probabilities')==post.get('probabilities'),'single_batch_equal':single.get('probabilities')==matching.get('probabilities'),'batch_errors':batch.get('errors',[])})
(out/'live-api.json').write_text(json.dumps({'rows':rows,'checks':checks},indent=2))
print(len(rows),'predictions;',sum(r['status']!=200 or bool(r['errors']) for r in rows),'failures')
