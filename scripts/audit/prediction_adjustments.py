"""Read-only SSI reconciliation against the frozen evaluation snapshot.

Never rewrites prices, trains models, or logs credentials. Persists each symbol's
summary so interruption does not discard completed checks.
"""
import json
from pathlib import Path

import pandas as pd
from vn_stock.ssi_client import SSIFastConnectClient


def main():
    output = Path('reports/prediction-audit-2026-11-20/ssi-adjustment-reconciliation.json')
    panel = pd.read_parquet(output.parent / 'quality/panel_snapshot.parquet')
    client = SSIFastConnectClient()
    token = client._get_access_token()
    headers = {**client._headers, 'Authorization':'Bearer ' + token}
    report = {'endpoint':'/api/v2/Market/DailyStockPrice', 'results':[],
              'limitations':['Vendor adjusted close is a current reference, not original ingestion provenance.',
                             'Comparisons use 0.011 thousand VND tolerance; no prices are changed.',
                             'Frozen evaluation snapshot ends 2026-11-18; latest VIC/HPG checked separately.']}
    if output.exists():
        previous = json.loads(output.read_text())
        report['results'] = [r for r in previous['results'] if 'completed_windows' in r]
    for symbol, local in panel.groupby('Symbol'):
        item = next((r for r in report['results'] if r['symbol']==symbol), None)
        if item is None:
            item = dict(symbol=symbol,local_rows=len(local),completed_windows=[],examples=[],vendor_rows=0,
                        matched_dates=0,missing_dates=0,invalid_adjusted=0,local_matches_raw=0,
                        local_matches_adjusted=0,vendor_raw_adjusted_differ=0,unadjusted_local_on_adjusted_dates=0)
            report['results'].append(item)
        start = local.Date.min()
        end = local.Date.max()
        try:
            while start<=end:
                stop = min(start+pd.Timedelta(days=29),end)
                key = [str(start.date()),str(stop.date())]
                if key not in item['completed_windows']:
                    response = client._session.get(client.api_url+'api/v2/Market/DailyStockPrice',
                        params={'Symbol':symbol,'FromDate':start.strftime('%d/%m/%Y'),
                                'ToDate':stop.strftime('%d/%m/%Y'),'PageIndex':1,'PageSize':1000,'Market':'HOSE'},
                        headers=headers,timeout=30)
                    response.raise_for_status()
                    payload = response.json()
                    if str(payload.get('status')).lower() not in ('success','200'):
                        raise ValueError('Vendor rejected bounded request')
                    rows = payload.get('data') or []
                    vendor = pd.DataFrame(rows,columns=['TradingDate','ClosePrice','ClosePriceAdjusted'])
                    vendor['Date'] = pd.to_datetime(vendor.TradingDate,format='%d/%m/%Y')
                    vendor['raw_close'] = pd.to_numeric(vendor.ClosePrice,errors='coerce')/1000
                    vendor['adjusted_close'] = pd.to_numeric(vendor.ClosePriceAdjusted,errors='coerce')/1000
                    part = local[(local.Date>=start)&(local.Date<=stop)][['Date','Close']]
                    merged = part.merge(vendor[['Date','raw_close','adjusted_close']],on='Date',how='left',validate='one_to_one')
                    raw_match = (merged.Close-merged.raw_close).abs()<=.011
                    adjusted_match = (merged.Close-merged.adjusted_close).abs()<=.011
                    adjusted_valid = merged.adjusted_close.notna() & (merged.adjusted_close>0)
                    vendor_diff = adjusted_valid & ((merged.raw_close-merged.adjusted_close).abs()>.011)
                    counts = dict(vendor_rows=len(vendor),matched_dates=int(merged.raw_close.notna().sum()),
                        missing_dates=int(merged.raw_close.isna().sum()),invalid_adjusted=int((~adjusted_valid).sum()),
                        local_matches_raw=int(raw_match.sum()),local_matches_adjusted=int(adjusted_match.sum()),
                        vendor_raw_adjusted_differ=int(vendor_diff.sum()),
                        unadjusted_local_on_adjusted_dates=int((vendor_diff & raw_match & ~adjusted_match).sum()))
                    for field,value in counts.items(): item[field]+=value
                    item['examples'] = (item['examples']+merged[vendor_diff & ~adjusted_match].head(3)
                        .assign(Date=lambda d:d.Date.astype(str)).to_dict('records'))[:3]
                    item['completed_windows'].append(key)
                    item.pop('error_type',None)
                    output.write_text(json.dumps(report,indent=2,allow_nan=False,default=str))
                start = stop+pd.Timedelta(days=1)
        except Exception as error:
            item['error_type'] = type(error).__name__
            output.write_text(json.dumps(report,indent=2,allow_nan=False,default=str))
            raise RuntimeError(f'Reconciliation stopped at {symbol}; saved completed windows') from None
        output.write_text(json.dumps(report,indent=2,allow_nan=False,default=str))
        print(symbol, item.get('matched_dates',0),item.get('unadjusted_local_on_adjusted_dates',0),item.get('error_type','ok'),flush=True)


if __name__ == '__main__':
    main()
