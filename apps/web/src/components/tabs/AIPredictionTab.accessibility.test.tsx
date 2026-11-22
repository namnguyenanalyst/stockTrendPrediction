// @vitest-environment jsdom
import React from 'react';
import { afterEach,expect,it,vi } from 'vitest';
import { cleanup,fireEvent,render,screen,waitFor } from '@testing-library/react';
vi.mock('@/lib/api',()=>({getPredictStatus:()=>Promise.resolve({last_atc_session_date:'2026-11-20',last_retrain_at:null})}));
vi.mock('@/components/charts/FireAntTrajectoryChart',()=>({FireAntTrajectoryChart:()=>null}));
vi.mock('@/components/market/FinancialDetailModal',()=>({FinancialDetailModal:()=>null}));
import { AIPredictionTab } from './AIPredictionTab';
import type { PredictionResponse } from '@/lib/types';
afterEach(cleanup);
it('opens model information by keyboard-accessible trigger and traps/restores focus',async()=>{
 render(<AIPredictionTab selectedSymbol="VIC" modelType="lightgbm" prediction={null} loading={false} bars={[]} onSelectSymbol={()=>{}} onChangeModelType={()=>{}}/>);
 const trigger=screen.getByRole('button',{name:'Thông tin mô hình đang chọn'});trigger.focus();fireEvent.click(trigger);
 const dialog=screen.getByRole('dialog',{name:'LightGBM — Đặc trưng dạng bảng'});
 const buttons=dialog.querySelectorAll('button');
 await waitFor(()=>expect(document.activeElement).toBe(buttons[0]));
 fireEvent.keyDown(window,{key:'Tab',shiftKey:true});expect(document.activeElement).toBe(buttons[buttons.length-1]);
 fireEvent.keyDown(window,{key:'Tab'});expect(document.activeElement).toBe(buttons[0]);
 fireEvent.keyDown(window,{key:'Escape'});expect(screen.queryByRole('dialog')).toBeNull();expect(document.activeElement).toBe(trigger);
});

it('explains probabilities with the artifact threshold and exposes expansion state',()=>{
 const prediction={symbol:'VIC',model_type:'lightgbm',current_price:50,predicted_label:2,class_name:'TĂNG',
  probabilities:{'GIẢM':.2,'ĐI NGANG':.3,'TĂNG':.5},date:'2026-11-20',horizon:'T+3',
  training_info:{threshold:.02}} as PredictionResponse;
 render(<AIPredictionTab selectedSymbol="VIC" modelType="lightgbm" prediction={prediction} loading={false} bars={[]} onSelectSymbol={()=>{}} onChangeModelType={()=>{}}/>);
 const trigger=screen.getByRole('button',{name:'Giải thích xác suất và ngưỡng phân loại'});
 expect(trigger.getAttribute('aria-expanded')).toBe('false');
 fireEvent.click(trigger);
 expect(trigger.getAttribute('aria-expanded')).toBe('true');
 expect(screen.getByText(/Ngưỡng phân loại: ±2%/)).toBeTruthy();
 expect(screen.getByText(/không phải độ chính xác đã đo/)).toBeTruthy();
 expect(screen.queryByText(/1.5%/)).toBeNull();
});
