import json
import numpy as np
import pandas as pd
import pytest
from app.services import stock_service
from app.routers.stocks import router


@pytest.mark.parametrize('symbol', ['HPG', 'VNINDEX'])
def test_history_before_limit_and_finite_values(monkeypatch, symbol):
    close = np.arange(250, dtype=float) + 50
    raw = pd.DataFrame({'Date': pd.date_range('2020-01-01', periods=250), 'Close': close, 'High': close+1, 'Low': close-1, 'Volume': close*100})
    monkeypatch.setattr(stock_service, 'load_stock_dataframe', lambda _: raw)
    result = stock_service.get_chart_indicators(symbol, 1)
    assert result['total_bars'] == 250
    assert len(result['indicators']) == 1
    assert result['indicators'][0]['values']['SMA200'] == close[-200:].mean()
    json.dumps(result, allow_nan=False)


def test_short_and_empty_history(monkeypatch):
    raw = pd.DataFrame({'Date': pd.date_range('2020-01-01', periods=1), 'Close': [10.], 'High': [11.], 'Low': [9.], 'Volume': [100.]})
    monkeypatch.setattr(stock_service, 'load_stock_dataframe', lambda _: raw)
    assert stock_service.get_chart_indicators('HPG')['indicators'][0]['values']['SMA200'] is None
    monkeypatch.setattr(stock_service, 'load_stock_dataframe', lambda _: raw.iloc[:0])
    assert stock_service.get_chart_indicators('HPG')['indicators'] == []


def test_endpoint_registered():
    assert '/stocks/chart-indicators' in [r.path for r in router.routes]


def test_history_merges_fresh_raw_with_older_panel(monkeypatch, tmp_path):
    from app.core.config import settings
    panel = tmp_path / 'interim/panel/Symbol=VIC'
    panel.mkdir(parents=True)
    raw_dir = tmp_path / 'raw'
    raw_dir.mkdir()
    def frame(dates, closes):
        return pd.DataFrame({'Date':pd.to_datetime(dates),'Open':closes,'High':closes,'Low':closes,'Close':closes,'Volume':[100]*len(dates)})
    frame(['2026-11-17','2026-11-18'],[240.,245.]).to_parquet(panel/'part.parquet')
    frame(['2026-11-18','2026-11-20'],[246.,241.9]).to_parquet(raw_dir/'VIC.parquet')
    monkeypatch.setattr(settings,'DATA_DIR',tmp_path)
    result=stock_service.get_stock_history('VIC')
    assert [b.date for b in result.bars]==['2026-11-17','2026-11-18','2026-11-20']
    assert result.bars[-1].close==241.9
    assert result.bars[1].close==246.
