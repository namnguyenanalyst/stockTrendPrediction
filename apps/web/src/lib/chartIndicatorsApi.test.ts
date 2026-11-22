import { afterEach, expect, it, vi } from 'vitest';
import { getChartIndicators } from './api';
afterEach(()=>vi.unstubAllGlobals());
it('calls the stock data router rather than the auth API prefix',async()=>{
 const payload={symbol:'BVH',total_bars:1,indicators:[]};
 const fetch=vi.fn().mockResolvedValue({ok:true,json:async()=>payload});vi.stubGlobal('fetch',fetch);
 expect(await getChartIndicators('BVH')).toEqual(payload);
 expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/stocks/chart-indicators?symbol=BVH&limit=1500',expect.any(Object));
});
