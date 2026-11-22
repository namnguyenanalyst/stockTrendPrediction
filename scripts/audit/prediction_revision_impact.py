"""Compare identical serving artifacts on old/reconciled data, in memory only."""
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from vn_stock.modeling.predict import predict_trend


def main():
    root = Path('reports/prediction-audit-2026-11-20')
    paths = {'original':root/'quality/panel_snapshot.parquet',
             'reconciled':root/'reconciled-data/panel_snapshot.parquet'}
    panels = {name:pd.read_parquet(path) for name,path in paths.items()}
    target = str(panels['original'].Date.max().date())
    report = {'data_as_of_date':target,'snapshot_hashes':{
        name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in paths.items()},
        'results':[], 'limitations':['Same legacy serving artifacts; this isolates input revision impact, not model quality.',
                                    'No source datasets or serving artifacts are modified.']}
    for symbol in ('GVR','TCB','VNM'):
        for model in ('lightgbm','lstm'):
            predictions = {}
            for name,panel in panels.items():
                selected = panel[panel.Symbol==symbol].copy()
                with patch('vn_stock.modeling.predict.load_panel_dataset',return_value=selected), \
                     patch('vn_stock.modeling.predict.get_target_market_date',return_value=target):
                    result = predict_trend(symbol,model)
                predictions[name] = {key:result[key] for key in (
                    'data_as_of_date','current_price','class_name','signal','probabilities')}
                predictions[name]['generation'] = result['training_info']['artifact_generation']
            old,new = predictions['original'],predictions['reconciled']
            assert old['generation']==new['generation']
            report['results'].append(dict(symbol=symbol,model=model,predictions=predictions,
                class_changed=old['class_name']!=new['class_name'],signal_changed=old['signal']!=new['signal'],
                max_probability_delta=max(abs(old['probabilities'][key]-new['probabilities'][key]) for key in old['probabilities'])))
    (root/'data-revision-inference-impact.json').write_text(json.dumps(report,indent=2))
    print([{key:r[key] for key in ('symbol','model','class_changed','signal_changed','max_probability_delta')}
           for r in report['results']])


if __name__ == '__main__':
    main()
