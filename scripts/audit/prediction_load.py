"""Bounded concurrent offline inference over immutable audit features."""
import os
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import time,json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
import torch
from vn_stock.config import MODELS_DIR
from vn_stock.features import ALL_FEATURE_COLS,compute_features_per_symbol,transform_model_features
from vn_stock.modeling.predict import load_prediction_snapshot
out=Path('reports/prediction-audit-2026-11-20')
panel=pd.read_parquet(out/'quality/panel_snapshot.parquet');features=compute_features_per_symbol(panel[panel.Symbol=='VIC']).tail(20)
torch.set_num_threads(1)
results={}
for kind in ['lightgbm','lstm']:
 start=time.perf_counter();model,scaler,info=load_prediction_snapshot(kind,MODELS_DIR);cold=time.perf_counter()-start
 scaled=transform_model_features(features,scaler)
 def run(_):
  start=time.perf_counter()
  if kind=='lightgbm':
   p=model.predict(scaled[ALL_FEATURE_COLS].tail(1),num_threads=1) if not hasattr(model,'predict_proba') else model.predict_proba(scaled[ALL_FEATURE_COLS].tail(1))
  else:
   with torch.no_grad():p=model.predict_proba(torch.from_numpy(scaled[ALL_FEATURE_COLS].to_numpy(dtype=np.float32)[None])).numpy()
  assert np.isfinite(p).all() and abs(float(p.sum())-1)<.001
  return time.perf_counter()-start
 levels=[]
 for count in [1,5,10]:
  with ThreadPoolExecutor(max_workers=count) as pool:times=list(pool.map(run,range(count*3)))
  levels.append({'concurrency':count,'requests':len(times),'errors':0,'p50_seconds':float(np.median(times)),'p95_seconds':float(np.quantile(times,.95))})
 results[kind]={'artifact_load_seconds':cold,'levels':levels}
(out/'offline-load.json').write_text(json.dumps({'results':results,'limitations':['Offline inference with a fixed feature snapshot; excludes HTTP, DB and SSI.','Bounded 1/5/10 concurrency, not a capacity/SLA guarantee.']},indent=2))
print('offline concurrency passed for both models')
