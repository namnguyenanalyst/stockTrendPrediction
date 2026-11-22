import { expect, it } from 'vitest';
import { formatSmaDeviation,describeSmaDeviation,describeVolumeRatio } from './marketMetricPresentation';
it('formats API percentage units without multiplying twice',()=>{
 expect(formatSmaDeviation(2.07)).toBe('+2,07%');
 expect(formatSmaDeviation(4.81)).toBe('+4,81%');
 expect(formatSmaDeviation(-2.07)).toBe('-2,07%');
 expect(describeSmaDeviation(-2,20)).toBe('Thấp hơn trung bình 20 phiên');
 expect(describeSmaDeviation(0,50)).toBe('Bằng giá trung bình 50 phiên');
});
it('explains volume ratios as differences from average',()=>{
 expect(describeVolumeRatio(.9)).toBe('Ít hơn 10% so với TB 20 phiên');
 expect(describeVolumeRatio(1.2)).toBe('Nhiều hơn 20% so với TB 20 phiên');
});
