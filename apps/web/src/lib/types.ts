/**
 * TypeScript Interfaces cho Hệ thống Web Dashboard Dự báo Chứng khoán VN.
 * Đồng bộ 1:1 với Pydantic Schemas của FastAPI Backend (apps/api/app/models/schemas.py).
 */

export interface StockSymbolInfo {
  symbol: string;
  name: string;
  exchange: string;
  is_core: boolean;
}

export interface StockBar {
  date: string; // YYYY-MM-DD
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface StockHistoryResponse {
  symbol: string;
  total_bars: number;
  bars: StockBar[];
}

export interface StockIndicatorBar {
  date: string;
  close: number;
  open_close_ratio: number;
  hl_ratio: number;
  sma_20_dev: number;
  sma_50_dev: number;
  sma_200_dev: number;
  cv_50: number;
  cv_200: number;
  rsi_14: number;
  return_1d: number;
  vol_ratio: number;
  vnindex_return_1d: number;
}

export interface StockIndicatorsResponse {
  symbol: string;
  total_bars: number;
  indicators: StockIndicatorBar[];
}

export interface StockSummaryResponse {
  symbol: string;
  latest_date: string;
  latest_close: number;
  prev_close: number;
  change_pct: number;
  volume: number;
  rsi_14: number;
  sma_20_dev: number;
  sma_50_dev: number;
}

export interface DayForecast {
  day_offset: number; // 1, 2, 3
  day_name: string; // "T+1", "T+2", "T+3"
  predicted_trend: "GIẢM" | "ĐI NGANG" | "TĂNG";
  signal: string; // "BÁN (SELL)" | "NẮM GIỮ (HOLD)" | "MUA (BUY)"
  confidence: number;
  probabilities: {
    GIẢM: number;
    "ĐI NGANG": number;
    TĂNG: number;
    [key: string]: number;
  };
  note?: string;
}

export interface PredictionResponse {
  symbol: string;
  date: string;
  data_as_of_date?: string;
  current_price: number;
  model_type: "lightgbm" | "lstm";
  predicted_label: number; // 0: Giảm, 1: Đi ngang, 2: Tăng
  class_name: "GIẢM" | "ĐI NGANG" | "TĂNG";
  signal: string; // "BÁN (SELL)" | "NẮM GIỮ (HOLD)" | "MUA (BUY)"
  probabilities: {
    GIẢM: number;
    "ĐI NGANG": number;
    TĂNG: number;
    [key: string]: number;
  };
  horizon: string;
  horizon_days?: number;
  is_live_synced?: boolean;
  trajectory?: DayForecast[];
  summary_guidance?: string;
}

export interface BatchPredictionResponse {
  model_type: string;
  total_symbols: number;
  predictions: PredictionResponse[];
}

export interface BacktestRequest {
  symbol: string;
  model_type: "lightgbm" | "lstm";
  initial_capital: number;
  slippage_rate?: number;
  fee_rate?: number;
  tax_rate?: number;
  lot_size?: number;
  settlement_delay?: number;
  execution_price?: "open" | "close";
  buy_prob_threshold?: number;
  sell_prob_threshold?: number;
}

export interface BacktestMetricsSchema {
  initial_capital: number;
  final_equity: number;
  total_return_pct: number;
  cagr_pct: number;
  buy_and_hold_return_pct: number;
  excess_return_pct: number;
  annualized_volatility_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown_pct: number;
  calmar_ratio: number;
  var_95_pct: number;
  cvar_95_pct: number;
  win_rate_pct: number;
  profit_factor: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  avg_trade_return_pct: number;
  avg_holding_days: number;
  total_fees_paid: number;
  total_taxes_paid: number;
  total_costs: number;
  cost_impact_pct: number;
}

export interface EquityCurvePoint {
  date: string;
  total_equity: number;
  benchmark_equity: number;
  drawdown_pct: number;
  daily_return: number;
}

export interface TradeLogItem {
  trade_id: number;
  order_type: "BUY" | "SELL";
  exec_date: string;
  exec_price: number;
  shares: number;
  fee: number;
  tax: number;
  net_cash_flow: number;
  realized_pnl: number | null;
  realized_return_pct: number | null;
  holding_days: number | null;
  reason: string;
}

export interface BacktestResponse {
  symbol: string;
  strategy_name: string;
  config: Record<string, unknown>;
  metrics: BacktestMetricsSchema;
  equity_curve: EquityCurvePoint[];
  trades: TradeLogItem[];
}

export interface BacktestSummaryItem {
  symbol: string;
  model: string;
  roi_pct: number;
  bh_roi_pct: number;
  excess_pct: number;
  sharpe: number;
  sortino: number;
  mdd_pct: number;
  win_rate_pct: number;
  profit_factor: number;
  trades: number;
  costs: number;
}

export interface BacktestSummaryResponse {
  model_type: string;
  summary: BacktestSummaryItem[];
}
