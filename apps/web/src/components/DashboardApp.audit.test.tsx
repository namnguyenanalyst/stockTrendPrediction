// @vitest-environment jsdom
import React from 'react';
import { afterEach,beforeEach,expect,it,vi } from 'vitest';
import { act,cleanup,fireEvent,render,screen,waitFor } from '@testing-library/react';
const api=vi.hoisted(()=>({getBatchPrediction:vi.fn(),getMarketBoard:vi.fn(),getPredictionSignal:vi.fn(),getStockHistory:vi.fn(),getStockIndicators:vi.fn(),getStockSummary:vi.fn(),runBacktestSimulation:vi.fn()}));
vi.mock('@/lib/api',()=>api);
vi.mock('@/context/AuthContext',()=>({useAuth:()=>({user:{id:'audit',role:'trader'}})}));
vi.mock('@/components/Sidebar',()=>({Sidebar:()=>null}));
vi.mock('@/components/TopHeader',()=>({TopHeader:({setSelectedSymbol}:{setSelectedSymbol:(s:string)=>void})=><button onClick={()=>setSelectedSymbol('HPG')}>HPG</button>}));
vi.mock('@/components/tabs/MarketOverviewTab',()=>({MarketOverviewTab:()=>null}));
vi.mock('@/components/tabs/BacktestSimulatorTab',()=>({BacktestSimulatorTab:()=>null}));
vi.mock('@/components/tabs/SystemStatsTab',()=>({SystemStatsTab:()=>null}));
vi.mock('@/components/tabs/AIPredictionTab',()=>({AIPredictionTab:(p:{selectedSymbol:string;prediction:{symbol:string}|null;bars:{close:number}[];loading:boolean;error:string|null;onRetry:()=>void})=><div><output>{JSON.stringify({symbol:p.selectedSymbol,prediction:p.prediction?.symbol,bars:p.bars,loading:p.loading,error:p.error})}</output><button onClick={p.onRetry}>Retry</button></div>}));
import { DashboardApp } from './DashboardApp';
function deferred<T>() {let resolve!:(value:T)=>void;const promise=new Promise<T>(r=>{resolve=r;});return {promise,resolve};}
beforeEach(()=>{vi.clearAllMocks();Object.defineProperty(window,'matchMedia',{writable:true,value:()=>({matches:false,addEventListener:vi.fn(),removeEventListener:vi.fn()})});api.getBatchPrediction.mockResolvedValue({predictions:[]});api.getMarketBoard.mockResolvedValue({});api.getStockIndicators.mockResolvedValue({indicators:[]});api.getStockSummary.mockResolvedValue({});});
afterEach(cleanup);
it('ignores old responses and clears prior candles immediately when changing symbol',async()=>{
 const old=deferred<{symbol:string}>();api.getPredictionSignal.mockImplementation((symbol:string)=>symbol==='VIC'?old.promise:Promise.resolve({symbol}));api.getStockHistory.mockImplementation((symbol:string)=>Promise.resolve({bars:[{close:symbol==='VIC'?50:30}]}));
 render(<DashboardApp initialTab="prediction"/>);await waitFor(()=>expect(api.getPredictionSignal).toHaveBeenCalledWith('VIC','lightgbm'));
 fireEvent.click(screen.getByRole('button',{name:'HPG'}));expect(screen.getByRole('status').textContent).not.toContain('"close":50');
 await waitFor(()=>expect(screen.getByRole('status').textContent).toContain('"prediction":"HPG"'));
 await act(async()=>old.resolve({symbol:'VIC'}));expect(screen.getByRole('status').textContent).toContain('"prediction":"HPG"');
 expect(api.getStockHistory).toHaveBeenCalledTimes(2);
});
it('shows prediction failure without claiming success and retries',async()=>{
 api.getStockHistory.mockResolvedValue({bars:[]});api.getPredictionSignal.mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce({symbol:'VIC'});
 render(<DashboardApp initialTab="prediction"/>);await waitFor(()=>expect(screen.getByRole('status').textContent).toContain('Không thể tải dự báo'));
 fireEvent.click(screen.getByRole('button',{name:'Retry'}));await waitFor(()=>expect(screen.getByRole('status').textContent).toContain('"prediction":"VIC"'));expect(api.getPredictionSignal).toHaveBeenCalledTimes(2);
});
