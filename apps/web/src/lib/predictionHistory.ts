import type { PredictionHistoryItem } from '@/components/tabs/AIPredictionTab';
export function predictionHistoryKey(userId: string) { return `vn_stock_prediction_history:v2:${userId}`; }
export function parsePredictionHistory(raw: string | null): PredictionHistoryItem[] {
 try {
  const value: unknown = JSON.parse(raw ?? '[]');
  if (!Array.isArray(value)) return [];
  return value.filter((r): r is PredictionHistoryItem => !!r && typeof r==='object'
   && ['id','timestamp','symbol','data_date','signal','horizon'].every(k=>typeof r[k]==='string')
   && ['lightgbm','lstm'].includes(r.model_type)
   && Number.isFinite(r.current_price) && r.current_price>0
   && [r.prob_up,r.prob_hold,r.prob_down,r.confidence].every(v=>Number.isFinite(v)&&v>=0&&v<=1)
   && Math.abs(r.prob_up+r.prob_hold+r.prob_down-1)<.01).slice(0,50);
 } catch { return []; }
}
