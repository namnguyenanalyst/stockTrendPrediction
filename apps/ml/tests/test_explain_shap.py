import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from vn_stock.features import ALL_FEATURE_COLS, FEATURE_COLS
from vn_stock.modeling.explain_shap import prepare_shap_sample


def test_shap_inputs_match_inference_scaling_without_changing_symbol_code():
    frame = pd.DataFrame(np.arange(52).reshape(4, 13), columns=FEATURE_COLS)
    scaler = StandardScaler().fit(frame)
    frame["Symbol_Code"] = [25, 25, 25, 25]
    sample = prepare_shap_sample(frame, scaler, 4).sort_index()
    np.testing.assert_allclose(sample[FEATURE_COLS], scaler.transform(frame[FEATURE_COLS]))
    assert sample.Symbol_Code.tolist() == [25] * 4
    assert sample.columns.tolist() == ALL_FEATURE_COLS
