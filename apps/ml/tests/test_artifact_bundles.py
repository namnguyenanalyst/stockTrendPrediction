import json
import pickle

import pytest

from vn_stock.modeling.artifacts import publish_bundle, resolve_bundle
from vn_stock.modeling.predict import clear_model_cache, load_prediction_snapshot


def writer(value):
    return lambda path: path.write_bytes(pickle.dumps(value))


def publish(root, value):
    return publish_bundle(root, 3, {
        "production_lgb_t3.pkl": writer(value),
        "production_scaler_t3.pkl": writer(value),
        "production_lstm_t3.pth": writer(value),
    }, {"version": value, "horizon_days": 3})


def test_failed_publish_keeps_previous_generation_visible(tmp_path):
    publish(tmp_path, 1)
    previous = (tmp_path / "production_bundle_t3.json").read_bytes()
    def fail(path):
        raise OSError("disk full")
    with pytest.raises(OSError):
        publish_bundle(tmp_path, 3, {"production_lgb_t3.pkl": fail}, {})
    assert (tmp_path / "production_bundle_t3.json").read_bytes() == previous
    files = resolve_bundle(tmp_path, 3)
    assert pickle.loads(files["production_lgb_t3.pkl"].read_bytes()) == 1


def test_snapshot_reload_never_pairs_new_model_with_old_scaler(tmp_path, monkeypatch):
    clear_model_cache()
    monkeypatch.setattr("vn_stock.modeling.predict._load_raw_artifacts",
                        lambda **kw: (pickle.loads(kw["model_path"].read_bytes()),
                                      pickle.loads(kw["scaler_path"].read_bytes())))
    publish(tmp_path, 1)
    assert load_prediction_snapshot("lightgbm", tmp_path) == (1, 1, {"version": 1, "horizon_days": 3})
    publish(tmp_path, 2)
    assert load_prediction_snapshot("lightgbm", tmp_path) == (2, 2, {"version": 2, "horizon_days": 3})
    files = resolve_bundle(tmp_path, 3)
    files["production_scaler_t3.pkl"].write_bytes(b"corrupt")
    assert load_prediction_snapshot("lightgbm", tmp_path) == (2, 2, {"version": 2, "horizon_days": 3})
    clear_model_cache()
    with pytest.raises(ValueError, match="hash"):
        load_prediction_snapshot("lightgbm", tmp_path)


def test_manifest_cannot_escape_generation_directory(tmp_path):
    publish(tmp_path, 1)
    path = tmp_path / "production_bundle_t3.json"
    data = json.loads(path.read_text())
    data["files"]["production_scaler_t3.pkl"]["path"] = "../external.pkl"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="path"):
        resolve_bundle(tmp_path, 3)
