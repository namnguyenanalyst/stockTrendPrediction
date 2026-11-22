"""A successful live refresh must not silently return a covering old cache."""
from unittest.mock import patch
import pandas as pd
import pytest
from vn_stock.data_ingestion import fetch_stock_data


def prices(close):
    return pd.DataFrame({'Date':pd.bdate_range('2024-01-01','2024-01-10'),
                         'Open':close,'High':close,'Low':close,'Close':close,'Volume':100})


def test_required_refresh_raises_instead_of_using_covering_cache_after_vendor_failure():
    with patch('vn_stock.data_ingestion.load_local_data',return_value=prices(10)), \
         patch('vn_stock.data_ingestion.SSIFastConnectClient') as client:
        client.return_value.get_daily_ohlcv.side_effect=OSError('isolated unavailable')
        with pytest.raises(RuntimeError,match='refresh'):
            fetch_stock_data('VIC','2024-01-01','2024-01-10',save_to_raw=False,require_fresh=True)


def test_required_refresh_replaces_revised_history_in_memory_even_when_dates_are_unchanged():
    with patch('vn_stock.data_ingestion.load_local_data',return_value=prices(10)), \
         patch('vn_stock.data_ingestion.SSIFastConnectClient') as client:
        client.return_value.get_daily_ohlcv.return_value=prices(5)
        result=fetch_stock_data('VIC','2024-01-01','2024-01-10',save_to_raw=False,require_fresh=True)
    assert result.Close.tolist()==[5]*len(result)
    assert client.return_value.get_daily_ohlcv.call_args.kwargs['start_date']=='2024-01-01'


def test_panel_build_resolves_one_current_cutoff_per_call(monkeypatch):
    from vn_stock.data_ingestion import build_panel_dataset
    frame = prices(10).assign(Symbol='VIC')
    index = frame[['Date']].assign(VNINDEX_Return_1d=0.)
    cutoffs = iter(['2024-01-09', '2024-01-10'])
    monkeypatch.setattr('vn_stock.data_ingestion.get_default_end_date', lambda: next(cutoffs))
    with patch('vn_stock.data_ingestion.fetch_stock_data', return_value=frame) as stock, \
         patch('vn_stock.data_ingestion.fetch_daily_index', return_value=index) as market, \
         patch('vn_stock.data_ingestion.check_cache_coverage', return_value=True):
        first = build_panel_dataset(['VIC'], start_date='2024-01-01', save_to_interim=False)
        second = build_panel_dataset(['VIC'], start_date='2024-01-01', save_to_interim=False)
    assert first.Date.max() == pd.Timestamp('2024-01-09')
    assert second.Date.max() == pd.Timestamp('2024-01-10')
    assert [call.kwargs['end_date'] for call in stock.call_args_list] == ['2024-01-09', '2024-01-10']
    assert [call.kwargs['end_date'] for call in market.call_args_list] == ['2024-01-09', '2024-01-10']


@pytest.mark.parametrize('outcome', [OSError('sync unavailable'), {'status':'partial','errors':{'VIC':'missing data'}}])
def test_production_training_does_not_fall_through_failed_sync(outcome, tmp_path):
    from vn_stock.modeling.train import train_production_model
    kwargs = {'side_effect': outcome} if isinstance(outcome, Exception) else {'return_value': outcome}
    with patch('vn_stock.data_ingestion.sync_latest_market_data', **kwargs), \
         patch('vn_stock.modeling.train.build_panel_dataset') as build:
        with pytest.raises(RuntimeError, match='synchronization'):
            train_production_model(symbols=['VIC'], models_dir=tmp_path)
    build.assert_not_called()
    assert not list(tmp_path.iterdir())


def test_sync_reports_panel_publish_failure_instead_of_success():
    from vn_stock.data_ingestion import sync_latest_market_data
    with patch('vn_stock.data_ingestion.fetch_stock_data', return_value=prices(10)), \
         patch('vn_stock.data_ingestion.fetch_daily_index', return_value=prices(1000)), \
         patch('vn_stock.data_ingestion.build_panel_dataset', side_effect=OSError('isolated panel publish failure')):
        result = sync_latest_market_data(['VIC'])
    assert result['status'] == 'partial'
    assert 'panel' in result['errors']
