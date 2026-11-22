from unittest.mock import patch
import pytest
from fastapi import HTTPException
from app.services.prediction_service import predict_batch_signals


def test_prediction_logs_link_symbol_model_date_and_generation(caplog):
    import logging
    from app.services.prediction_service import predict_stock_signal
    result = dict(symbol='VIC', date='2026-11-20', current_price=241.9,
                  model_type='lightgbm', predicted_label=0, class_name='GIẢM',
                  signal='BÁN (SELL)', probabilities={'GIẢM':.6,'ĐI NGANG':.3,'TĂNG':.1},
                  training_info={'artifact_generation':'audit-generation','serving_status':'healthy'})
    with caplog.at_level(logging.INFO), patch('vn_stock.modeling.predict_trend',return_value=result):
        predict_stock_signal(' vic ', 'lightgbm')
    records=[r for r in caplog.records if getattr(r,'event',None)=='prediction_completed']
    assert len(records)==1
    record=records[0]
    assert (record.symbol,record.model_type,record.data_as_of_date,record.artifact_generation)==(
        'VIC','lightgbm','2026-11-20','audit-generation')
    assert record.elapsed_ms >= 0
    assert 'audit-generation' in record.getMessage()


def test_batch_exposes_failed_symbols():
    with patch('app.services.prediction_service.predict_stock_signal',side_effect=HTTPException(503,'Unavailable')):
        result=predict_batch_signals(symbols=['VIC','HPG'])
    assert result.requested_symbols == 2
    assert result.total_symbols == 0
    assert {e.symbol for e in result.errors} == {'VIC','HPG'}
    assert {e.status_code for e in result.errors} == {503}


def test_live_sync_failure_is_not_successful_cached_prediction():
    from app.services.prediction_service import sync_live_and_predict
    with patch('vn_stock.data_ingestion.fetch_stock_data', side_effect=RuntimeError('upstream private detail')):
        with pytest.raises(HTTPException) as exc:
            sync_live_and_predict('VIC', 'lightgbm')
    assert exc.value.status_code == 503
    assert 'private' not in exc.value.detail


def test_live_sync_stale_data_is_rejected_before_inference():
    import pandas as pd
    from app.services.prediction_service import sync_live_and_predict
    old = pd.DataFrame({'Date':pd.to_datetime(['2020-01-01'])})
    with patch('vn_stock.data_ingestion.fetch_stock_data',return_value=old), patch('vn_stock.modeling.predict_trend') as infer:
        with pytest.raises(HTTPException) as exc:
            sync_live_and_predict('VIC', 'lstm')
    assert exc.value.status_code == 503
    infer.assert_not_called()


def test_live_sync_requires_vendor_refresh_even_if_cache_covers_today():
    import pandas as pd
    from app.services.prediction_service import sync_live_and_predict
    with patch('vn_stock.data_ingestion.fetch_stock_data',return_value=pd.DataFrame()) as fetch:
        with pytest.raises(HTTPException):
            sync_live_and_predict('VIC','lightgbm')
    assert fetch.call_args.kwargs.get('require_fresh') is True






@pytest.mark.asyncio
@pytest.mark.parametrize('prefix', ['/api', '/api/v1'])
@pytest.mark.parametrize('method', ['GET','POST'])
async def test_live_write_requires_authentication(async_client, prefix, method):
    with patch('app.services.prediction_service.sync_live_and_predict',side_effect=HTTPException(418,'reached inference')) as infer:
        response = await async_client.request(method,prefix+'/predict/live',json={'symbol':'VIC'} if method=='POST' else None)
    assert response.status_code == 401
    infer.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize('role', ['trader','admin'])
@pytest.mark.parametrize('active', [True,False])
@pytest.mark.parametrize('endpoint', ['/api/predict/live','/api/stocks/sync'])
async def test_live_write_role_matrix_real_tokens(async_client,db_session,role,active,endpoint):
    import uuid
    from app.db.models.user import User,UserRole
    from app.core.security import create_access_token
    user=User(id=uuid.uuid4(),email=f'{uuid.uuid4().hex}@example.test',hashed_password='unused',role=UserRole(role),is_active=active)
    db_session.add(user)
    await db_session.commit()
    token=create_access_token(user.id,extra_claims={'role':role})
    with patch('app.services.prediction_service.sync_live_and_predict',side_effect=HTTPException(418,'reached inference')) as infer, patch('app.services.prediction_service.trigger_market_sync',side_effect=HTTPException(418,'reached sync')) as sync:
        response=await async_client.post(endpoint,json={'symbol':'VIC'},headers={'Authorization':f'Bearer {token}'})
    assert response.status_code == (418 if active else 400)
    assert (infer.call_count + sync.call_count) == (1 if active else 0)


