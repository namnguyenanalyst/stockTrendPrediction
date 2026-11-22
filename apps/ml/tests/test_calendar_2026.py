from datetime import datetime
from vn_stock.market_session import get_target_market_date,get_future_trading_days,get_target_market_session_info


def test_new_year_extended_holiday_and_weekend():
    assert get_target_market_date(datetime(2026,1,2,16)) == '2025-12-31'
    assert [d['date'] for d in get_future_trading_days('2025-12-31')] == ['2026-01-05','2026-01-06','2026-01-07']


def test_lunar_new_year_and_national_day():
    assert get_target_market_date(datetime(2026,2,20,16)) == '2026-02-13'
    assert get_future_trading_days('2026-02-13')[0]['date'] == '2026-02-23'
    assert get_future_trading_days('2026-08-28')[0]['date'] == '2026-09-03'
    info=get_target_market_session_info(datetime(2026,9,2,16))
    assert info['is_market_closed'] is True
    assert info['is_holiday'] is True
    assert info['target_date']=='2026-08-28'


def test_calendar_does_not_claim_future_years_verified():
    info=get_target_market_session_info(datetime(2027,1,4,16))
    assert info['holiday_calendar_verified'] is False
