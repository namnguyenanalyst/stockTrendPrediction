// @vitest-environment jsdom
import React from "react";
import { afterEach, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { SavedStrategyItem } from "@/lib/types";

const mocks = vi.hoisted(() => ({ run: vi.fn(), save: vi.fn() }));
vi.mock("@/context/AuthContext", () => ({ useAuth: () => ({ user: null, isAuthenticated: false }) }));
vi.mock("@/lib/api", async () => ({
  ...await vi.importActual<typeof import("@/lib/api")>("@/lib/api"),
  runAdvancedBacktest: mocks.run, saveUserBacktest: mocks.save,
  getMarketSyncStatus: async () => null, getStockSymbols: async () => [],
  getStockSectors: async () => [], getStrategyPresets: async () => ({ presets: [] }),
  getRecentStrategySignals: async () => ({ signals: [] }),
}));
vi.mock("@/components/charts/EquityCurveChart", () => ({ EquityCurveChart: () => null }));
vi.mock("@/components/charts/DrawdownChart", () => ({ DrawdownChart: () => null }));
vi.mock("@/components/backtest/SavedStrategiesManager", () => ({
  SavedStrategiesManager: ({ strategies, onRunStrategy }: { strategies: SavedStrategyItem[], onRunStrategy: (s: SavedStrategyItem) => void }) =>
    <button onClick={() => onRunStrategy(strategies[0])}>Run fixture strategy</button>
}));
import { BacktestSimulatorTab } from "./BacktestSimulatorTab";
import { STRATEGY_STORAGE_KEY } from "@/lib/strategyStorage";
const strategy: SavedStrategyItem = {
  id: "fixture", name: "Saved fixture", status: "draft", scope_type: "stock", symbol: "FPT",
  start_date: "2024-01-02", end_date: "2024-03-01", initial_capital: 900000000,
  model_type: "lstm", slippage_rate: 0.01, use_advanced_settings: true,
  buy_conditions: { use_rsi: true, rsi_threshold: 30 }, sell_conditions: { stop_loss_pct: 0.1 },
  created_at: "2024-01-01", updated_at: "2024-01-01",
};
afterEach(() => { cleanup(); localStorage.clear(); vi.clearAllMocks(); });

it("runs a saved strategy with its own configuration rather than stale builder state", async () => {
  localStorage.setItem(STRATEGY_STORAGE_KEY, JSON.stringify([strategy]));
  mocks.run.mockImplementation(() => new Promise(() => { }));
  render(<BacktestSimulatorTab selectedSymbol="FPT" onSelectSymbol={() => { }} backtestResult={null} onRunBacktest={() => { }} loading={false} />);
  fireEvent.click(screen.getByText("Run fixture strategy"));
  await waitFor(() => expect(mocks.run).toHaveBeenCalledOnce());
  expect(mocks.run.mock.calls[0][0]).toMatchObject({
    scope_type: "stock", symbol: "FPT", start_date: strategy.start_date,
    initial_capital: strategy.initial_capital, model_type: "lstm",
    slippage_rate: 0.01, use_advanced_settings: true, buy_conditions: strategy.buy_conditions,
  });
});

it("ignores an old result after the symbol changes, including saved strategy metrics", async () => {
  localStorage.setItem(STRATEGY_STORAGE_KEY, JSON.stringify([strategy]));
  let resolve!: (value: unknown) => void;
  mocks.run.mockImplementation(() => new Promise(done => { resolve = done; }));
  const props = { selectedSymbol: "FPT", onSelectSymbol: () => { }, backtestResult: null, onRunBacktest: () => { }, loading: false };
  const view = render(<BacktestSimulatorTab {...props} />);
  fireEvent.click(screen.getByText("Run fixture strategy"));
  await waitFor(() => expect(mocks.run).toHaveBeenCalledOnce());
  view.rerender(<BacktestSimulatorTab {...props} selectedSymbol="HPG" />);
  await act(async () => resolve({ aggregate_metrics: { total_return_pct: 321 }, individual_results: {}, symbols_breakdown: [], portfolio_equity_curve: [] }));
  expect(screen.queryByText("+321.00%")).toBeNull();
  expect(JSON.parse(localStorage.getItem(STRATEGY_STORAGE_KEY)!)[0].last_metrics).toBeUndefined();
});

it("displays a persistent error state when backtest execution fails and never claims OOS for non-OOS results", async () => {
  localStorage.setItem(STRATEGY_STORAGE_KEY, JSON.stringify([strategy]));
  mocks.run.mockRejectedValueOnce(new Error("Thiếu dữ liệu cục bộ cho FPT"));
  render(<BacktestSimulatorTab selectedSymbol="FPT" onSelectSymbol={() => { }} backtestResult={null} onRunBacktest={() => { }} loading={false} />);
  fireEvent.click(screen.getByText("Run fixture strategy"));
  await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
  expect(screen.getAllByText(/Thiếu dữ liệu cục bộ cho FPT/).length).toBeGreaterThanOrEqual(1);
  expect(screen.queryByText(/Đo lường OOS/)).toBeNull();
});

it("handles 0 trades, 100% wins, 100% losses, and renders exec_price in VND without * 1000", async () => {
  localStorage.setItem(STRATEGY_STORAGE_KEY, JSON.stringify([strategy]));
  const baseCurve = [{ date: "2024-01-02", total_equity: 100000000, benchmark_equity: 100000000, drawdown_pct: 0, daily_return: 0 }];

  // 1. Zero trades
  mocks.run.mockResolvedValueOnce({
    scope_type: "stock", scope_target: "FPT", symbols_count: 1,
    start_date: "2024-01-02", end_date: "2024-03-01",
    aggregate_metrics: {
      initial_capital: 100000000, final_equity: 100000000,
      total_return_pct: 0, buy_and_hold_return_pct: 0, excess_return_pct: 0,
      sharpe_ratio: null, max_drawdown_pct: 0, win_rate_pct: null,
      total_trades: 0, winning_trades: 0, losing_trades: 0,
      avg_trade_return_pct: null, max_gain_pct: null, max_loss_pct: null,
      reward_risk_ratio: null, total_costs: 0,
    },
    portfolio_equity_curve: baseCurve, symbols_breakdown: [], individual_results: {},
  });
  const view = render(<BacktestSimulatorTab selectedSymbol="FPT" onSelectSymbol={() => { }} backtestResult={null} onRunBacktest={() => { }} loading={false} />);
  fireEvent.click(screen.getByText("Run fixture strategy"));
  await waitFor(() => expect(screen.getByText("Tổng: 0 lệnh đóng")).toBeTruthy());
  expect(screen.queryByText("---")).toBeNull();

  // 2. 100% winning trades (no losing trades) + check VND exec_price in trades tab
  mocks.run.mockResolvedValueOnce({
    scope_type: "stock", scope_target: "FPT", symbols_count: 1,
    start_date: "2024-01-02", end_date: "2024-03-01",
    aggregate_metrics: {
      initial_capital: 100000000, final_equity: 110000000,
      total_return_pct: 10, buy_and_hold_return_pct: 5, excess_return_pct: 5,
      sharpe_ratio: 1.5, max_drawdown_pct: 0, win_rate_pct: 100,
      total_trades: 1, winning_trades: 1, losing_trades: 0,
      avg_trade_return_pct: 10, max_gain_pct: 10, max_loss_pct: null,
      reward_risk_ratio: null, total_costs: 150000,
    },
    portfolio_equity_curve: baseCurve, symbols_breakdown: [],
    individual_results: {
      FPT: {
        metrics: {}, equity_curve: baseCurve,
        trades: [{
          trade_id: 1, order_type: "SELL", exec_date: "2024-02-01",
          exec_price: 27400, shares: 100, fee: 4110, tax: 2740,
          net_cash_flow: 2733150, realized_pnl: 250000, realized_return_pct: 10,
          holding_days: 5, reason: "TAKE_PROFIT",
        }],
      },
    },
  });
  fireEvent.click(screen.getByRole("button", { name: /CHẠY KIỂM THỬ/ }));
  await waitFor(() => expect(screen.getByText("Tổng: 1 lệnh đóng")).toBeTruthy());
  expect(screen.getByText("Không có lệnh lỗ để tính tỷ lệ")).toBeTruthy();

  // Switch to Sổ lệnh thực thi tab and verify 27.400 đ (not 27.400.000 đ)
  fireEvent.click(screen.getByText(/Sổ lệnh thực thi/));
  expect(screen.getByText("27.400 đ")).toBeTruthy();
  expect(screen.queryByText("27.400.000 đ")).toBeNull();

  // 3. 100% losing trades (no winning trades)
  mocks.run.mockResolvedValueOnce({
    scope_type: "stock", scope_target: "FPT", symbols_count: 1,
    start_date: "2024-01-02", end_date: "2024-03-01",
    aggregate_metrics: {
      initial_capital: 100000000, final_equity: 95000000,
      total_return_pct: -5, buy_and_hold_return_pct: 0, excess_return_pct: -5,
      sharpe_ratio: -1.0, max_drawdown_pct: 5, win_rate_pct: 0,
      total_trades: 1, winning_trades: 0, losing_trades: 1,
      avg_trade_return_pct: -5, max_gain_pct: null, max_loss_pct: -5,
      reward_risk_ratio: null, total_costs: 150000,
    },
    portfolio_equity_curve: baseCurve, symbols_breakdown: [],
    individual_results: {
      FPT: {
        metrics: {}, equity_curve: baseCurve,
        trades: [{
          trade_id: 2, order_type: "SELL", exec_date: "2024-02-05",
          exec_price: 25000, shares: 100, fee: 3750, tax: 2500,
          net_cash_flow: 2493750, realized_pnl: -125000, realized_return_pct: -5,
          holding_days: 3, reason: "STOP_LOSS",
        }],
      },
    },
  });
  fireEvent.click(screen.getByRole("button", { name: /CHẠY KIỂM THỬ/ }));
  await waitFor(() => expect(screen.getByText("Không có lệnh lãi để tính tỷ lệ")).toBeTruthy());
  view.unmount();
});
