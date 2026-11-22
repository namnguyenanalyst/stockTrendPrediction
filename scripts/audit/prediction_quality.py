"""Reproducible expanding-window audit; never promotes evaluation artifacts."""
import os
os.environ.setdefault('OMP_NUM_THREADS','1')
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, log_loss, roc_auc_score
from vn_stock.data_ingestion import load_panel_dataset
from vn_stock.modeling.evaluation import EvaluationConfig, run_temporal_evaluation

import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,default=Path('reports/prediction-audit-2026-11-20/quality'))
parser.add_argument('--snapshot',type=Path)
args=parser.parse_args()
out=args.output.resolve()
out.mkdir(parents=True, exist_ok=True)
source=args.snapshot or out/'panel_snapshot.parquet'
panel=pd.read_parquet(source) if source.exists() else load_panel_dataset().sort_values(['Date','Symbol']).reset_index(drop=True)
if not (out/'panel_snapshot.parquet').exists():panel.to_parquet(out/'panel_snapshot.parquet',index=False)
(out/'snapshot.json').write_text(json.dumps({'sha256':hashlib.sha256((out/'panel_snapshot.parquet').read_bytes()).hexdigest(),'rows':len(panel),'symbols':sorted(panel.Symbol.unique()),'start':str(panel.Date.min()),'end':str(panel.Date.max())},indent=2))
dates=sorted(panel.Date.unique())
folds=[(dates[-64],dates[-41]),(dates[-44],dates[-21]),(dates[-24],dates[-1])]
all_records=[]
for index,(cutoff,end) in enumerate(folds,1):
 directory=out/f'fold-{index}'
 config=EvaluationConfig(str(pd.Timestamp(cutoff).date()),str(pd.Timestamp(end).date()),epochs=40)
 if not (directory/'evaluation.json').exists():
  if directory.exists():
   import shutil
   shutil.rmtree(directory)
  run_temporal_evaluation(panel,directory,config)
 report=json.loads((directory/'evaluation.json').read_text())
 records=json.loads((directory/'predictions.json').read_text())
 priors=np.array(report['training_info']['train_class_counts'],float);priors/=priors.sum()
 for row in records:row.update(fold=index,train_priors=priors.tolist())
 all_records+=records
 print('Completed fold',index,flush=True)

def score(rows, baseline=False):
 y=np.array([r['label'] for r in rows]);p=np.array([r['train_priors'] if baseline else r['probabilities'] for r in rows]);pred=p.argmax(1)
 result={'n':len(y),'classification':classification_report(y,pred,labels=[0,1,2],output_dict=True,zero_division=0),'log_loss':log_loss(y,p,labels=[0,1,2]),'multiclass_brier':float(np.mean(np.sum((p-np.eye(3)[y])**2,axis=1)))}
 result['roc_auc_ovr_macro']=float(roc_auc_score(y,p,multi_class='ovr')) if len(set(y))==3 else None
 confidence=p.max(1);bins=[]
 for low in np.arange(0,1,.1):
  mask=(confidence>=low)&(confidence<low+.1 if low<.9 else confidence<=1)
  if mask.any():bins.append({'lower':round(float(low),1),'n':int(mask.sum()),'confidence':float(confidence[mask].mean()),'accuracy':float((pred[mask]==y[mask]).mean())})
 result['calibration_bins']=bins
 # Day-block bootstrap preserves cross-stock dependence within a date.
 rng=np.random.default_rng(42);days=sorted({r['date'] for r in rows});byday={d:[i for i,r in enumerate(rows) if r['date']==d] for d in days};acc=[]
 for _ in range(500):
  indices=[i for d in rng.choice(days,len(days),replace=True) for i in byday[d]];acc.append(float((pred[indices]==y[indices]).mean()))
 result['accuracy_day_bootstrap_95ci']=np.quantile(acc,[.025,.975]).tolist()
 return result
summary={}
for model in ['lightgbm','lstm']:
 rows=[r for r in all_records if r['model']==model]
 summary[model]={'overall':score(rows),'by_symbol':{s:score([r for r in rows if r['symbol']==s]) for s in sorted({r['symbol'] for r in rows})},'by_fold':{str(i):score([r for r in rows if r['fold']==i]) for i in [1,2,3]}}
summary['train_prior_baseline']=score([r for r in all_records if r['model']=='lightgbm'],True)
summary['limitations']=['Three fixed expanding-window folds, no test-set tuning.','Current constituents, not survivorship-adjusted.','Bootstrap by date does not fully account for overlapping T+3 labels.','Classification only; no claim of investment profitability.','Historical isolated retraining, not an independent validation of deployed legacy artifacts.']
(out/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({k:v.get('overall',v) for k,v in summary.items() if k!='limitations'},indent=2),flush=True)
