"""Inspect frozen audit data and deployed artifact provenance without mutation."""
from pathlib import Path
import json
import pandas as pd
import numpy as np
from vn_stock.config import MODELS_DIR
from vn_stock.features import compute_features_per_symbol,FEATURE_COLS
from vn_stock.modeling.predict import load_prediction_snapshot
out=Path('reports/prediction-audit-2026-11-20')
panel=pd.read_parquet(out/'quality/panel_snapshot.parquet')
issues={}
for symbol,g in panel.groupby('Symbol'):
 g=g.sort_values('Date');bad=(g.High<g[['Open','Close','Low']].max(axis=1))|(g.Low>g[['Open','Close','High']].min(axis=1))|(g.Volume<0)|(g.Close<=0)
 issues[symbol]={'rows':len(g),'last_date':str(g.Date.max()),'duplicate_dates':int(g.Date.duplicated().sum()),'invalid_ohlcv':int(bad.sum()),'missing_ohlcv':int(g[['Open','High','Low','Close','Volume']].isna().any(axis=1).sum()),'largest_absolute_daily_return':float(g.Close.pct_change().abs().max())}
features=compute_features_per_symbol(panel)
cutoff=sorted(panel.Date.unique())[-60]
prior=compute_features_per_symbol(panel[panel.Date<=cutoff])
comparison=features[features.Date<=cutoff].reset_index(drop=True)
pd.testing.assert_frame_equal(prior.reset_index(drop=True),comparison)
artifacts={}
for model in ['lightgbm','lstm']:
 _,scaler,info=load_prediction_snapshot(model,MODELS_DIR)
 artifacts[model]={'metadata':info,'scaler_features':getattr(scaler,'n_features_in_',None),'nonnumeric_feature_values':int((~np.isfinite(features[FEATURE_COLS].to_numpy())).sum())}
(out/'data-model-audit.json').write_text(json.dumps({'symbols':issues,'past_features_unchanged_by_future':True,'artifacts':artifacts,'limitations':['No verified corporate-action provenance found: largest returns are flags, not proof of corrupt data.','Production legacy artifact metadata may not prove exact train/validation provenance.']},indent=2,default=str))
print('data audit',len(issues),'symbols; causal feature check passed')
