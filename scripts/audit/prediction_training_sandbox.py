"""Bootstrap ONLY a disposable, unmounted training-audit Docker container.

Never install this bootstrap in a production service. Real SSI calls are observed,
not replaced; fault controls and fake accounts exist only in the isolated container.
"""
import os
from pathlib import Path
import shutil
import json
import asyncio
import time


def main():
    assert os.environ.get('CORE_TRAINING_SANDBOX') == '1'
    assert Path('/.dockerenv').exists() and Path('/app/apps/ml').is_dir()
    assert os.geteuid() == 0, 'Bootstrap needs root only to assign private copy ownership'
    ml=Path('/app/apps/ml')
    first_boot = not Path('/tmp/core-trim-proof.json').exists()
    if first_boot:
        for name in ['data','models']:
            incoming=Path('/tmp/core-copy')/name
            assert incoming.is_dir()
            destination=ml/name
            if destination.exists():shutil.rmtree(destination)
            shutil.copytree(incoming,destination)
            for item in [destination,*destination.rglob('*')]:os.chown(item,1001,1001)
    os.setgroups([]);os.setgid(1001);os.setuid(1001)

    import pandas as pd
    from vn_stock.config import DEFAULT_SYMBOLS,RAW_DATA_DIR
    if first_boot:
        trimmed=[]
        for symbol in [*DEFAULT_SYMBOLS,'VNINDEX','VN30']:
            path=RAW_DATA_DIR/f'{symbol}.parquet'
            frame=pd.read_parquet(path).sort_values('Date')
            frame.iloc[:-2].to_parquet(path,index=False)
            trimmed.append({'symbol':symbol,'original_end':str(pd.Timestamp(frame.Date.max()).date()),
                            'trimmed_end':str(pd.Timestamp(frame.iloc[:-2].Date.max()).date())})
        Path('/tmp/core-trim-proof.json').write_text(json.dumps(trimmed,indent=2))

    from vn_stock.ssi_client import SSIFastConnectClient
    def observe(method,kind):
        def call(client,*args,**kwargs):
            fault_path=Path('/tmp/core-faults.json')
            faults=json.loads(fault_path.read_text()) if fault_path.exists() else {}
            record={'kind':kind,'symbol':kwargs.get('symbol',kwargs.get('index_id')),
                    'start_date':kwargs.get('start_date'),'end_date':kwargs.get('end_date')}
            started=time.perf_counter()
            try:
                if faults.get('source_unavailable'):raise RuntimeError('Isolated SSI failure fixture')
                result=method(client,*args,**kwargs)
                record.update(status='success',rows=len(result))
                return result
            except Exception as error:
                record.update(status='error',error_type=type(error).__name__)
                raise
            finally:
                record['seconds']=round(time.perf_counter()-started,3)
                with Path('/tmp/core-ssi-calls.jsonl').open('a') as stream:
                    stream.write(json.dumps(record)+'\n')
        return call
    SSIFastConnectClient.get_daily_ohlcv=observe(SSIFastConnectClient.get_daily_ohlcv,'stock')
    SSIFastConnectClient.get_daily_index=observe(SSIFastConnectClient.get_daily_index,'index')

    from app.core.config import settings
    assert str(settings.DATA_DIR).startswith('/app/apps/ml/')
    assert str(settings.MODELS_DIR).startswith('/app/apps/ml/')
    assert settings.DATABASE_URL.startswith('sqlite+')
    from app.main import app
    from app.db.models import Base
    from app.db.models.user import User
    from app.db.session import engine,async_session_factory
    from sqlalchemy import select
    from app.core.security import get_password_hash
    from vn_stock.modeling.predict import load_prediction_snapshot
    before={kind:load_prediction_snapshot(kind,models_dir=settings.MODELS_DIR)[2]['artifact_generation']
            for kind in ['lightgbm','lstm']}
    Path('/tmp/core-generation-before.json').write_text(json.dumps(before))
    async def seed():
        async with engine.begin() as connection:await connection.run_sync(Base.metadata.create_all)
        async with async_session_factory() as session:
            existing = await session.scalar(select(User).where(User.email == 'core-audit@example.test'))
            if existing is None:
                session.add(User(email='core-audit@example.test',full_name='Core Audit Test',
                                 hashed_password=get_password_hash('CoreAuditOnly2026!')))
                await session.commit()
    asyncio.run(seed())
    import uvicorn
    uvicorn.run(app,host='0.0.0.0',port=8000)


if __name__=='__main__':main()
