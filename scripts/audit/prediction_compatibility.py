"""Compare actual serving preprocessing/model outputs across isolated runtimes."""
import os
os.environ.setdefault('OMP_NUM_THREADS','1')
import argparse,json,platform,warnings
from pathlib import Path
from importlib.metadata import version
import numpy as np
import pandas as pd
from vn_stock.features import ALL_FEATURE_COLS,FEATURE_COLS,transform_model_features
from vn_stock.modeling.predict import load_prediction_snapshot


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts',type=Path,required=True)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    data=np.load(args.input,allow_pickle=False)
    assert list(data['feature_cols'])==FEATURE_COLS
    frame=pd.DataFrame(data['numeric'],columns=FEATURE_COLS)
    frame['Symbol_Code']=data['symbol_code']
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        model,scaler,info=load_prediction_snapshot('lightgbm',models_dir=args.artifacts)
        transformed=transform_model_features(frame,scaler)
        inputs=transformed[ALL_FEATURE_COLS]
        probabilities=model.predict_proba(inputs) if hasattr(model,'predict_proba') else model.predict(inputs)
        import torch
        lstm,lstm_scaler,_=load_prediction_snapshot('lstm',models_dir=args.artifacts)
        lstm_inputs=transform_model_features(frame,lstm_scaler)[ALL_FEATURE_COLS]
        sequences=np.stack([lstm_inputs[frame.Symbol_Code==code].tail(20).to_numpy(dtype=np.float32)
                            for code in sorted(frame.Symbol_Code.unique())])
        with torch.no_grad():
            lstm_probabilities=lstm.predict_proba(torch.from_numpy(sequences)).cpu().numpy()
    assert np.isfinite(probabilities).all()
    assert np.allclose(np.sum(probabilities,axis=1),1,atol=1e-9)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    np.savez(args.output,scaled=inputs.to_numpy(dtype=np.float64),probabilities=probabilities,lstm_probabilities=lstm_probabilities)
    metadata={'python':platform.python_version(),'platform':platform.platform(),
              'versions':{name:version(name) for name in ['scikit-learn','numpy','pandas','lightgbm','torch']},
              'rows':len(frame),'artifact_generation':info.get('artifact_generation'),
              'warnings':[{'type':type(w.message).__name__,'message':str(w.message)} for w in caught]}
    args.output.with_suffix('.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
    print(json.dumps({k:metadata[k] for k in ['versions','rows','artifact_generation']}))


if __name__=='__main__':main()
