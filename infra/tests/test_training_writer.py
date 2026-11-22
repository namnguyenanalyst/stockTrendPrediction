"""Training writes through an internal service; inference mounts stay read-only."""
import importlib.util
from pathlib import Path
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('training_entrypoint', ROOT / 'infra/scripts/training_api_entrypoint.py')
entrypoint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entrypoint)


@pytest.mark.parametrize('relative', ['docker-compose.yml', 'infra/docker-compose.yml'])
def test_worker_targets_private_writer_with_same_runtime(relative):
    services = yaml.safe_load((ROOT / relative).read_text())['services']
    reader = services['vn_stock_api']
    writer = services['vn_stock_training_api']
    worker = services['vn_stock_retrain_worker']
    assert writer['image'] == reader['image']
    assert 'ports' not in writer
    assert writer['user'] == '${ML_WRITER_UID:-1001}:${ML_WRITER_GID:-1001}'
    assert writer['environment']['AUTO_SYNC_ON_STARTUP'] == 'false'
    assert writer['environment']['INTERNAL_WORKER_SECRET'] == reader['environment']['INTERNAL_WORKER_SECRET']
    for area in ('models', 'data'):
        assert any(f'/app/apps/ml/{area}:ro' in mount for mount in reader['volumes'])
        assert any(mount.endswith(f':/app/apps/ml/{area}') for mount in writer['volumes'])
    assert worker['environment']['API_BASE_URL'] == 'http://vn_stock_training_api:8000'
    assert worker['depends_on']['vn_stock_training_api']['condition'] == 'service_healthy'


def test_preflight_requires_secret_and_probes_without_leaving_files(tmp_path, monkeypatch):
    monkeypatch.delenv('INTERNAL_WORKER_SECRET', raising=False)
    with pytest.raises(RuntimeError, match='INTERNAL_WORKER_SECRET'):
        entrypoint.verify_training_storage(tmp_path)
    monkeypatch.setenv('INTERNAL_WORKER_SECRET', 'test-only')
    entrypoint.verify_training_storage(tmp_path)
    assert all(not list((tmp_path / directory).iterdir()) for directory in ('models', 'data/raw', 'data/interim', 'data/processed'))
