import numpy as np
import pandas as pd
import pytest

from vn_stock.modeling.evaluation import EvaluationConfig, prepare_temporal_holdout
from vn_stock.modeling.train import evaluate_predictions


def test_holdout_training_panel_excludes_future_and_scores_only_matured_labels():
    dates = pd.bdate_range("2023-01-02", periods=300)
    frame = pd.DataFrame({"Date": dates, "Symbol": "VIC", "Open": 50., "High": 51.,
                          "Low": 49., "Close": 50., "Volume": 1000., "VNINDEX_Return_1d": 0.})
    config = EvaluationConfig(str(dates[269].date()), str(dates[-1].date()))
    train, features, test = prepare_temporal_holdout(frame, config)
    assert train.Date.max() == dates[269]
    assert test.Date.min() == dates[270]
    assert test.Date.max() == dates[-4]
    modified = frame.copy()
    modified.loc[270:, "Close"] = 500.
    other_train, other_features, _ = prepare_temporal_holdout(modified, config)
    pd.testing.assert_frame_equal(train, other_train)
    pd.testing.assert_frame_equal(features[features.Date <= dates[269]],
                                  other_features[other_features.Date <= dates[269]])


def test_classification_always_reports_three_classes_even_if_test_has_one():
    metrics = evaluate_predictions(np.array([1, 1]), np.array([1, 1]))
    assert np.array(metrics["confusion_matrix"]).shape == (3, 3)
    assert metrics["macro_f1"] == pytest.approx(1 / 3)
