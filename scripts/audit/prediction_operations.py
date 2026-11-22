"""Read-only operational checks; never starts workers or retrains artifacts."""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
from urllib.request import urlopen

ICT = timezone(timedelta(hours=7))


def assess(worker_running, predictions, target_date, now, max_model_age_days=8):
    """Report freshness independently of HTTP health. Age policy is explicit."""
    findings = []
    if not worker_running:
        findings.append({'code': 'worker_not_running'})
    for prediction in predictions:
        context = {'symbol': prediction['symbol'], 'model': prediction['model_type']}
        date = prediction.get('data_as_of_date') or prediction.get('date')
        if date != target_date:
            findings.append({**context, 'code': 'data_date_mismatch', 'actual': date, 'expected': target_date})
        info = prediction.get('training_info') or {}
        if info.get('serving_status') != 'healthy':
            findings.append({**context, 'code': 'artifact_not_healthy', 'status': info.get('serving_status')})
        stamp = info.get('timestamp')
        try:
            trained = datetime.fromisoformat(stamp)
            if trained.tzinfo is None:
                trained = trained.replace(tzinfo=ICT)
            age = (now - trained).total_seconds() / 86400
            if age < 0 or age > max_model_age_days:
                findings.append({**context, 'code': 'artifact_age_outside_policy', 'age_days': round(age, 3)})
        except (TypeError, ValueError):
            findings.append({**context, 'code': 'artifact_training_time_unknown'})
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-model-age-days', type=int, default=8)
    args = parser.parse_args()
    from vn_stock.market_session import get_target_market_date

    def get(path):
        with urlopen('http://localhost:8000' + path, timeout=60) as response:
            return json.load(response)

    containers = subprocess.check_output(
        ['docker', 'ps', '--format', '{{.Names}}'], text=True).splitlines()
    predictions = [get(f'/api/predict/signal?symbol={symbol}&model_type={model}')
                   for symbol in ('VIC', 'HPG') for model in ('lightgbm', 'lstm')]
    target = get_target_market_date()
    now = datetime.now(ICT)
    worker_running = 'vn_stock_retrain_worker' in containers
    report = {'observed_at': now.isoformat(), 'health': get('/health'),
              'target_date': target, 'max_model_age_days': args.max_model_age_days,
              'worker_running': worker_running,
              'findings': assess(worker_running, predictions, target, now, args.max_model_age_days),
              'limitations': ['Worker container presence does not prove a successful scheduled run.',
                             'Legacy naive training timestamps are interpreted as Vietnam time.',
                             'Eight-day age policy is an operational threshold, not model quality evidence.']}
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
