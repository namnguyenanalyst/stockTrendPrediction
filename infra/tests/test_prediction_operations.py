"""Freshness checks must not confuse successful HTTP with fresh predictions."""
import importlib.util
from pathlib import Path
from datetime import datetime, timezone

path = Path(__file__).resolve().parents[2] / 'scripts/audit/prediction_operations.py'
spec = importlib.util.spec_from_file_location('prediction_operations', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def prediction(**overrides):
    row = {'symbol':'VIC','model_type':'lightgbm','data_as_of_date':'2026-11-20',
           'training_info':{'timestamp':'2026-11-14T02:00:00+07:00','serving_status':'healthy'}}
    return {**row, **overrides}


def test_detects_stopped_worker_even_when_predictions_are_fresh():
    now = datetime(2026,11,21,tzinfo=timezone.utc)
    assert module.assess(False,[prediction()],'2026-11-20',now)==[{'code':'worker_not_running'}]


def test_detects_stale_data_degraded_model_and_old_or_unknown_training_time():
    now = datetime(2026,11,21,tzinfo=timezone.utc)
    stale = prediction(data_as_of_date='2026-11-19',training_info={
        'timestamp':'2026-10-01T00:00:00','serving_status':'degraded_cached_generation'})
    codes={x['code'] for x in module.assess(True,[stale, prediction(training_info={})],'2026-11-20',now)}
    assert codes=={'data_date_mismatch','artifact_not_healthy','artifact_age_outside_policy','artifact_training_time_unknown'}
