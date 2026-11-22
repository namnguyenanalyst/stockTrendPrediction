// @vitest-environment jsdom
import React from 'react';
import { afterEach,expect,it,vi } from 'vitest';
import { cleanup,render,screen,waitFor } from '@testing-library/react';
vi.mock('@/lib/api',()=>({getPredictStatus:()=>Promise.resolve({last_atc_session_date:'2026-11-20',last_retrain_at:null})}));
vi.mock('@/components/charts/FireAntTrajectoryChart',()=>({FireAntTrajectoryChart:()=>null}));
vi.mock('@/components/market/FinancialDetailModal',()=>({FinancialDetailModal:()=>null}));
import { AIPredictionTab } from './AIPredictionTab';
import type { PredictionResponse } from '@/lib/types';
const prediction={symbol:'VIC',date:'2026-11-20',data_as_of_date:'2026-11-20',model_type:'lightgbm',predicted_label:2,class_name:'TĂNG',current_price:50,signal:'MUA',probabilities:{'GIẢM':.2,'ĐI NGANG':.3,'TĂNG':.5}} as PredictionResponse;
afterEach(()=>{cleanup();vi.restoreAllMocks();localStorage.clear();});
it.each(['getItem','setItem'] as const)('survives blocked or full localStorage at %s',async(method)=>{
 vi.spyOn(Storage.prototype,method).mockImplementation(()=>{throw new DOMException('Blocked storage','QuotaExceededError');});
 render(<AIPredictionTab selectedSymbol="VIC" modelType="lightgbm" prediction={prediction} bars={[]} loading={false} userId="isolated-account" onSelectSymbol={()=>{}} onChangeModelType={()=>{}}/>);
 await waitFor(()=>expect(screen.getByText('1 bản ghi',{exact:false})).toBeTruthy());
 expect(screen.getByRole('heading',{name:'MUA'})).toBeTruthy();
});
