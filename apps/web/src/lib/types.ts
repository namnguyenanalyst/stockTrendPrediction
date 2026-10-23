/**
 * TypeScript Interfaces cho Hệ thống Web Dashboard Dự báo Chứng khoán VN.
 * Đồng bộ 1:1 với Pydantic Schemas của FastAPI Backend (apps/api/app/models/schemas.py).
 */

export interface StockSymbolInfo {
  symbol: string;
  name: string;
  exchange: string;
  is_core: boolean;
  sector?: string;
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

export interface IndexOverview {
  name: string;
  symbol: string;
  value: number;
  change: number;
  change_pct: number;
  volume_str: string;
  value_str: string;
  advancing: number;
  ceiling: number;
  unchanged: number;
  declining: number;
  floor: number;
  sparkline: number[];
}

export interface StockBoardItem {
  symbol: string;
  name: string;
  exchange: string;
  sector: string;
  close: number;
  change: number;
  change_pct: number;
  volume: number;
  ceiling: number;
  floor: number;
  reference: number;
  sparkline: number[];
  buy_ratio: number;
  sell_ratio: number;
  rsi_14: number;
  sma_20_dev: number;
  ai_bias: string;
}

export interface MarketBreadth {
  ceiling: number;
  advancing: number;
  unchanged: number;
  declining: number;
  floor: number;
}

export interface MarketBoardResponse {
  updated_at: string;
  indices: IndexOverview[];
  breadth: MarketBreadth;
  stocks: StockBoardItem[];
  ai_market_insight: string;
  top_gainers: StockBoardItem[];
  top_losers: StockBoardItem[];
  top_search?: StockBoardItem[];
  top_volume?: StockBoardItem[];
}

export interface MarketSyncStatusResponse {
  target_date: string;
  session_type: "session_T" | "session_T_minus_1";
  session_name: string;
  status_label: string;
  is_market_closed: boolean;
  prediction_horizon_desc: string;
  current_time?: string;
  updated_symbols?: string[];
  total_symbols?: number;
}

export interface DayForecast {
  day_offset: number; // 1, 2, 3
  day_name: string; // "T+1", "T+2", "T+3"
  date?: string; // "YYYY-MM-DD"
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

export interface ModelMetricsSummary {
  accuracy?: number;
  macro_f1?: number;
  weighted_f1?: number;
  precision_macro?: number;
  recall_macro?: number;
  [key: string]: unknown;
}

export interface RetrainResponse {
  status: string;
  timestamp: string;
  horizon: string;
  horizon_days: number;
  threshold: number;
  val_buffer_days: number;
  latest_market_date: string;
  train_samples: number;
  val_samples: number;
  total_samples: number;
  lightgbm_metrics?: ModelMetricsSummary;
  lstm_metrics?: ModelMetricsSummary;
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
  market_session_label?: string;
  session_info?: MarketSyncStatusResponse;
  trajectory?: DayForecast[];
  summary_guidance?: string;
  training_info?: {
    latest_market_date?: string;
    horizon?: string;
    threshold?: number;
    train_samples?: number;
    val_samples?: number;
    lightgbm_metrics?: ModelMetricsSummary;
    lstm_metrics?: ModelMetricsSummary;
    timestamp?: string;
  };
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
  take_profit_pct?: number | null;
  stop_loss_pct?: number | null;
  trailing_stop_pct?: number | null;
  preset_id?: string | null;
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

export interface StrategyPresetItem {
  id: string;
  name: string;
  category: string;
  description: string;
  target_symbols: string[];
  default_symbol: string;
  conditions_summary: string;
  win_rate_pct: number;
  cumulative_pnl_pct: number;
  risk_reward_ratio: string;
  copy_count: number;
  take_profit_pct: number;
  stop_loss_pct: number;
  trailing_stop_pct: number;
  model_type: "lightgbm" | "lstm";
  timeframe: string;
}

export interface StrategyPresetsResponse {
  presets: StrategyPresetItem[];
}

export interface RecentSignalItem {
  signal_id: string;
  symbol: string;
  action: "BUY" | "SELL" | "HOLD";
  strategy_name: string;
  price: number;
  target_price: number;
  stop_price: number;
  confidence: number;
  timestamp: string;
  status: string;
}

export interface RecentSignalsResponse {
  signals: RecentSignalItem[];
}

export type BacktestScopeType = "stock" | "index" | "sector" | "portfolio";

export interface BacktestConditionFilter {
  market_condition?: "all" | "uptrend" | "sideways" | "downtrend";
  use_ma?: boolean;
  ma_type?: string;
  use_ema?: boolean;
  use_macd?: boolean;
  use_rsi?: boolean;
  rsi_threshold?: number;
  rsi_sell_threshold?: number;
  use_bb?: boolean;
  use_volume_spike?: boolean;
  use_price_increase?: boolean;
  max_pe?: number | null;
  max_pb?: number | null;
  min_roe?: number | null;
  foreign_net_buy?: boolean;
  foreign_net_sell?: boolean;
  prop_net_buy?: boolean;
  take_profit_pct?: number | null;
  stop_loss_pct?: number | null;
  trailing_stop_pct?: number | null;
}

export interface AdvancedBacktestRequest {
  scope_type: BacktestScopeType;
  symbol?: string;
  index_name?: string;
  sector_name?: string;
  portfolio_symbols?: string[];
  start_date: string;
  end_date: string;
  initial_capital: number;
  model_type: "lightgbm" | "lstm";
  slippage_rate?: number;
  buy_conditions?: BacktestConditionFilter;
  sell_conditions?: BacktestConditionFilter;
}

export interface SymbolBreakdownItem {
  symbol: string;
  name: string;
  sector: string;
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

export interface PortfolioBacktestResponse {
  scope_type: BacktestScopeType;
  scope_target: string;
  start_date: string;
  end_date: string;
  symbols_count: number;
  aggregate_metrics: BacktestMetricsSchema;
  portfolio_equity_curve: EquityCurvePoint[];
  symbols_breakdown: SymbolBreakdownItem[];
  individual_results?: Record<string, {
    metrics: BacktestMetricsSchema;
    equity_curve: EquityCurvePoint[];
    trades: TradeLogItem[];
  }>;
}

export interface SectorItem {
  sector: string;
  symbols: string[];
  count: number;
}