@pytest.mark.asyncio
async def test_valid_worker_secret_cannot_authenticate_as_user(async_client,monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings,'INTERNAL_WORKER_SECRET','isolated-worker-test-key')
    response=await async_client.get('/api/predict/live',headers={'X-Internal-Worker-Secret':'isolated-worker-test-key'})
    assert response.status_code == 401






@pytest.mark.parametrize('model',['lightgbm','lstm'])
def test_live_inference_consumes_fetched_request_snapshot(model):
    import pandas as pd
    from app.services.prediction_service import sync_live_and_predict
    snapshot = pd.DataFrame({'Date':pd.to_datetime(['2026-11-20']), 'Symbol':['VIC'], 'Close':[245.]})
    result = dict(symbol='VIC', date='2026-11-20', data_as_of_date='2026-11-20', current_price=245.,
                  model_type=model, predicted_label=1, class_name='ĐI NGANG', signal='NẮM GIỮ (HOLD)',
                  probabilities={'GIẢM':.2,'ĐI NGANG':.6,'TĂNG':.2},
                  data_quality={'source_provenance':'SSI_request_snapshot'})
    with patch('vn_stock.data_ingestion.fetch_live_prediction_panel',return_value=snapshot) as fetch, \
         patch('vn_stock.data_ingestion.fetch_stock_data',side_effect=AssertionError('shared-cache path used')), \
         patch('vn_stock.market_session.get_target_market_date',return_value='2026-11-20'), \
         patch('vn_stock.modeling.predict_trend',return_value=result) as infer:
        response = sync_live_and_predict(' vic ',model)
    fetch.assert_called_once_with('VIC','2026-11-20')
    assert infer.call_args.kwargs['raw_snapshot'] is snapshot
    assert infer.call_args.kwargs['is_live_synced'] is True
    assert response.is_live_synced is True
    assert response.data_quality['source_provenance'] == 'SSI_request_snapshot'


@pytest.mark.asyncio
@pytest.mark.parametrize('prefix',['/api','/api/v1'])
@pytest.mark.parametrize('method',['GET','POST'])
async def test_live_snapshot_http_contract_uses_request_local_data(async_client,monkeypatch,prefix,method):
    import pandas as pd
    from app.main import app
    from app.core.deps import get_current_active_user
    monkeypatch.setitem(app.dependency_overrides,get_current_active_user,lambda: object())
    snapshot=pd.DataFrame({'Date':pd.to_datetime(['2026-11-20']),'Symbol':['VIC'],'Close':[245.]})
    probabilities={'GIẢM':.2,'ĐI NGANG':.6,'TĂNG':.2}
    prediction=dict(symbol='VIC',date='2026-11-20',current_price=245.,model_type='lightgbm',
                    predicted_label=1,class_name='ĐI NGANG',signal='NẮM GIỮ (HOLD)',probabilities=probabilities,
                    data_quality={'historical_adjustment_status':'unverified','source_provenance':'SSI_request_snapshot'},
                    trajectory=[dict(day_offset=i,day_name=f'T+{i}',predicted_trend='ĐI NGANG',
                                     signal='NẮM GIỮ (HOLD)',confidence=.6,probabilities=probabilities)
                                for i in [1,2,3]])
    with patch('vn_stock.data_ingestion.fetch_live_prediction_panel',return_value=snapshot), \
         patch('vn_stock.data_ingestion.fetch_stock_data',side_effect=AssertionError('Unexpected cache access')), \
         patch('vn_stock.market_session.get_target_market_date',return_value='2026-11-20'), \
         patch('vn_stock.modeling.predict_trend',return_value=prediction) as infer:
        kwargs={'json':{'symbol':'VIC'}} if method=='POST' else {'params':{'symbol':'VIC'}}
        response=await async_client.request(method,prefix+'/predict/live',**kwargs)
    assert response.status_code==200,response.text
    assert response.json()['is_live_synced'] is True
    assert response.json()['data_quality']['source_provenance']=='SSI_request_snapshot'
    assert len(response.json()['trajectory'])==3
    assert infer.call_args.kwargs['raw_snapshot'] is snapshot


@pytest.mark.parametrize('scope',['CORE','VN30'])
def test_retrain_scope_reaches_training_pipeline_without_expanding_universe(scope):
    from app.services.prediction_service import retrain_production_system
    with patch('vn_stock.modeling.train.train_production_model',return_value={'status':'success'}) as train:
        retrain_production_system(scope=scope)
    assert train.call_args.kwargs['symbols']==scope
