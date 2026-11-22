import { expect, it } from 'vitest';
import { matchesPrediction } from './predictionPresentation';
import { predictionLoadErrorMessage } from './predictionPresentation';
import type { PredictionResponse } from './types';
const prediction={symbol:'VIC',model_type:'lightgbm',current_price:50,predicted_label:2,class_name:'TĂNG',probabilities:{'GIẢM':.2,'ĐI NGANG':.3,'TĂNG':.5}} as PredictionResponse;
it('preserves a safe unavailable reason without displaying arbitrary internal errors',()=>{
 expect(predictionLoadErrorMessage({status:503,detail:'Dữ liệu giá cần đối chiếu.'})).toBe('Dữ liệu giá cần đối chiếu.');
 expect(predictionLoadErrorMessage({status:500,detail:'PRIVATE_MODEL_PATH'})).not.toContain('PRIVATE');
 expect(predictionLoadErrorMessage(new Error('PRIVATE_MODEL_PATH'))).not.toContain('PRIVATE');
});
it('rejects malformed responses without crashing UI',()=>{
 for(const data of [{...prediction,probabilities:null},{...prediction,model_type:null},{...prediction,current_price:Infinity},{...prediction,predicted_label:0}]) {
  expect(matchesPrediction(data as unknown as PredictionResponse,'VIC','lightgbm')).toBe(false);
 }
});
import { buildTrajectory,trajectoryProblem } from './predictionTrajectory';
import { parsePredictionHistory,predictionHistoryKey } from './predictionHistory';
const bar={date:'2026-11-20',open:50,high:51,low:49,close:50,volume:100};
const complete={...prediction,date:bar.date,data_as_of_date:bar.date,trajectory:['2026-11-23','2026-11-24','2026-11-25'].map((date,i)=>({date,day_offset:i+1,day_name:`T+${i+1}`,predicted_trend:'TĂNG',confidence:.5,probabilities:prediction.probabilities,signal:'MUA',note:''}))} as PredictionResponse;
it('creates precisely T and three future points with consistent anchor',()=>{
 const points=buildTrajectory(complete,'VIC','lightgbm',bar);expect(points).toHaveLength(4);expect(points[0].price).toBe(50);expect(points[3].date).toBe('2026-11-25');
 expect(buildTrajectory({...complete,data_as_of_date:bar.date+'T00:00:00'},'VIC','lightgbm',bar)).toHaveLength(4);
});
it('never fabricates missing or invalid future steps',()=>{
 for(const broken of [{...complete,trajectory:complete.trajectory!.slice(0,2)},{...complete,current_price:70},{...complete,date:'2026-11-19',data_as_of_date:'2026-11-19'},{...complete,trajectory:complete.trajectory!.map(s=>({...s,date:bar.date}))}]){
  expect(buildTrajectory(broken,'VIC','lightgbm',bar)).toEqual([]);expect(trajectoryProblem(broken,'VIC','lightgbm',bar)).toBeTruthy();
 }
});
it('scopes local history to accounts and rejects malformed saved entries',()=>{
 expect(predictionHistoryKey('a')).not.toBe(predictionHistoryKey('b'));
 for(const raw of ['{}','null','[{}]','invalid'])expect(parsePredictionHistory(raw)).toEqual([]);
});
