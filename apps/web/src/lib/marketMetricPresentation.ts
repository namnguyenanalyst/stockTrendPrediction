/** Summary SMA deviations arrive in percentage units, unlike feature ratios. */
export function formatSmaDeviation(percent: number): string {
  return `${percent > 0 ? '+' : ''}${percent.toLocaleString('vi-VN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`;
}
export function describeSmaDeviation(percent: number, period: number): string {
  if (percent === 0) return `Bằng giá trung bình ${period} phiên`;
  return `${percent > 0 ? 'Cao' : 'Thấp'} hơn trung bình ${period} phiên`;
}
export function describeVolumeRatio(ratio: number): string {
  if (ratio === 1) return 'Bằng trung bình 20 phiên';
  return `${ratio > 1 ? 'Nhiều' : 'Ít'} hơn ${Math.abs((ratio - 1) * 100).toLocaleString('vi-VN', { maximumFractionDigits: 1 })}% so với TB 20 phiên`;
}
