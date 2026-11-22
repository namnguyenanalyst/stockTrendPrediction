"""Local isolated E2E harness. Test-only SQLite and fake accounts; never deploy.
Run with PYTHONPATH=apps/api:apps/ml apps/api/.venv/bin/python this_file.py.
Fault controls: /tmp/stock-prediction-e2e/faults.json; no production endpoints added.
"""
import os,asyncio
os.environ['DATABASE_URL']='sqlite+aiosqlite:////tmp/stock-prediction-e2e/test.db'
os.environ['AUTO_SYNC_ON_STARTUP']='false'
os.environ['ENVIRONMENT']='development'
os.environ['CORS_ORIGINS']='["http://localhost:3001"]'
from app.main import app
from app.db.models import Base
from app.db.models.user import User
from app.db.session import engine,async_session_factory
from app.core.security import get_password_hash
from sqlalchemy import select
async def seed():
 async with engine.begin() as c:await c.run_sync(Base.metadata.create_all)
 async with async_session_factory() as s:
  for email,name in [('audit@example.test','Audit Test'),('audit2@example.test','Audit Two')]:
   if not (await s.execute(select(User).where(User.email==email))).scalar_one_or_none():
    s.add(User(email=email,hashed_password=get_password_hash('AuditOnly2026!'),full_name=name));await s.commit()
asyncio.run(seed())
from pathlib import Path
import json,time
from fastapi.responses import JSONResponse
@app.middleware('http')
async def audit_faults(request, call_next):
    start=time.perf_counter()
    config_path=Path('/tmp/stock-prediction-e2e/faults.json')
    config=json.loads(config_path.read_text()) if config_path.exists() else {}
    path=request.url.path
    symbol=request.query_params.get('symbol')
    if path.endswith('/predict/signal'):
        if config.get('signal_error'):
            return JSONResponse({'detail':'Injected isolated test failure'},status_code=503)
        await asyncio.sleep(config.get('delays',{}).get(symbol,0))
    response=await call_next(request)
    with open('/tmp/stock-prediction-e2e/requests.jsonl','a') as log:
        log.write(json.dumps({'path':path,'symbol':symbol,'model':request.query_params.get('model_type'),'method':request.method,'status':response.status_code,'seconds':time.perf_counter()-start})+'\n')
    return response
import uvicorn
uvicorn.run(app,host='127.0.0.1',port=8001)
