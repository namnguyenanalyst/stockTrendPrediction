import { afterEach,expect,it,vi } from 'vitest';
import { getPredictionSignal,getStockHistory } from './api';
afterEach(()=>{vi.useRealTimers();vi.unstubAllGlobals();});
it.each([getPredictionSignal,getStockHistory])('aborts a stalled prediction dependency after 30 seconds',async(call)=>{
 vi.useFakeTimers();
 vi.stubGlobal('fetch',vi.fn((_url,options:RequestInit)=>new Promise((_resolve,reject)=>{
  options.signal?.addEventListener('abort',()=>reject(new DOMException('Timed out','AbortError')));
 })));
 const result=call('VIC');const rejected=expect(result).rejects.toMatchObject({name:'AbortError'});
 await vi.advanceTimersByTimeAsync(30000);await rejected;
});
