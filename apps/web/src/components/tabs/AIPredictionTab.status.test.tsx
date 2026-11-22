// @vitest-environment jsdom
import React from 'react';
import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
const api = vi.hoisted(() => ({ status: vi.fn() }));
vi.mock('@/lib/api', () => ({ getPredictStatus: api.status }));
vi.mock('@/components/charts/FireAntTrajectoryChart', () => ({ FireAntTrajectoryChart: () => null }));
vi.mock('@/components/market/FinancialDetailModal', () => ({ FinancialDetailModal: () => null }));
import { AIPredictionTab } from './AIPredictionTab';
afterEach(() => { cleanup(); vi.resetAllMocks(); });
it('does not present failed status as no retraining and recovers on retry', async () => {
  api.status.mockRejectedValueOnce(Object.assign(new Error('expired'), { status: 401 }))
    .mockResolvedValueOnce({ last_atc_session_date: '2026-11-20', last_retrain_at: '2026-11-22T01:00:00Z' });
  render(<AIPredictionTab selectedSymbol="VIC" modelType="lightgbm" prediction={null} loading={false} userId="audit" onSelectSymbol={() => {}} onChangeModelType={() => {}} />);
  expect((await screen.findByRole('alert')).textContent).toContain('Phiên đăng nhập đã hết hạn');
  expect(screen.queryByText(/Chưa có lần cập nhật nào/)).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Thử tải lại trạng thái' }));
  await waitFor(() => expect(screen.getByText('2026-11-20')).toBeTruthy());
  expect(screen.queryByRole('alert')).toBeNull();
  expect(api.status).toHaveBeenCalledTimes(2);
});
