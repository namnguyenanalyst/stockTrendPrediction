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
    first = load_prediction_snapshot("lightgbm", tmp_path)
    assert first[:2] == (1, 1)
    assert first[2]["serving_status"] == "healthy"
    publish(tmp_path, 2)
    second = load_prediction_snapshot("lightgbm", tmp_path)
    assert second[:2] == (2, 2)
    assert second[2]["version"] == 2
    files = resolve_bundle(tmp_path, 3)
    files["production_scaler_t3.pkl"].write_bytes(b"corrupt")
    fallback = load_prediction_snapshot("lightgbm", tmp_path)
    assert fallback[:2] == (2, 2)
    assert fallback[2]["artifact_generation"] == second[2]["artifact_generation"]
    assert fallback[2]["serving_status"] == "degraded_cached_generation"
    assert second[2]["serving_status"] == "healthy"
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


def test_concurrent_requests_observe_complete_generations(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    clear_model_cache()
    monkeypatch.setattr('vn_stock.modeling.predict._load_raw_artifacts',
                        lambda **kw: (pickle.loads(kw['model_path'].read_bytes()),
                                      pickle.loads(kw['scaler_path'].read_bytes())))
    publish(tmp_path, 1)
    def read(_):
        snapshots = [load_prediction_snapshot('lightgbm', tmp_path) for _ in range(15)]
        for model, scaler, metadata in snapshots:
            assert model == scaler == metadata['version']
            assert metadata['artifact_generation']
        return len(snapshots)
    def update():
        for version in range(2, 7):
            publish(tmp_path, version)
    with ThreadPoolExecutor(max_workers=6) as pool:
        writer_future = pool.submit(update)
        readers = list(pool.map(read, range(5)))
        writer_future.result()
    assert sum(readers) == 75
    assert load_prediction_snapshot('lightgbm',tmp_path)[:2] == (6,6)
    clear_model_cache()


def test_compatibility_export_failure_does_not_hide_committed_generation(tmp_path, monkeypatch):
    from vn_stock.modeling.artifacts import publish_training_bundle
    publish(tmp_path, 1)
    original = __import__('pathlib').Path.replace
    def fail_compatibility(path, target):
        if str(target).endswith('lightgbm_classifier.pkl'):
            raise OSError('disk full during compatibility export')
        return original(path, target)
    monkeypatch.setattr('pathlib.Path.replace', fail_compatibility)
    result = publish_training_bundle(tmp_path, 3, {
        'production_lgb_t3.pkl': writer(2),
        'production_scaler_t3.pkl': writer(2),
        'production_lstm_t3.pth': writer(2),
    }, {'version': 2}, {'lightgbm_classifier.pkl': 'production_lgb_t3.pkl'})
    assert result['compatibility_export_failures'] == ['lightgbm_classifier.pkl']
    files = resolve_bundle(tmp_path, 3)
    assert pickle.loads(files['production_lgb_t3.pkl'].read_bytes()) == 2
    assert result['artifact_generation'] == files['production_lgb_t3.pkl'].parent.name
    assert not list(tmp_path.glob('.*.tmp'))
